"""Agent memory read/write tools (MEM-01, MEM-02).

Per D-04 through D-11:
- write_memory: validates category, upserts by user_id+key, rejects anonymous
- read_memories: profile-scored retrieval using taste_tags overlap, recency fallback
"""

import json
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from sqlalchemy import select

from backend.agent.context import AgentContext
from backend.models.database import ALLOWED_CATEGORIES, AgentMemory, User


@function_tool
async def write_memory(
    ctx: RunContextWrapper[AgentContext],
    key: str,
    value: str,
    category: str,
) -> str:
    """写入一条用户记忆。用于记住用户的偏好、限制、反馈或行程上下文。

    Args:
        key: 记忆键名，如"dietary_preference"、"budget_limit"
        value: JSON字符串，必须包含note字段。如'{"note":"不喜欢辣","tags":["清淡"]}'
        category: 分类，必须是 preference/constraint/feedback/trip_context 之一
    """
    if category not in ALLOWED_CATEGORIES:
        return f"写入失败：无效分类 '{category}'。支持的分类：{', '.join(sorted(ALLOWED_CATEGORIES))}"

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return "写入失败：value 必须是合法的 JSON 字符串"

    if not isinstance(parsed, dict) or "note" not in parsed:
        return "写入失败：value 必须是 JSON 对象且包含 'note' 字段"

    user_id = ctx.context.user_id
    if not user_id:
        return "无法写入记忆：请先登录"

    db_session = ctx.context.db_session
    now = datetime.now(timezone.utc)

    result = await db_session.execute(
        select(AgentMemory).where(
            AgentMemory.user_id == user_id,
            AgentMemory.key == key,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = json.dumps(parsed, ensure_ascii=False)
        existing.category = category
        existing.access_count += 1
        existing.updated_at = now
        existing.last_accessed_at = now
        await db_session.flush()
        return f"已更新：{key}"
    else:
        memory = AgentMemory(
            user_id=user_id,
            key=key,
            value=json.dumps(parsed, ensure_ascii=False),
            category=category,
            access_count=1,
            created_at=now,
            updated_at=now,
            last_accessed_at=now,
        )
        db_session.add(memory)
        await db_session.flush()
        return f"已记住：{key}"


@function_tool
async def read_memories(
    ctx: RunContextWrapper[AgentContext],
    category: str | None = None,
    limit: int = 20,
) -> str:
    """读取当前用户的记忆。按用户画像相关度排序返回。

    Args:
        category: 可选，筛选特定分类的记忆
        limit: 返回条数上限，默认20
    """
    user_id = ctx.context.user_id
    if not user_id:
        return "[]"

    db_session = ctx.context.db_session

    stmt = select(AgentMemory).where(AgentMemory.user_id == user_id)
    if category:
        if category not in ALLOWED_CATEGORIES:
            return f"读取失败：无效分类 '{category}'。支持的分类：{', '.join(sorted(ALLOWED_CATEGORIES))}"
        stmt = stmt.where(AgentMemory.category == category)

    result = await db_session.execute(stmt)
    memories = result.scalars().all()

    if not memories:
        return "[]"

    user_result = await db_session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    taste_tags: list[str] = []
    if user:
        try:
            taste_tags = json.loads(user.taste_tags_default) if user.taste_tags_default else []
        except (json.JSONDecodeError, TypeError):
            taste_tags = []

    def _score(mem: AgentMemory) -> tuple[int, datetime]:
        if not taste_tags:
            return (0, mem.updated_at or datetime.min.replace(tzinfo=timezone.utc))
        try:
            val = json.loads(mem.value)
            mem_tags = val.get("tags", [])
            tag_score = len(set(taste_tags) & set(mem_tags))
        except (json.JSONDecodeError, TypeError, AttributeError):
            tag_score = 0
        return (tag_score, mem.updated_at or datetime.min.replace(tzinfo=timezone.utc))

    memories = sorted(memories, key=_score, reverse=True)

    memories = memories[:limit]

    items = []
    for m in memories:
        items.append({
            "id": m.id,
            "key": m.key,
            "value": json.loads(m.value) if m.value else {},
            "category": m.category,
            "access_count": m.access_count,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        })

    return json.dumps(items, ensure_ascii=False)
