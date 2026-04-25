"""Integration tests for pipeline with agent enrichment stage."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agent.context import AgentContext
from backend.pipeline.coordinator import PipelineCoordinator
from backend.pipeline.events import EventBus, PipelineEvent


class _SpyEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.events: list[PipelineEvent] = []

    async def emit(self, event: PipelineEvent):
        self.events.append(event)
        await super().emit(event)


def _make_intent(city="上海", days=2, interests=None):
    from backend.models.pydantic import IntentOutput
    return IntentOutput(
        city=city,
        days=days,
        budget_level="适中",
        pace="适中",
        rating_level="较好",
        interests=interests or ["美食"],
    )


def _make_agent_context():
    ctx = MagicMock(spec=AgentContext)
    ctx.db_session = AsyncMock()
    ctx.amap_service = MagicMock()
    ctx.user_id = "test-user"
    ctx.settings = MagicMock()
    ctx.active_skills = []
    return ctx


def _make_mock_itinerary():
    itin = MagicMock()
    itin.days = []
    itin.model_dump_json = MagicMock(return_value='{"title":"test"}')
    itin.model_dump = MagicMock(return_value={"title": "test"})
    return itin


@pytest.mark.asyncio
async def test_coordinator_accepts_agent_context():
    coordinator = PipelineCoordinator(
        db_session=AsyncMock(),
        llm_client=MagicMock(),
        amap_service=MagicMock(),
        agent_context=_make_agent_context(),
    )
    assert coordinator._agent_context is not None


@pytest.mark.asyncio
async def test_coordinator_without_agent_context():
    coordinator = PipelineCoordinator(
        db_session=AsyncMock(),
        llm_client=MagicMock(),
        amap_service=MagicMock(),
        agent_context=None,
    )
    assert coordinator._agent_context is None


@pytest.mark.asyncio
async def test_pipeline_calls_agent_enrich_between_filter_and_generate():
    coordinator = PipelineCoordinator(
        db_session=AsyncMock(),
        llm_client=MagicMock(),
        amap_service=MagicMock(),
        agent_context=_make_agent_context(),
    )
    coordinator._user_id = "test-user"

    with patch("backend.pipeline.stages.stage1_intent.extract_intent", new_callable=AsyncMock) as mock_intent, \
         patch("backend.pipeline.stages.stage2_filter.filter_pois", new_callable=AsyncMock) as mock_filter, \
         patch("backend.pipeline.stages.stage3_generate.generate_itinerary", new_callable=AsyncMock) as mock_generate, \
         patch("backend.pipeline.stages.stage4_validate.validate_itinerary", new_callable=AsyncMock) as mock_validate, \
         patch("backend.pipeline.stages.stage_agent.agent_enrich", new_callable=AsyncMock) as mock_agent_enrich:

        mock_intent.return_value = _make_intent()
        mock_filter.return_value = [MagicMock(tier=1, id="p1", name="test poi")]
        mock_agent_enrich.return_value = "天气晴朗，推荐户外活动"
        mock_generate.return_value = ("raw response", _make_mock_itinerary())
        mock_validate.return_value = MagicMock(is_valid=True, total_walking_minutes=10)

        with patch.object(coordinator, "_enrich_poi_coordinates", new_callable=AsyncMock), \
             patch.object(coordinator, "_save_to_db", new_callable=AsyncMock):
            await coordinator._run_pipeline_async("上海两天", None, None)

        assert mock_agent_enrich.called
        assert mock_intent.called
        assert mock_filter.called
        assert mock_generate.called


@pytest.mark.asyncio
async def test_enrichment_text_passed_to_generate():
    coordinator = PipelineCoordinator(
        db_session=AsyncMock(),
        llm_client=MagicMock(),
        amap_service=MagicMock(),
        agent_context=_make_agent_context(),
    )
    coordinator._user_id = "test-user"

    with patch("backend.pipeline.stages.stage1_intent.extract_intent", new_callable=AsyncMock) as mock_intent, \
         patch("backend.pipeline.stages.stage2_filter.filter_pois", new_callable=AsyncMock) as mock_filter, \
         patch("backend.pipeline.stages.stage3_generate.generate_itinerary", new_callable=AsyncMock) as mock_generate, \
         patch("backend.pipeline.stages.stage4_validate.validate_itinerary", new_callable=AsyncMock) as mock_validate, \
         patch("backend.pipeline.stages.stage_agent.agent_enrich", new_callable=AsyncMock) as mock_agent_enrich:

        mock_intent.return_value = _make_intent()
        mock_filter.return_value = [MagicMock(tier=1)]
        mock_agent_enrich.return_value = "上海今天晴天"
        mock_generate.return_value = ("raw", _make_mock_itinerary())
        mock_validate.return_value = MagicMock(is_valid=True, total_walking_minutes=10)

        with patch.object(coordinator, "_enrich_poi_coordinates", new_callable=AsyncMock), \
             patch.object(coordinator, "_save_to_db", new_callable=AsyncMock):
            await coordinator._run_pipeline_async("test", None, None)

        gen_call = mock_generate.call_args
        assert gen_call.kwargs.get("enrichment_context") == "上海今天晴天"


@pytest.mark.asyncio
async def test_pipeline_skips_agent_without_context():
    coordinator = PipelineCoordinator(
        db_session=AsyncMock(),
        llm_client=MagicMock(),
        amap_service=MagicMock(),
        agent_context=None,
    )
    coordinator._user_id = None
    coordinator._user_prefs = None

    with patch("backend.pipeline.stages.stage1_intent.extract_intent", new_callable=AsyncMock) as mock_intent, \
         patch("backend.pipeline.stages.stage2_filter.filter_pois", new_callable=AsyncMock) as mock_filter, \
         patch("backend.pipeline.stages.stage3_generate.generate_itinerary", new_callable=AsyncMock) as mock_generate, \
         patch("backend.pipeline.stages.stage4_validate.validate_itinerary", new_callable=AsyncMock) as mock_validate, \
         patch("backend.pipeline.stages.stage_agent.agent_enrich", new_callable=AsyncMock) as mock_agent_enrich:

        mock_intent.return_value = _make_intent()
        mock_filter.return_value = [MagicMock(tier=1)]
        mock_generate.return_value = ("raw", _make_mock_itinerary())
        mock_validate.return_value = MagicMock(is_valid=True, total_walking_minutes=10)

        with patch.object(coordinator, "_enrich_poi_coordinates", new_callable=AsyncMock), \
             patch.object(coordinator, "_save_to_db", new_callable=AsyncMock):
            await coordinator._run_pipeline_async("test", None, None)

        assert not mock_agent_enrich.called
        gen_call = mock_generate.call_args
        assert gen_call.kwargs.get("enrichment_context") == ""


@pytest.mark.asyncio
async def test_stage3_uses_enrichment_context():
    from backend.pipeline.stages.stage3_generate import generate_itinerary

    mock_llm = MagicMock()
    mock_llm.generate_json = AsyncMock(return_value='{"title":"test","summary":"s","days":[],"total_walking_minutes":0}')

    mock_itin = MagicMock()
    mock_itin.days = []

    with patch("backend.pipeline.stages.stage3_generate.parse_itinerary_output", new_callable=AsyncMock, return_value=mock_itin), \
         patch("backend.pipeline.stages.stage3_generate._load_prompt", return_value="sys\n{CITY}\n{USER_PREFERENCES}\n{TIER_A_POIS}\n{TIER_B_MATCHING_POIS}\n{DAYS}"), \
         patch("backend.pipeline.stages.stage3_generate._enforce_max_pois_per_day", return_value=mock_itin):

        _, result = await generate_itinerary(
            llm_client=mock_llm,
            intent=_make_intent(),
            poi_candidates=[],
            user_input="test",
            enrichment_context="天气好",
        )

    gen_call = mock_llm.generate_json.call_args
    messages = gen_call[0][0]
    user_msg = messages[1]["content"]
    assert "智能推荐补充信息" in user_msg
    assert "天气好" in user_msg


@pytest.mark.asyncio
async def test_stage3_works_without_enrichment():
    from backend.pipeline.stages.stage3_generate import generate_itinerary

    mock_llm = MagicMock()
    mock_llm.generate_json = AsyncMock(return_value='{"title":"test","summary":"s","days":[],"total_walking_minutes":0}')

    mock_itin = MagicMock()
    mock_itin.days = []

    with patch("backend.pipeline.stages.stage3_generate.parse_itinerary_output", new_callable=AsyncMock, return_value=mock_itin), \
         patch("backend.pipeline.stages.stage3_generate._load_prompt", return_value="sys\n{CITY}\n{USER_PREFERENCES}\n{TIER_A_POIS}\n{TIER_B_MATCHING_POIS}\n{DAYS}"), \
         patch("backend.pipeline.stages.stage3_generate._enforce_max_pois_per_day", return_value=mock_itin):

        _, result = await generate_itinerary(
            llm_client=mock_llm,
            intent=_make_intent(),
            poi_candidates=[],
            user_input="test",
            enrichment_context="",
        )

    gen_call = mock_llm.generate_json.call_args
    messages = gen_call[0][0]
    user_msg = messages[1]["content"]
    assert "智能推荐补充信息" not in user_msg


@pytest.mark.asyncio
async def test_agent_stage_emits_sse_events():
    coordinator = PipelineCoordinator(
        db_session=AsyncMock(),
        llm_client=MagicMock(),
        amap_service=MagicMock(),
        agent_context=_make_agent_context(),
    )
    coordinator._user_id = "test-user"

    spy_bus = _SpyEventBus()
    coordinator.event_bus = spy_bus
    spy_bus.itinerary_id = coordinator.itinerary_id

    with patch("backend.pipeline.stages.stage1_intent.extract_intent", new_callable=AsyncMock) as mock_intent, \
         patch("backend.pipeline.stages.stage2_filter.filter_pois", new_callable=AsyncMock) as mock_filter, \
         patch("backend.pipeline.stages.stage3_generate.generate_itinerary", new_callable=AsyncMock) as mock_generate, \
         patch("backend.pipeline.stages.stage4_validate.validate_itinerary", new_callable=AsyncMock) as mock_validate, \
         patch("backend.pipeline.stages.stage_agent.agent_enrich", new_callable=AsyncMock) as mock_agent_enrich:

        mock_intent.return_value = _make_intent()
        mock_filter.return_value = [MagicMock(tier=1)]
        mock_agent_enrich.return_value = "enrichment"
        mock_generate.return_value = ("raw", _make_mock_itinerary())
        mock_validate.return_value = MagicMock(is_valid=True, total_walking_minutes=10)

        with patch.object(coordinator, "_enrich_poi_coordinates", new_callable=AsyncMock), \
             patch.object(coordinator, "_save_to_db", new_callable=AsyncMock):
            await coordinator._run_pipeline_async("test", None, None)

    agent_events = [e for e in spy_bus.events if e.stage == "agent"]
    assert len(agent_events) >= 2
    assert any(e.message == "开始智能推荐..." for e in agent_events)
    assert any(e.message == "智能推荐完成" for e in agent_events)
