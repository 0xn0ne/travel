"""POI nearby search API for P-map (即兴玩家) page."""

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class AmapClient:
    BASE_URL = "https://restapi.amap.com/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_around(
        self,
        keywords: str,
        location: str,  # "lng,lat"
        radius: int = 5000,
        city: str | None = None,
        page: int = 1,
        count: int = 20,
    ) -> dict:
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "location": location,
            "radius": radius,
            "offset": count,
            "page": page,
            "extensions": "all",
        }
        if city:
            params["city"] = city
        response = await self.client.get(f"{self.BASE_URL}/place/around", params=params)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()


class POISearchRequest(BaseModel):
    keywords: str
    city: str = ""
    location: str  # "lng,lat"
    radius: int = 5000
    pageSize: int = 20
    pageNum: int = 1


class POIItem(BaseModel):
    id: str
    name: str
    location: str
    address: str
    type: str
    rating: float | None = None
    biz_ext: dict | None = None


class POISearchResponse(BaseModel):
    pois: list[dict]
    total: int


@router.post("/poi/search", response_model=POISearchResponse)
async def search_poi(req: POISearchRequest):
    """Search POIs around a circle area from AMap."""
    settings = get_settings()
    if not settings.amap_api_key:
        raise HTTPException(status_code=500, detail="AMap API key not configured")

    client = AmapClient(settings.amap_api_key)
    try:
        data = await client.search_around(
            keywords=req.keywords,
            location=req.location,
            radius=req.radius,
            city=req.city or None,
            page=req.pageNum,
            count=req.pageSize,
        )
    finally:
        await client.close()

    if data.get("status") != "1":
        logger.warning("AMap search failed: %s", data.get("info", "unknown error"))
        return POISearchResponse(pois=[], total=0)

    pois = []
    for poi in data.get("pois", []):
        rating_str = poi.get("biz_ext", {}).get("rating", "0")
        rating = float(rating_str) if rating_str else None
        pois.append(
            {
                "id": poi.get("id", ""),
                "name": poi.get("name", ""),
                "location": poi.get("location", ""),
                "address": poi.get("address", ""),
                "type": poi.get("type", ""),
                "rating": rating,
                "biz_ext": poi.get("biz_ext", {}),
            }
        )

    return POISearchResponse(pois=pois, total=int(data.get("count", 0)))
