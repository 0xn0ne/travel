"""GET /api/scenarios — list all test scenarios."""

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.models.database import ItineraryRow, Scenario

router = APIRouter()


@router.get("/scenarios")
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scenario))
    scenarios = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "user_input": s.user_input,
            "city": s.city,
            "tags": s.tags,
        }
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}/itineraries")
async def get_scenario_itineraries(scenario_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItineraryRow).where(ItineraryRow.scenario_id == scenario_id))
    rows = result.scalars().all()
    by_group = {}
    for row in rows:
        parsed = json.loads(row.parsed_itinerary)
        by_group[row.group] = {
            "id": row.id,
            "group": row.group,
            "itinerary": parsed,
        }
    return {"scenario_id": scenario_id, "itineraries": by_group}
