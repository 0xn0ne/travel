"""Itinerary routes: list user itineraries, get single itinerary."""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_db
from backend.models.database import ItineraryRow, POI

router = APIRouter()


class ItineraryCard(BaseModel):
    id: str
    city: str
    title: str
    date: str
    poi_count: int | None = None


@router.get("/itineraries")
async def list_itineraries(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List current user's past itineraries as cards."""
    result = await db.execute(
        select(ItineraryRow)
        .where(ItineraryRow.user_id == current_user["id"])
        .order_by(desc(ItineraryRow.created_at))
        .limit(50)
    )
    itineraries = result.scalars().all()

    cards = []
    for it in itineraries:
        title = f"{it.city}行程"
        poi_count = None
        try:
            parsed = json.loads(it.parsed_itinerary) if it.parsed_itinerary else {}
            if isinstance(parsed, dict):
                title = parsed.get("title", title)
                poi_count = parsed.get("poi_count")
        except json.JSONDecodeError:
            pass

        cards.append(
            ItineraryCard(
                id=it.id,
                city=it.city,
                title=title,
                date=it.created_at.strftime("%Y-%m-%d") if it.created_at else "",
                poi_count=poi_count,
            )
        )
    return cards


async def _enrich_pois_with_coordinates(itinerary_data: dict, db: AsyncSession) -> dict:
    """Enrich POIs in itinerary with coordinates from the POI database."""
    if not itinerary_data or "days" not in itinerary_data:
        return itinerary_data
    
    # Collect all unique poi_ids that have coordinates in the database
    all_poi_ids = set()
    for day in itinerary_data.get("days", []):
        for poi in day.get("pois", []):
            poi_id = poi.get("poi_id")
            if poi_id:
                all_poi_ids.add(poi_id)
    
    if not all_poi_ids:
        return itinerary_data
    
    # Batch query POI coordinates from database
    result = await db.execute(
        select(POI.id, POI.latitude, POI.longitude).where(POI.id.in_(all_poi_ids))
    )
    poi_coords = {row[0]: {"latitude": row[1], "longitude": row[2]} for row in result.all()}
    
    # Enrich each POI with coordinates
    for day in itinerary_data.get("days", []):
        for poi in day.get("pois", []):
            poi_id = poi.get("poi_id")
            if poi_id and poi_id in poi_coords:
                poi["latitude"] = poi_coords[poi_id]["latitude"]
                poi["longitude"] = poi_coords[poi_id]["longitude"]
    
    return itinerary_data


@router.get("/itinerary/{itinerary_id}")
async def get_itinerary(itinerary_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItineraryRow).where(ItineraryRow.id == itinerary_id))
    row = result.scalar_one_or_none()
    if not row or not row.parsed_itinerary:
        raise HTTPException(404, "Itinerary not found")
    parsed = json.loads(row.parsed_itinerary)
    
    # Enrich POIs with coordinates from database
    parsed = await _enrich_pois_with_coordinates(parsed, db)
    
    return {
        "id": row.id,
        "scenario_id": row.scenario_id,
        "group": row.group,
        "city": row.city,
        "itinerary": parsed,
    }


@router.get("/itinerary/{itinerary_id}/meta")
async def get_itinerary_meta(itinerary_id: str, db: AsyncSession = Depends(get_db)):
    """Get OG meta tags data for an itinerary (public, no auth required)."""
    result = await db.execute(select(ItineraryRow).where(ItineraryRow.id == itinerary_id))
    row = result.scalar_one_or_none()
    if not row or not row.parsed_itinerary:
        raise HTTPException(404, "Itinerary not found")
    
    parsed = json.loads(row.parsed_itinerary)
    
    # Extract title, description (summary), and city
    title = parsed.get("title", f"{row.city}行程")
    description = parsed.get("summary", f"{row.city}的精选行程，发现独特体验。")
    city = row.city
    
    return {
        "title": title,
        "description": description,
        "city": city,
    }