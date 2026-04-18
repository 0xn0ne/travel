"""Seed POI data from JSON file into SQLite database."""

import asyncio
import json
import uuid

from sqlalchemy import delete

from backend.db import init_db as _db_mod
from backend.db.init_db import init_db
from backend.models.database import POI


def determine_tier(rating: float | None, is_chain: bool) -> int:
    """Auto-tiering: Tier B = rating > 4.0 and non-chain, Tier C = rest (per D-10).

    Tier A is curated and not auto-assigned.
    """
    if rating is not None and rating > 4.0 and not is_chain:
        return 2  # Tier B
    return 3  # Tier C


def poi_from_json(data: dict, city: str) -> POI:
    """Convert JSON POI dict to POI model instance.

    Existing JSON has: amap_id, name, tier (1=A, 2=B), category,
    latitude, longitude, address, taste_tags, highlight_note,
    permanent_features, opening_hours, rating.
    """
    lat = data.get("latitude")
    lng = data.get("longitude")

    if lat is None or lng is None:
        # May need to parse from location field "lng,lat" in future acquisitions
        pass

    return POI(
        id=str(uuid.uuid4()),
        amap_id=data.get("amap_id", ""),
        name=data.get("name", ""),
        city=city,
        tier=data.get("tier", 3),
        category=data.get("category", ""),
        latitude=lat or 0.0,
        longitude=lng or 0.0,
        address=data.get("address"),
        taste_tags=json.dumps(data.get("taste_tags", []), ensure_ascii=False),
        highlight_note=data.get("highlight_note"),
        permanent_features=json.dumps(data.get("permanent_features", []), ensure_ascii=False)
        if data.get("permanent_features")
        else None,
        opening_hours=data.get("opening_hours"),
        rating=data.get("rating"),
        is_chain=data.get("is_chain", False),
    )


async def seed_pois_from_json(json_path: str, city: str, clear_existing: bool = False):
    """Load POI data from JSON file into database.

    Args:
        json_path: Path to JSON file with pois array
        city: City name (e.g., "上海", "杭州")
        clear_existing: If True, delete existing POIs for this city first
    """
    await init_db()

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    pois_data = data.get("pois", [])

    async with _db_mod.AsyncSessionFactory() as sess:
        if clear_existing:
            # Delete existing POIs for this city
            await sess.execute(delete(POI).where(POI.city == city))

        for poi_data in pois_data:
            poi = poi_from_json(poi_data, city)
            sess.add(poi)

        await sess.commit()
        print(f"Seeded {len(pois_data)} POIs for {city}")


if __name__ == "__main__":
    import sys

    city = sys.argv[1] if len(sys.argv) > 1 else "上海"
    json_file = sys.argv[2] if len(sys.argv) > 2 else f"data/pois/{city.lower()}.json"
    asyncio.run(seed_pois_from_json(json_file, city))
