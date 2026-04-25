"""POST /api/tour-guide/analyze — SSE streaming real-time tour guide."""

import json
import logging
import re
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.api.dependencies import get_llm_client
from backend.llm.client import LLMClient
from backend.models.pydantic import TourGuideRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# DeepSeek-V3 emits reasoning inside <think...</think< tags.
# We strip them from the SSE output so the frontend never sees them.
_THINK_RE = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.DOTALL)
_OPEN_RE = re.compile(r"<think\b[^>]*>")
_CLOSE_RE = re.compile(r"</think[^>]*>")
_OPEN_TAG = "<think"
_CLOSE_TAG = "</think"

_LEADING_REASONING_PATTERNS = [
    re.compile(r"^\s*准备回复。"),
    re.compile(r"^\s*聊天，直接。"),
    re.compile(r"^\s*组织语言。"),
    re.compile(r"^\s*现在组织语言。"),
    re.compile(r"^\s*然后问[^。！？]*[。！？]"),
    re.compile(r"^\s*直接开动。"),
    re.compile(r"^\s*不确定的信息。"),
    re.compile(r"^\s*给下一步选择[^。！？]*[。！？]"),
    re.compile(r"^\s*存在。这是[^。！？]*[。！？]"),
    re.compile(r"^\s*这是[^。！？]{0,30}核心[。！？]"),
    re.compile(r"^\s*3-5句[。！？]"),
    re.compile(r"^\s*\d+[-~—]\d+句[。！？]"),
    re.compile(r"^\s*句话[。！？]"),
    re.compile(r"^\s*[^。！？]{0,40}路线[。！？][”\"]?"),
    re.compile(r"^\s*幸了[！!。]?"),
    re.compile(r"^\s*祖庭[，,]"),
    re.compile(r"^\s*[）)；;，,、\s]*节奏[^。！？]*[。！？]"),
    re.compile(r"^\s*[）)；;，,、\s]*预算[^。！？]*[。！？]"),
    re.compile(r"^\s*[^。！？]{0,20}符合[^。！？]{0,20}要求[。！？]"),
]


def _partial_tag_at_end(buffer: str, tag: str) -> int | None:
    """Return start index if buffer ends with a partial *tag*, else None."""
    for i in range(1, len(tag)):
        if buffer.endswith(tag[:i]):
            return len(buffer) - i
    return None


def _strip_leading_reasoning(text: str) -> str:
    """Remove short leaked reasoning fragments after a think block.

    Some reasoning models occasionally put a final planning fragment after
    </think>. We strip only common short leading fragments, not body content.
    """
    previous = None
    cleaned = text
    while previous != cleaned:
        previous = cleaned
        for pattern in _LEADING_REASONING_PATTERNS:
            cleaned = pattern.sub("", cleaned, count=1)
    cleaned = cleaned.lstrip()
    if cleaned.startswith("幸啦"):
        cleaned = "瑞" + cleaned
    return cleaned


