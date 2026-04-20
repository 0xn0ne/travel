"""Integration tests for AgentContext and SDK foundation."""

import pytest
from unittest.mock import MagicMock

from agents import Agent
from backend.agent.context import AgentContext, create_deepseek_model
from backend.agent import init_agent_sdk
from backend.services.amap_service import AmapService


def _make_mock_amap() -> AmapService:
    """Create an AmapService with a real API key but mock internals for testing."""
    return AmapService(api_key="test-key")


def test_agent_context_with_mock_services():
    """AgentContext constructs with mock services."""
    ctx = AgentContext(
        db_session=MagicMock(),
        amap_service=_make_mock_amap(),
        user_id=None,
        settings=MagicMock(),
    )
    assert ctx.user_id is None
    assert ctx.db_session is not None


def test_agent_context_with_user():
    """AgentContext constructs with user_id."""
    ctx = AgentContext(
        db_session=MagicMock(),
        amap_service=_make_mock_amap(),
        user_id="test-uuid-123",
        settings=MagicMock(),
    )
    assert ctx.user_id == "test-uuid-123"


def test_create_deepseek_model():
    """create_deepseek_model returns model with correct name."""
    model = create_deepseek_model(api_key="test-key")
    assert model.model == "deepseek-chat"


def test_init_agent_sdk():
    """init_agent_sdk sets chat_completions API without error."""
    init_agent_sdk()  # Should not raise


def test_sdk_agent_construction():
    """SDK Agent can be constructed with empty tools and DeepSeek model."""
    model = create_deepseek_model(api_key="test-key")
    agent = Agent(
        name="test-agent",
        tools=[],
        instructions="You are a test agent.",
        model=model,
    )
    assert agent.name == "test-agent"
    assert len(agent.tools) == 0
