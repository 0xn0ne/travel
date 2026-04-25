"""Tests for agent enrichment pipeline stage."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.pipeline.events import EventBus, PipelineEvent
from backend.pipeline.stages.stage_agent import PipelineSSEHooks, agent_enrich


class _SpyEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.events: list[PipelineEvent] = []

    async def emit(self, event: PipelineEvent):
        self.events.append(event)
        await super().emit(event)


def _make_intent(city="上海", interests=None, days=2):
    intent = MagicMock()
    intent.city = city
    intent.interests = interests or []
    intent.days = days
    return intent


def _make_agent_context():
    ctx = MagicMock()
    ctx.db_session = AsyncMock()
    ctx.amap_service = MagicMock()
    ctx.user_id = "test-user"
    ctx.settings = MagicMock()
    ctx.active_skills = []
    return ctx


@pytest.fixture
def spy_bus():
    return _SpyEventBus()


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.clone = MagicMock(return_value=agent)
    return agent


@pytest.mark.asyncio
async def test_emits_agent_thinking_at_start(spy_bus, mock_agent):
    with patch("backend.pipeline.stages.stage_agent.get_sdk_agent", return_value=mock_agent):
        with patch("backend.pipeline.stages.stage_agent.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "丰富文本"
            mock_runner.run = AsyncMock(return_value=mock_result)

            await agent_enrich(
                llm_client=MagicMock(),
                intent=_make_intent(),
                poi_candidates=[],
                user_input="我想去上海玩",
                event_bus=spy_bus,
                agent_context=_make_agent_context(),
            )

    thinking_events = [e for e in spy_bus.events if e.event_type == "agent_thinking"]
    assert len(thinking_events) == 1
    assert thinking_events[0].stage == "agent"
    assert thinking_events[0].status == "thinking"
    assert "挖掘" in thinking_events[0].message


@pytest.mark.asyncio
async def test_sse_hooks_emit_tool_executing(spy_bus):
    hooks = PipelineSSEHooks(spy_bus)
    tool = MagicMock()
    tool.name = "search_pois"

    await hooks.on_tool_start(MagicMock(), MagicMock(), tool)

    exec_events = [e for e in spy_bus.events if e.event_type == "tool_executing"]
    assert len(exec_events) == 1
    assert "搜索" in exec_events[0].message


@pytest.mark.asyncio
async def test_sse_hooks_emit_tool_completed(spy_bus):
    hooks = PipelineSSEHooks(spy_bus)
    tool = MagicMock()
    tool.name = "search_pois"

    await hooks.on_tool_end(MagicMock(), MagicMock(), tool, "result")

    completed_events = [e for e in spy_bus.events if e.event_type == "tool_completed"]
    assert len(completed_events) == 1
    assert "地点信息" in completed_events[0].message


@pytest.mark.asyncio
async def test_returns_enrichment_text(spy_bus, mock_agent):
    with patch("backend.pipeline.stages.stage_agent.get_sdk_agent", return_value=mock_agent):
        with patch("backend.pipeline.stages.stage_agent.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "上海今天天气晴朗，适合户外活动"
            mock_runner.run = AsyncMock(return_value=mock_result)

            result = await agent_enrich(
                llm_client=MagicMock(),
                intent=_make_intent(),
                poi_candidates=[],
                user_input="我想去上海",
                event_bus=spy_bus,
                agent_context=_make_agent_context(),
            )

    assert result == "上海今天天气晴朗，适合户外活动"


@pytest.mark.asyncio
async def test_graceful_degradation_on_failure(spy_bus, mock_agent):
    with patch("backend.pipeline.stages.stage_agent.get_sdk_agent", return_value=mock_agent):
        with patch("backend.pipeline.stages.stage_agent.Runner") as mock_runner:
            mock_runner.run = AsyncMock(side_effect=RuntimeError("SDK broke"))

            result = await agent_enrich(
                llm_client=MagicMock(),
                intent=_make_intent(),
                poi_candidates=[],
                user_input="test",
                event_bus=spy_bus,
                agent_context=_make_agent_context(),
            )

    assert result == ""
    error_events = [e for e in spy_bus.events if e.event_type == "agent_error"]
    assert len(error_events) == 1
    assert "基础方案" in error_events[0].message


@pytest.mark.asyncio
async def test_uses_cached_agent_with_overridden_instructions(spy_bus, mock_agent):
    with patch("backend.pipeline.stages.stage_agent.get_sdk_agent", return_value=mock_agent) as mock_get:
        with patch("backend.pipeline.stages.stage_agent.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "text"
            mock_runner.run = AsyncMock(return_value=mock_result)

            await agent_enrich(
                llm_client=MagicMock(),
                intent=_make_intent(),
                poi_candidates=[],
                user_input="上海两天",
                event_bus=spy_bus,
                agent_context=_make_agent_context(),
            )

    mock_get.assert_called_once()
    mock_agent.clone.assert_called_once()
    clone_kwargs = mock_agent.clone.call_args[1]
    assert "上海" in clone_kwargs["instructions"]


@pytest.mark.asyncio
async def test_does_not_call_emit_done(spy_bus, mock_agent):
    with patch("backend.pipeline.stages.stage_agent.get_sdk_agent", return_value=mock_agent):
        with patch("backend.pipeline.stages.stage_agent.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "text"
            mock_runner.run = AsyncMock(return_value=mock_result)

            await agent_enrich(
                llm_client=MagicMock(),
                intent=_make_intent(),
                poi_candidates=[],
                user_input="test",
                event_bus=spy_bus,
                agent_context=_make_agent_context(),
            )

    assert not hasattr(spy_bus, "emit_done_called")
    assert not any(e.event_type == "done" for e in spy_bus.events)
