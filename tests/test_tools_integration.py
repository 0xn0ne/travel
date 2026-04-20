"""Integration tests for SDK Agent + all tools."""

import pytest
from unittest.mock import MagicMock

from agents import Agent
from backend.agent.context import AgentContext, create_deepseek_model
from backend.services.amap_service import AmapService
from backend.tools import ALL_TOOLS


def _make_mock_amap() -> AmapService:
    """Create an AmapService with a test API key."""
    return AmapService(api_key="test-key")


def test_all_tools_count():
    """ALL_TOOLS list has exactly 10 tool functions."""
    assert len(ALL_TOOLS) == 10, f"Expected 10 tools, got {len(ALL_TOOLS)}"


def test_sdk_agent_with_all_tools():
    """SDK Agent can be constructed with all tools."""
    model = create_deepseek_model(api_key="test-key")
    agent = Agent(
        name="test-agent",
        tools=ALL_TOOLS,
        instructions="You are a travel assistant.",
        model=model,
    )
    assert agent.name == "test-agent"
    assert len(agent.tools) == 10


def test_tool_names():
    """Each tool has the expected name."""
    expected_names = {
        "search_pois",
        "query_weather",
        "get_user_preferences",
        "get_itinerary_context",
        "web_search",
        "web_fetch",
        "list_files",
        "read_file",
        "write_file",
        "execute_command",
    }
    actual_names = {tool.name for tool in ALL_TOOLS}
    assert actual_names == expected_names, f"Missing: {expected_names - actual_names}, Extra: {actual_names - expected_names}"


def test_tool_names_are_chinese_friendly():
    """Tool names are valid identifiers (no spaces, no special chars)."""
    for tool in ALL_TOOLS:
        assert tool.name.isidentifier(), f"Tool name '{tool.name}' is not a valid identifier"


def test_agent_context_with_all_mock_services():
    """AgentContext constructs with all services mocked."""
    ctx = AgentContext(
        db_session=MagicMock(),
        amap_service=_make_mock_amap(),
        user_id="test-user-id",
        settings=MagicMock(),
    )
    assert ctx.user_id == "test-user-id"
    assert ctx.db_session is not None
    assert ctx.amap_service is not None
