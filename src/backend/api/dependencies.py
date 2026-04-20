"""FastAPI dependencies for database sessions and service clients."""

from functools import lru_cache

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import decode_token, get_jwt_secret_key
from backend.config import get_settings
from backend.db.init_db import get_async_session
from backend.llm.client import ChatGPTClient, DeepSeekClient, LLMClient
from backend.services.amap_service import AmapService

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
