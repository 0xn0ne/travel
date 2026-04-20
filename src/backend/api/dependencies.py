"""FastAPI dependencies for database sessions and service clients."""

from functools import lru_cache

from agents import Agent
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.context import AgentContext, create_deepseek_model
from backend.agent.loop import AgentLoop
from backend.api.auth import decode_token, get_jwt_secret_key
from backend.config import get_settings
from backend.db.init_db import get_async_session
from backend.llm.client import ChatGPTClient, DeepSeekClient, LLMClient
from backend.services.amap_service import AmapService
from backend.tools import ALL_TOOLS
from backend.tools.registry import ToolRegistry

get_db = get_async_session


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    return LLMClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
    )


@lru_cache
def get_chatgpt_client() -> ChatGPTClient:
    settings = get_settings()
    return ChatGPTClient(api_key=settings.openai_api_key)


@lru_cache
def get_tool_registry() -> ToolRegistry:
    """Return singleton ToolRegistry loaded from config.yml (per D-12)."""
    return ToolRegistry(config_path="config.yml")


def get_agent_loop(
    llm: LLMClient = Depends(get_llm_client),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> AgentLoop:
    """Create request-scoped AgentLoop. EventBus is injected at call sites (pipeline/chat)."""
    return AgentLoop(llm=llm, tool_registry=registry)


def get_amap_service(db: AsyncSession = Depends(get_db)) -> AmapService:
    settings = get_settings()
    return AmapService(api_key=settings.amap_api_key, db_session=db)


async def get_current_user(
    authorization: str = Header(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate JWT from Authorization header. Returns user dict.

    Raises HTTPException 401 if token is missing, invalid, or user not found.
    """
    from fastapi import HTTPException
    from sqlalchemy import select

    from backend.models.database import User

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]  # strip "Bearer "
    secret_key = get_jwt_secret_key()
    payload = decode_token(token, secret_key)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch user from DB
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "taste_tags_default": user.taste_tags_default,
        "budget_default": user.budget_default,
    }


async def get_current_user_optional(
    authorization: str | None = Header(None),
    db: AsyncSession | None = Depends(get_db),
) -> dict | None:
    """Optional auth — returns user dict or None if no valid token."""
    from fastapi import HTTPException

    if authorization is None:
        return None

    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


def get_agent_context(
    db: AsyncSession = Depends(get_db),
    amap: AmapService = Depends(get_amap_service),
    user: dict | None = Depends(get_current_user_optional),
) -> AgentContext:
    """Create request-scoped AgentContext with all services (per D-09)."""
    settings = get_settings()
    return AgentContext(
        db_session=db,
        amap_service=amap,
        user_id=user["id"] if user else None,
        settings=settings,
    )


@lru_cache
def get_sdk_agent() -> Agent:
    """Create SDK Agent with all tools and DeepSeek model (per D-01, D-02)."""
    settings = get_settings()
    model = create_deepseek_model(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
    )
    return Agent(
        name="拾途助手",
        tools=ALL_TOOLS,
        instructions="你是一个旅行助手，帮助用户规划行程。",
        model=model,
    )
