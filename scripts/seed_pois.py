"""Seed POI and scenario data into the database."""

import asyncio
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from db.init_db import AsyncSessionFactory, init_db
from models.database import POI, Scenario
from sqlalchemy import select


def deterministic_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shitu.{name}"))


async def seed_pois():
    data = json.loads(Path("data/pois/shanghai.json").read_text(encoding="utf-8"))
    async with AsyncSessionFactory() as session:
        for p in data["pois"]:
            existing = await session.execute(select(POI).where(POI.amap_id == p["amap_id"]))
            if existing.scalar_one_or_none():
                continue
            poi = POI(
                id=deterministic_uuid(f"poi.{p['amap_id']}"),
                amap_id=p["amap_id"],
                name=p["name"],
                city="上海",
                tier=p["tier"],
                category=p["category"],
                lat=p["latitude"],
                lng=p["longitude"],
                address=p["address"],
                taste_tags=json.dumps(p["taste_tags"], ensure_ascii=False),
                highlight_note=p.get("highlight_note", ""),
                permanent_features=json.dumps(p.get("permanent_features", []), ensure_ascii=False),
                opening_hours=p.get("opening_hours", ""),
                rating=p.get("rating", 0.0),
                walk_time_minutes=0,
            )
            session.add(poi)
        await session.commit()
    tier_a = sum(1 for p in data["pois"] if p["tier"] == 1)
    tier_b = sum(1 for p in data["pois"] if p["tier"] == 2)
    print(f"Seeded {len(data['pois'])} POIs (Tier A: {tier_a}, Tier B: {tier_b})")


async def seed_scenarios():
    scenario_path = Path("data/scenarios/scenarios.json")
    if not scenario_path.exists():
        print("No scenarios.json found, skipping scenario seeding")
        return
    data = json.loads(scenario_path.read_text(encoding="utf-8"))
    async with AsyncSessionFactory() as session:
        for s in data:
            existing = await session.execute(select(Scenario).where(Scenario.name == s["name"]))
            if existing.scalar_one_or_none():
                continue
            scenario = Scenario(
                id=deterministic_uuid(f"scenario.{s['id']}"),
                name=s["name"],
                description=s["description"],
                user_input=s["user_input"],
                city=s["city"],
                tags=json.dumps(s["tags"], ensure_ascii=False),
            )
            session.add(scenario)
        await session.commit()
    print(f"Seeded {len(data)} scenarios")


async def main():
    await init_db()
    await seed_pois()
    await seed_scenarios()
    print("All data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