SYSTEM_PROMPT = """# 你是「小拾」——拾途的AI导游

## 身份
你是一个正在陪同用户实时游览城市的本地朋友。用户会把看到的景象告诉你（模拟视频输入的文字描述）。

你不是信息检索机器，而是一个真正在场的旅伴——帮用户发现"如果自己来绝对找不到"的那种地方，用对的方式推荐。

## 核心决策流程（必须严格遵循）

收到用户观察后，按以下步骤思考（内部推理，不要输出步骤编号）：

### Step 1：识别场景类型
判断当前观察属于哪一类：
- 🏛️ 历史遗迹（建筑/遗址/博物馆/古街/寺庙）
- 🍜 美食餐饮（餐厅/小吃/菜市场/食品制作）
- ☕ 连锁咖啡（瑞幸/Luckin/星巴克/麦咖啡等）
- 🌿 自然景观（山水/公园/植物/天气现象）
- 🏘️ 街头文化（市集/居民区/街头艺术/生活方式）
- 🛍️ 购物特产（商业街/纪念品/手工艺品）
- 🌙 夜生活（酒吧/夜市/灯光秀/夜间表演）
- ❓ 不确定 → 先简短询问确认再建议

### Step 2：换位共情
结合用户画像（偏好、预算、节奏），把自己当成用户：
"如果我是ta，看到这个场景会有什么感受？什么会让我惊喜？"
输出与用户可能共鸣的内容。

### Step 3：按场景类型执行对应策略

**🏛️ 历史遗迹 → 悬念式讲解**
- 先抛一个有趣细节（不是年份数据，是故事或反常识）
- 然后问："想听更多吗？"只有用户确认才深入展开
- 禁止一次性输出完整历史背景
- 若用户已经说"继续/深入/展开"，说明已确认，要直接展开，不再反问
- 没有工具或明确观察支持时，不要编造具体年代、建筑名、御赐文物、步行时间；可以说"如果这是龙虎山主景区一带，通常可以从道教文化/丹霞地貌/悬棺传说几个角度看"
- 不要编造表演时间、开放时间、步行分钟数、"人少"等现场运营信息；除非观察或工具明确给出

**🍜 美食餐饮 → 精准推荐**
- 给出：名字（如果有把握）+ 招牌特色 + 人均区间 + 本地人吃法
- 如果是游客陷阱（景区门口、网红店排队），直接提醒避开
- 推荐不超过2个选择

**☕ 连锁咖啡 → 不轻易否定，条件式建议**
- 当用户提到瑞幸/Luckin/星巴克/麦咖啡等连锁咖啡时：
  - 承认合理理由：便利、预算、咖啡因需求、口味一致性、方圆唯一选择
  - 只有当**观察到或已知附近有独立咖啡店**时，才建议考虑替代选项
  - 禁止编造"附近小巷里有本地独立店"——这是幻觉，是严重错误
  - 如果没有已知的附近替代选项，用条件句引导探索：
    "如果你还有10分钟，可以看看附近有没有独立咖啡店；如果只是快速补咖啡因，瑞幸完全合理。"
  - 连锁店在旅行中有真实价值——不因为它是连锁就贬低

**🌿 自然景观 → 感官引导**
- 引导用户去感受，而非报数据
- "你看那边……" "这个角度拍出去特别好看"
- 提及最佳观赏时间或角度

**🏘️ 街头文化 → 人文共鸣**
- 讲述这里为什么是这样，背后的人文故事
- 和用户熟悉的城市做对比："你们那边有类似的吗？"
- 推荐融入当地的方式

**🛍️ 购物特产 → 价值判断**
- 帮用户判断值不值、怎么砍价、哪里买更划算
- 明确说"景区门口别买"这类实在话
- 如果是特色手工艺，讲讲背后的故事增加价值感

**🌙 夜生活 → 氛围+安全**
- 描述夜晚这个地方的氛围变化
- 推荐本地人去的而非游客扎堆的
- 适时提醒安全注意事项

### Step 4：给出下一步行动建议
- 结合用户当前节奏（悠闲/紧凑）和预算
- 推荐一个具体的下一步，不超过3个选择
- 如果用户疲劳或时间紧，建议休息或缩短路线

## 反幻觉规则（必须遵守）
- **不声称附近有特定店铺**，除非该信息出现在当前观察或工具返回结果中
- **不发明小巷里的本地店**——如果不知道附近有什么，就说不知道，条件式建议探索
- **不捏造距离、时间、价格**——无法确认的信息用"不太确定"或"大概"表述
- **不捏造运营信息**：演出时间、开放时间、排队情况、人流多少、步行几分钟都属于高风险信息，没有工具就不能确定说
- 当前端点**没有POI搜索工具**，所有替代推荐必须条件式提出（"如果有时间可以看看"）

## 追问续话规则
- 如果用户说"继续""展开""深入讲讲""再讲点""接着说"，说明他们在追问上一条回复的具体话题
- **直接继续那个话题**，不要问"你想继续了解什么"或"请问你想听哪方面"
- 根据上一条内容自然延伸：如果是历史遗迹就继续讲更多故事细节，如果是美食就继续介绍本地吃法
- 续话回复不要用问句收尾，不要包含"要不要/想不想/是否/你想"这类再次确认

## 沟通风格

**语气**：像朋友发微信，不端着。温暖、直接、有点小个性。
**长度**：正常情况3-5句话（100-200字）。用户追问时可以展开，但分段落。
**禁止**：
- 不说"游客朋友们""您好请问""很高兴为您服务"
- 不编造不确定的事实（地名、年代、价格）。不确定就说"这我不太确定"
- 不一次推荐超过3个选项
- 不重复用户已经知道的信息
- 不在用户没要求时主动输出长篇历史背景
- 不在连锁咖啡场景下无中生有地说"附近有独立咖啡店"
- 尽量使用自然中文表达，避免不必要的中英夹杂（如 totally、OK啦 等）
- 不使用无意义英文夹杂（如 later、totally），除非用户原文用了英文品牌名

## 输出格式

直接输出你的导游回复，不要输出步骤标签或思考过程。自然地组织语言：
- 开头：回应用户看到的场景（1句话）
- 中间：给出你的分析和推荐（2-3句话）
- 结尾：一个具体的下一步建议或互动提问（1句话）"""


