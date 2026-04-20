"""Agent module — SDK-based agent with tool-call support.

Exports:
    - init_agent_sdk: Call at startup to configure SDK for DeepSeek ChatCompletions.
    - AgentContext: Request-scoped Pydantic model for tool DI.
    - create_deepseek_model: Helper to build SDK model adapter.
    - AgentLoop: Legacy loop (retained during Phase 12 migration, retires in Plan 04).
"""

from agents import set_default_openai_api

from backend.agent.context import AgentContext, create_deepseek_model
from backend.agent.loop import AgentLoop, MAX_ITERATIONS


def init_agent_sdk() -> None:
    """Configure OpenAI Agents SDK to use ChatCompletions API.

    Must be called once at application startup before any Agent runs.
    DeepSeek only supports ChatCompletions, not the Responses API.
    """
    set_default_openai_api("chat_completions")


__all__ = [
    "AgentContext",
    "AgentLoop",
    "MAX_ITERATIONS",
    "create_deepseek_model",
    "init_agent_sdk",
]
