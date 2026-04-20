"""AgentContext — request-scoped services and config for SDK Agent tools.

Per D-09, D-10, D-11: Pydantic model holding all services that tools need
via RunContextWrapper DI pattern.
"""

from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict

from backend.services.amap_service import AmapService


class AgentContext(BaseModel):
    """Request-scoped context injected into every SDK tool call.

    Fields use Any for types Pydantic can't serialize (AsyncSession, Settings).
    Access via ctx.context inside @function_tool handlers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    db_session: Any  # AsyncSession — not Pydantic-serializable
    amap_service: AmapService
    user_id: str | None = None
    settings: Any  # Settings from backend.config


def create_deepseek_model(
    api_key: str,
    base_url: str = "https://api.deepseek.com",
    model: str = "deepseek-chat",
) -> Any:
    """Create an OpenAIChatCompletionsModel configured for DeepSeek.

    DeepSeek exposes an OpenAI-compatible API. The SDK's ChatCompletions
    model adapter wraps it for use with Agent(model=...).

    Args:
        api_key: DeepSeek API key.
        base_url: DeepSeek API base URL.
        model: Model identifier (default: deepseek-chat = DeepSeek-V3).

    Returns:
        OpenAIChatCompletionsModel instance.
    """
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return OpenAIChatCompletionsModel(model=model, openai_client=client)
