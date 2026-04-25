"""Stage Agent: Agent enrichment stage for the pipeline.

Per PIPE-01, PIPE-02, AGENT-03:
- Runs SDK Agent with tools to gather real-time enrichment data
- Streams human-readable SSE events (Chinese) via EventBus
- Returns enrichment text for stage3 prompt injection
- Graceful degradation on failure
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from agents import Agent, Runner
from agents.lifecycle import RunHooksBase
from agents.tool import FunctionTool

from backend.api.dependencies import build_agent_instructions, get_sdk_agent
from backend.pipeline.events import EventBus, PipelineEvent

if TYPE_CHECKING:
    from backend.agent.context import AgentContext
    from backend.llm.client import LLMClient
    from backend.models.pydantic import IntentOutput, POICandidate

logger = logging.getLogger(__name__)

_TOOL_DISPLAY_NAMES: dict[str, tuple[str, str]] = {
    "search_pois": ("正在搜索相关地点...", "已获取地点信息"),
    "query_weather": ("正在查询天气信息...", "已获取天气信息"),
    "get_user_preferences": ("正在了解你的偏好...", "已了解你的偏好"),
    "get_itinerary_context": ("正在回顾历史行程...", "已回顾历史行程"),
    "web_search": ("正在搜索网络信息...", "已获取网络信息"),
    "web_fetch": ("正在获取网页内容...", "已获取网页内容"),
    "read_memories": ("正在回忆之前的旅行偏好...", "已回忆旅行偏好"),
    "write_memory": ("", ""),
    "list_files": ("", ""),
    "read_file": ("", ""),
    "write_file": ("", ""),
    "execute_command": ("", ""),
}


class PipelineSSEHooks(RunHooksBase):
    """SDK lifecycle hooks that emit SSE events via EventBus.

    Per D-18~D-20: hooks capture tool start/end events and emit
    human-readable Chinese messages. Tool mechanics (JSON schema,
    function names, raw args) are NEVER exposed to the user.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def on_tool_start(self, context: Any, agent: Any, tool: Any) -> None:
        tool_name = getattr(tool, "name", "")
        display = _TOOL_DISPLAY_NAMES.get(tool_name)
        if display and display[0]:
            await self._event_bus.emit(
                PipelineEvent(
                    stage="agent",
                    status="executing",
                    event_type="tool_executing",
                    message=display[0],
                )
            )
        else:
            await self._event_bus.emit(
                PipelineEvent(
                    stage="agent",
                    status="executing",
                    event_type="tool_executing",
                    message="正在获取更多信息...",
                )
            )

    async def on_tool_end(self, context: Any, agent: Any, tool: Any, result: str) -> None:
        tool_name = getattr(tool, "name", "")
        display = _TOOL_DISPLAY_NAMES.get(tool_name)
        if display and display[1]:
            await self._event_bus.emit(
                PipelineEvent(
                    stage="agent",
                    status="completed",
                    event_type="tool_completed",
                    message=display[1],
                )
            )
        else:
            await self._event_bus.emit(
                PipelineEvent(
                    stage="agent",
                    status="completed",
                    event_type="tool_completed",
                    message="信息获取完成",
                )
            )


async def agent_enrich(
    *,
    llm_client: "LLMClient",
    intent: "IntentOutput",
    poi_candidates: list["POICandidate"],
    user_input: str,
    event_bus: EventBus,
    agent_context: "AgentContext",
) -> str:
    """Run SDK Agent to gather enrichment text for itinerary generation.

    Per D-01: New pipeline stage between filter and generate.
    Per D-11: Returns enrichment text (Chinese), NOT modified POI list.
    Per D-14: Returns empty string on failure — pipeline continues.
    """
    await event_bus.emit(
        PipelineEvent(
            stage="agent",
            status="thinking",
            event_type="agent_thinking",
            message="正在为你挖掘更多有趣的去处...",
        )
    )

    interests = intent.interests if hasattr(intent, "interests") else []
    instructions = build_agent_instructions(user_input, interests)

    city = intent.city if hasattr(intent, "city") else ""
    poi_count = len(poi_candidates) if poi_candidates else 0
    instructions += (
        f"\n\n## 当前任务\n"
        f"城市：{city}\n"
        f"已筛选出 {poi_count} 个候选地点\n"
        f"用户需求：{user_input}\n"
        f"请利用工具收集实时信息（天气、用户偏好、网络评价等），"
        f"为行程生成提供补充建议。不要修改候选地点列表，只提供额外的信息和建议。"
    )

    base_agent = get_sdk_agent()
    agent = base_agent.clone(instructions=instructions)

    hooks = PipelineSSEHooks(event_bus)

    try:
        result = await asyncio.wait_for(
            Runner.run(
                starting_agent=agent,
                input=user_input,
                context=agent_context,
                max_turns=8,
                hooks=hooks,
            ),
            timeout=30.0,
        )
        enrichment = result.final_output or ""
        return enrichment
    except asyncio.TimeoutError:
        logger.warning("agent_enrich timed out after 30s")
        await event_bus.emit(
            PipelineEvent(
                stage="agent",
                status="error",
                event_type="agent_error",
                message="智能推荐暂时不可用，将使用基础方案",
            )
        )
        return ""
    except Exception as e:
        logger.warning("agent_enrich failed: %s", e)
        await event_bus.emit(
            PipelineEvent(
                stage="agent",
                status="error",
                event_type="agent_error",
                message="智能推荐暂时不可用，将使用基础方案",
            )
        )
        return ""
