"""Stage 4: Route validation via Amap API + hallucination check.

Phase 1: Verify all poi_ids in itinerary exist in candidate list (hallucination check).
Phase 2: For each consecutive POI pair, validate walking time via Amap walking API.
"""

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pydantic import FlaggedSegment, Itinerary, POICandidate, ValidationResult

if TYPE_CHECKING:
    from backend.services.amap_service import AmapService

# Module-level call counter for Amap API usage tracking
_amap_call_count = 0


def get_amap_call_count() -> int:
    return _amap_call_count


async def validate_itinerary(
    amap_service: "AmapService",
    db_session: AsyncSession,
    itinerary: Itinerary,
    poi_candidates: list[POICandidate],
) -> ValidationResult:
    """Validate itinerary: hallucination check + walking route validation via Amap API."""

    # Build valid POI ID set and POI map
    valid_ids = {p.id for p in poi_candidates}

    # Phase 1: Hallucination check
    all_poi_ids = [poi.poi_id for day in itinerary.days for poi in day.pois]
    invalid_ids = [pid for pid in all_poi_ids if pid not in valid_ids]
    has_hallucination = len(invalid_ids) > 0

    if has_hallucination:
        import logging

        logging.warning(f"Hallucinated POI IDs detected: {invalid_ids}")

    # Phase 2: Walking route validation
    # Build POI coordinate lookup from candidates (Stage 2 already loaded coords)
    # We need a way to get coordinates. Use the DB session to look up by POI id.
    from backend.models.database import POI as POIRow  # noqa: N811

    poi_ids_needed = list(set(all_poi_ids))
    coords_result = await db_session.execute(
        select(POIRow.id, POIRow.latitude, POIRow.longitude).where(POIRow.id.in_(poi_ids_needed))
    )
    coords = {row[0]: (row[1], row[2]) for row in coords_result.all()}

    # Collect consecutive POI pairs per day
    segments: list[FlaggedSegment] = []
    total_walking = 0
    flagged_count = 0

    for day in itinerary.days:
        for i in range(len(day.pois) - 1):
            from_id = day.pois[i].poi_id
            to_id = day.pois[i + 1].poi_id
            walk_mins = day.pois[i].walk_to_next_minutes

            if from_id not in coords or to_id not in coords:
                # Missing coords — flag as potentially problematic
                segments.append(
                    FlaggedSegment(
                        from_poi=from_id,
                        to_poi=to_id,
                        walk_minutes=walk_mins or 10,
                        is_acceptable=False,
                    )
                )
                total_walking += walk_mins or 10
                flagged_count += 1
                continue

            from_lat, from_lng = coords[from_id]
            to_lat, to_lng = coords[to_id]

            try:
                route = await amap_service.get_walking_route(from_lng, from_lat, to_lng, to_lat)
                walk_mins = route.duration_minutes
            except Exception:
                walk_mins = walk_mins or 10

            total_walking += walk_mins
            is_acceptable = walk_mins <= 15
            if not is_acceptable:
                flagged_count += 1

            segments.append(
                FlaggedSegment(
                    from_poi=from_id,
                    to_poi=to_id,
                    walk_minutes=walk_mins,
                    is_acceptable=is_acceptable,
                )
            )

    is_valid = not has_hallucination and flagged_count == 0

    return ValidationResult(
        is_valid=is_valid,
        flagged_segments=segments,
        total_walking_minutes=total_walking,
    )
