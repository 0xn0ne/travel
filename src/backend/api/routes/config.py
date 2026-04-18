"""Config routes: public configuration endpoints."""

from fastapi import APIRouter

from backend.config import get_settings

router = APIRouter()


@router.get("/config/amap-key")
async def get_amap_key():
    """Get the Amap JS API key for frontend map initialization.

    This endpoint is public (no auth required) because the JS API key
    is domain-restricted and designed for client-side exposure.
    """
    settings = get_settings()
    return {"key": settings.amap_api_key}
