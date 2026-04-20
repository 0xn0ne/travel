"""Async client for 高德开放平台 Web Service APIs (Amap).

Provides walking route validation, POI search, and weather query.
Uses httpx async client with tenacity retry and concurrent request limiting.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.models.database import AmapCache

logger = logging.getLogger(__name__)


@dataclass
class WalkingRouteResult:
    distance_meters: int
    duration_minutes: int
    path_found: bool


class AmapService:
    """Async client for Amap walking route API."""

    BASE_URL = "https://restapi.amap.com/v3"
    _call_count: int = 0
    QUOTA_WARNING_THRESHOLD = 4000

    def __init__(self, api_key: str, db_session: AsyncSession | None = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self._db_session = db_session

    @property
    def call_count(self) -> int:
        return AmapService._call_count

    @staticmethod
    def increment_call_count() -> int:
        AmapService._call_count += 1
        count = AmapService._call_count
        if count in (100, 500, 1000):
            logging.warning(f"Amap API call #{count} — milestone reached")
        if count >= AmapService.QUOTA_WARNING_THRESHOLD and count % 100 == 0:
            logger.warning(f"Amap API call #{count} — 80%% quota warning (5000/mo limit)")
        return count

    @staticmethod
    def _hash_query(method: str, params: dict) -> str:
        canonical = json.dumps(params, sort_keys=True, ensure_ascii=False)
        raw = f"{method}:{canonical}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _cache_lookup(self, query_hash: str) -> dict | None:
        if not self._db_session:
            return None
        now = datetime.now(timezone.utc)
        stmt = select(AmapCache).where(
            AmapCache.query_hash == query_hash,
            AmapCache.expires_at > now,
        )
        result = await self._db_session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return json.loads(row.response_json)
        return None

    async def _cache_store(
        self,
        query_hash: str,
        method: str,
        response_json: str,
        ttl_days: int,
    ) -> None:
        if not self._db_session:
            return
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=ttl_days)
        existing = await self._db_session.get(AmapCache, query_hash)
        if existing:
            existing.response_json = response_json
            existing.api_method = method
            existing.expires_at = expires
        else:
            self._db_session.add(
                AmapCache(
                    query_hash=query_hash,
                    response_json=response_json,
                    api_method=method,
                    expires_at=expires,
                )
            )
        await self._db_session.flush()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def get_walking_route(
        self,
        origin_lng: float,
        origin_lat: float,
        dest_lng: float,
        dest_lat: float,
    ) -> WalkingRouteResult:
        """Get walking route between two points.

        Amap uses longitude,latitude coordinate order (opposite of Google Maps).
        Returns distance in meters and duration in minutes.
        """
        cache_params = {
            "origin": f"{origin_lng},{origin_lat}",
            "destination": f"{dest_lng},{dest_lat}",
        }
        qhash = self._hash_query("walking", cache_params)
        cached = await self._cache_lookup(qhash)
        if cached:
            return WalkingRouteResult(**cached)

        self.increment_call_count()

        response = await self.client.get(
            f"{self.BASE_URL}/direction/walking",
            params={
                "key": self.api_key,
                "origin": f"{origin_lng},{origin_lat}",
                "destination": f"{dest_lng},{dest_lat}",
            },
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1" or "route" not in data:
            return WalkingRouteResult(distance_meters=0, duration_minutes=15, path_found=False)

        path = data["route"]["paths"][0]
        result = WalkingRouteResult(
            distance_meters=int(path["distance"]),
            duration_minutes=int(int(path["duration"]) / 60),
            path_found=True,
        )

        await self._cache_store(
            qhash,
            "walking",
            json.dumps(
                {
                    "distance_meters": result.distance_meters,
                    "duration_minutes": result.duration_minutes,
                    "path_found": result.path_found,
                }
            ),
            ttl_days=30,
        )

        return result

    async def validate_segments(
        self,
        poi_pairs: list[tuple[float, float, float, float]],
        max_acceptable_minutes: int = 15,
    ) -> list[tuple[int, bool]]:
        """Validate multiple walking segments concurrently (max 5 concurrent).

        Args:
            poi_pairs: list of (origin_lng, origin_lat, dest_lng, dest_lat)

        Returns:
            list of (duration_minutes, is_acceptable) in same order as input
        """
        semaphore = asyncio.Semaphore(5)

        async def validate_one(
            origin_lng: float, origin_lat: float, dest_lng: float, dest_lat: float
        ) -> tuple[int, bool]:
            async with semaphore:
                try:
                    route = await self.get_walking_route(origin_lng, origin_lat, dest_lng, dest_lat)
                    return route.duration_minutes, route.duration_minutes <= max_acceptable_minutes
                except Exception:
                    return 15, False  # flag on error

        tasks = [validate_one(*pair) for pair in poi_pairs]
        return await asyncio.gather(*tasks)

    async def close(self):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def search_pois(
        self,
        city: str,
        keywords: str,
        types: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """Search POIs using Amap Text Search API.

        Amap API: https://restapi.amap.com/v3/place/text
        Returns dict with pois list and total count.
        """
        cache_params = {
            "keywords": keywords,
            "city": city,
            "types": types or "",
            "page": page,
            "limit": limit,
        }
        qhash = self._hash_query("place_text", cache_params)
        cached = await self._cache_lookup(qhash)
        if cached:
            return cached

        self.increment_call_count()

        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "offset": page * limit - limit,
            "count": limit,
            "extensions": "all",
        }
        if types:
            params["type"] = types

        response = await self.client.get(
            f"{self.BASE_URL}/place/text",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            result = {"pois": [], "total": 0}
            await self._cache_store(qhash, "place_text", json.dumps(result), ttl_days=7)
            return result

        pois = []
        for poi in data.get("pois", []):
            pois.append(
                {
                    "amap_id": poi.get("id", ""),
                    "name": poi.get("name", ""),
                    "location": poi.get("location", ""),
                    "address": poi.get("address", ""),
                    "category": poi.get("type", ""),
                    "rating": float(poi.get("biz_ext", {}).get("rating", 0)) or None,
                    "opening_hours": poi.get("opening_hours", ""),
                }
            )

        result = {"pois": pois, "total": int(data.get("count", 0))}
        await self._cache_store(qhash, "place_text", json.dumps(result), ttl_days=7)
        return result

    async def batch_search_pois(
        self,
        city: str,
        keyword_list: list[str],
        types: str | None = None,
        limit_per_keyword: int = 20,
    ) -> list[dict]:
        """Search POIs for multiple keywords, deduplicate by amap_id.

        Used for acquiring POI data for a city with various taste categories.
        Implements rate limiting: max 100 calls per session (per D-09).
        """
        all_pois = {}
        call_count = 0
        max_calls = 100

        for keyword in keyword_list:
            if call_count >= max_calls:
                logging.warning(f"Amap rate limit reached ({max_calls} calls), stopping acquisition")
                break

            page = 1
            while True:
                if call_count >= max_calls:
                    break
                result = await self.search_pois(
                    city=city,
                    keywords=keyword,
                    types=types,
                    page=page,
                    limit=limit_per_keyword,
                )
                call_count += 1

                for poi in result["pois"]:
                    if poi["amap_id"] not in all_pois:
                        all_pois[poi["amap_id"]] = poi

                if page * limit_per_keyword >= result["total"]:
                    break
                page += 1
                await asyncio.sleep(0.1)  # avoid rate limit

        return list(all_pois.values())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def get_weather(self, city_name: str, days: int = 3) -> dict:
        """Query weather for a city using 高德 weather API.

        Uses CityConfig adcode mapping for city→adcode resolution.
        Fetches both live conditions (extensions=base) and forecast (extensions=all).

        Args:
            city_name: Chinese city name, e.g. "上海", "杭州".
            days: Number of forecast days to return (1-7, default 3).

        Returns:
            Dict with city, current conditions, and forecast list.
        """
        from backend.services.city_config import get_city_config

        city_config = get_city_config(city_name)
        if not city_config:
            return {"error": f"暂不支持该城市的天气查询: {city_name}"}

        adcode = city_config.adcode

        # Fetch current conditions
        self.increment_call_count()
        live_resp = await self.client.get(
            f"{self.BASE_URL}/weather/weatherInfo",
            params={
                "key": self.api_key,
                "city": adcode,
                "extensions": "base",
            },
        )
        live_resp.raise_for_status()
        live_data = live_resp.json()

        current = {}
        if live_data.get("status") == "1" and live_data.get("lives"):
            live = live_data["lives"][0]
            current = {
                "temperature": live.get("temperature", ""),
                "weather": live.get("weather", ""),
                "winddirection": live.get("winddirection", ""),
                "windpower": live.get("windpower", ""),
                "humidity": live.get("humidity", ""),
                "reporttime": live.get("reporttime", ""),
            }

        # Fetch forecast
        self.increment_call_count()
        forecast_resp = await self.client.get(
            f"{self.BASE_URL}/weather/weatherInfo",
            params={
                "key": self.api_key,
                "city": adcode,
                "extensions": "all",
            },
        )
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()

        forecast = []
        if forecast_data.get("status") == "1" and forecast_data.get("forecasts"):
            casts = forecast_data["forecasts"][0].get("casts", [])
            for cast in casts[:days]:
                forecast.append(
                    {
                        "date": cast.get("date", ""),
                        "dayweather": cast.get("dayweather", ""),
                        "nightweather": cast.get("nightweather", ""),
                        "daytemp": cast.get("daytemp", ""),
                        "nighttemp": cast.get("nighttemp", ""),
                        "daywind": cast.get("daywind", ""),
                        "nightwind": cast.get("nightwind", ""),
                        "daypower": cast.get("daypower", ""),
                        "nightpower": cast.get("nightpower", ""),
                    }
                )

        return {
            "city": city_name,
            "current": current,
            "forecast": forecast,
        }