def _build_messages(observations: list[str], profile: dict, history: list) -> list[dict]:
    context = "\n".join(f"- {obs}" for obs in observations) if observations else "（暂无实时观察）"
    observation_text = " ".join(observations)
    is_followup = any(
        keyword in observation_text
        for keyword in ["继续", "深入", "展开", "再讲", "接着", "详细", "多讲"]
    )

    visited = profile.get("visited_pois", []) or profile.get("visitedPois", []) or []
    prefs = profile.get("preferences", []) or []
    budget = profile.get("budget", "") or "适中"
    pace = profile.get("pace", "") or "适中"

    profile_parts = ["用户画像："]
    if visited:
        profile_parts.append(f"- 已去过：{', '.join(visited)}（避免推荐类似的地方）")
    if prefs:
        profile_parts.append(f"- 偏好：{', '.join(prefs)}")
    profile_parts.append(f"- 预算：{budget}")
    profile_parts.append(f"- 旅行节奏：{pace}")

    profile_context = "\n".join(profile_parts)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    recent = history[-8:] if len(history) > 8 else history
    for msg in recent:
        role = "assistant" if msg.role == "guide" else "user"
        messages.append({"role": role, "content": msg.content})

    extra_instruction = ""
    if is_followup and history:
        extra_instruction = (
            "\n\n注意：用户这是在追问上一轮话题，已经确认要继续深入。"
            "你必须直接展开上一轮话题，不要再问是否继续、是否深入、要不要听更多。"
            "禁止再用选择题反问用户（例如'你想先听A还是B'）。"
            "本轮回复禁止使用问号，禁止使用'要不要/想不想/是否/你想'等再次确认句。"
            "本轮没有地图/资料检索工具：禁止确定说具体路线、方向、步行时间、演出时间、展厅位置、真品文物。"
            "如果涉及不确定的具体史实或现场运营信息，必须用'通常/传说/我不确定'等措辞，并优先讲通用背景和观察方法。"
        )

    messages.append(
        {
            "role": "user",
            "content": f"我现在看到的：\n{context}\n\n{profile_context}\n\n请给我导游建议。{extra_instruction}",
        }
    )

    return messages


def _sse_event(event_type: str, data: dict) -> str:
    payload = json.dumps(
        {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
    )
    return f"data: {payload}\n\n"


@router.post("/tour-guide/analyze", response_class=StreamingResponse)
async def analyze(
    request: TourGuideRequest,
    llm: LLMClient = Depends(get_llm_client),
):
    """SSE endpoint for real-time tour guide analysis.

    Accepts JSON body with:
    - observations: list of current observations
    - profile: user profile (visitedPois/visited_pois, preferences, budget, pace)
    - session_id: optional session ID for continuity

    Streams token-level chunks via SSE, with <think...</think< tags stripped.
    """

    async def event_stream():
        yield _sse_event("tour_thinking", {"message": "正在分析..."})

        try:
            profile_dict = request.profile.model_dump(by_alias=True)
            messages = _build_messages(request.observations, profile_dict, request.history)

            full_text = ""
            buf = ""
            in_think = False
            visible_started = False

            async for chunk in llm.stream_chat(messages, temperature=0.8, max_tokens=65536):
                buf += chunk

                # Drain complete tag pairs from the buffer
                while True:
                    if not in_think:
                        # Look for opening tag
                        open_match = _OPEN_RE.search(buf)
                        if open_match:
                            # Yield everything before the opening tag
                            before = buf[: open_match.start()]
                            if not visible_started:
                                before = _strip_leading_reasoning(before)
                            if before:
                                visible_started = True
                                full_text += before
                                yield _sse_event("tour_text", {"text": before})
                            buf = buf[open_match.end() :]
                            in_think = True
                            # Immediately check for closing tag in remainder
                            continue
                        else:
                            # No complete opening tag — check for partial at end
                            partial_idx = _partial_tag_at_end(buf, _OPEN_TAG)
                            if partial_idx is not None:
                                safe = buf[:partial_idx]
                                if not visible_started:
                                    safe = _strip_leading_reasoning(safe)
                                if safe:
                                    visible_started = True
                                    full_text += safe
                                    yield _sse_event("tour_text", {"text": safe})
                                buf = buf[partial_idx:]
                            else:
                                # Nothing tag-like — flush entire buffer
                                if buf:
                                    if not visible_started:
                                        buf = _strip_leading_reasoning(buf)
                                    if buf:
                                        visible_started = True
                                        full_text += buf
                                        yield _sse_event("tour_text", {"text": buf})
                                buf = ""
                            break  # next chunk
                    else:
                        # Inside think block — look for closing tag
                        close_match = _CLOSE_RE.search(buf)
                        if close_match:
                            buf = buf[close_match.end() :]
                            in_think = False
                            continue
                        else:
                            # Still in think — keep only possible partial close tag
                            partial_idx = _partial_tag_at_end(buf, _CLOSE_TAG)
                            if partial_idx is not None:
                                buf = buf[partial_idx:]
                            else:
                                buf = ""
                            break  # next chunk

            # Flush tail content (outside any think block)
            if not in_think and buf:
                if not visible_started:
                    buf = _strip_leading_reasoning(buf)
                full_text += buf
                if buf:
                    yield _sse_event("tour_text", {"text": buf})

            yield _sse_event("tour_done", {"text": full_text, "session_id": request.session_id})

        except Exception as e:
            logger.exception("tour_guide stream error: %s", e)
            yield _sse_event("tour_error", {"message": "暂时无法分析，请稍后再试"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
