"""Stage 2: Pre-filter POIs by city + taste_tags matching, handle Group A/B highlight_note.

Supports optional dynamic Amap POI expansion and user preference passthrough.
"""

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.seed_pois import determine_tier
from backend.models.database import POI
from backend.models.pydantic import IntentOutput, POICandidate

if TYPE_CHECKING:
    from backend.services.amap_service import AmapService

logger = logging.getLogger(__name__)

TIER_WEIGHTS = {1: 3, 2: 2, 3: 1}


def _poi_to_candidate(poi: POI, include_highlight: bool = True) -> POICandidate:
    """Convert SQLAlchemy POI row to Pydantic POICandidate."""
    return POICandidate(
        id=poi.id,
        name=poi.name,
        tier=poi.tier,
        category=poi.category,
        taste_tags=json.loads(poi.taste_tags) if poi.taste_tags else [],
        highlight_note=poi.highlight_note if include_highlight else None,
        permanent_features=json.loads(poi.permanent_features) if poi.permanent_features else [],
        walk_time_minutes=poi.walk_time_minutes,
        rating=poi.rating,
        latitude=poi.latitude,
        longitude=poi.longitude,
    )


def _amap_to_candidate(poi_data: dict) -> POICandidate:
    """Convert Amap search result dict to POICandidate."""
    rating = poi_data.get("rating")
    return POICandidate(
        id=poi_data["amap_id"],
        name=poi_data.get("name", ""),
        tier=determine_tier(rating, False),  # auto-tier: B if rating>4.0, else C
        category=poi_data.get("category", ""),
        taste_tags=[],  # Amap results don't have taste_tags
        highlight_note=None,
        rating=rating,
    )


def _score_poi(poi_tags: list[str], tier: int, rating: float | None, interest_tags: list[str]) -> float:
    """Score a POI by taste_tag overlap + tier weight + rating."""
    overlap = len(set(poi_tags) & set(interest_tags))
    tier_score = TIER_WEIGHTS.get(tier, 1)
    rating_score = (rating or 0.0) / 5.0
    return overlap * 2.0 + tier_score + rating_score


async def filter_pois(
    db_session: AsyncSession,
    intent: IntentOutput,
    group: str | None = None,
    amap_service: "AmapService | None" = None,
    user_prefs: dict | None = None,
) -> list[POICandidate]:
    """Query POIs by city + taste_tags, score-rank, enforce 40% Tier A floor, handle Group A/B.

    When amap_service is provided, dynamically expands the POI pool by searching
    Amap for POIs matching intent.interests. Merges and deduplicates by amap_id.
    User preferences (taste_tags, budget) influence scoring.
    """

    include_highlight = group != "B"

    # Merge user prefs into scoring interests
    scoring_interests = list(intent.interests)
    if user_prefs and user_prefs.get("taste_tags"):
        scoring_interests.extend(user_prefs["taste_tags"])

    # Tier A: all for the city
    tier_a_query = select(POI).where(POI.city == intent.city, POI.tier == 1)
    tier_a_result = await db_session.execute(tier_a_query)
    tier_a_rows = list(tier_a_result.scalars().all())

    # Tier B + C: match any of intent.interests via LIKE on JSON text
    conditions = []
    for tag in intent.interests:
        conditions.append(POI.taste_tags.like(f'%"{tag}"%'))

    tier_bc_query = (
        select(POI)
        .where(POI.city == intent.city, POI.tier.in_([2, 3]))
        .where(or_(*conditions) if conditions else True)
        .order_by(POI.rating.desc().nullslast())
        .limit(120)
    )
    tier_bc_result = await db_session.execute(tier_bc_query)
    tier_bc_rows = list(tier_bc_result.scalars().all())

    # Convert and score all candidates
    tier_a_candidates = [_poi_to_candidate(p, include_highlight=include_highlight) for p in tier_a_rows]
    tier_bc_candidates = [_poi_to_candidate(p, include_highlight=True) for p in tier_bc_rows]

    # --- Dynamic Amap expansion ---
    amap_pois: list[dict] = []
    if amap_service is not None:
        try:
            search_keywords = intent.interests[:5]
            if search_keywords:
                amap_results = await amap_service.batch_search_pois(
                    city=intent.city,
                    keyword_list=search_keywords,
                    limit_per_keyword=10,
                )
                # Track existing amap_ids from curated DB for dedup
                existing_amap_ids = {p.amap_id for p in tier_a_rows + tier_bc_rows if p.amap_id}
                for poi_data in amap_results:
                    if poi_data["amap_id"] not in existing_amap_ids:
                        amap_pois.append(poi_data)
                        existing_amap_ids.add(poi_data["amap_id"])
        except Exception as e:
            logger.warning(f"Amap expansion failed, continuing with DB-only: {e}")

    # Convert Amap POIs to candidates and merge into tier_bc pool
    amap_candidates = [_amap_to_candidate(p) for p in amap_pois]
    for c in amap_candidates:
        c.__score = _score_poi(c.taste_tags, c.tier, c.rating, scoring_interests)
    tier_bc_candidates.extend(amap_candidates)

    # Score-rank Tier B/C candidates (including Amap additions)
    for c in tier_bc_candidates:
        c.__score = _score_poi(c.taste_tags, c.tier, c.rating, scoring_interests)
    tier_bc_candidates.sort(key=lambda x: x.__score, reverse=True)

    # Build final list with balanced tier distribution
    # Tier A floor: >= 40% of total must be Tier A
    # Target total: 25-30 candidates
    target_total = 28
    tier_a_count = len(tier_a_candidates)

    if tier_a_count >= target_total * 0.4:
        max_bc = target_total - tier_a_count
    else:
        max_bc = int(tier_a_count / 0.4 * 0.6) if tier_a_count > 0 else target_total
        max_bc = min(max_bc, target_total - tier_a_count)

    tier_bc_final = tier_bc_candidates[:max_bc]

    # Ensure Tier C <= 30% of total
    total = tier_a_count + len(tier_bc_final)
    if total > 0:
        tier_c_final = [c for c in tier_bc_final if c.tier == 3]
        max_tier_c = int(total * 0.3)
        if len(tier_c_final) > max_tier_c:
            excess = len(tier_c_final) - max_tier_c
            tier_bc_final = [c for c in tier_bc_final if c.tier != 3][: len(tier_bc_final) - excess]

    result = tier_a_candidates + tier_bc_final

    logger.info(
        f"Stage 2: {len(result)} candidates ({tier_a_count} Tier A, {len(tier_bc_final)} Tier B/C"
        f"{' + ' + str(len(amap_candidates)) + ' from Amap' if amap_candidates else ''})"
    )
    return result
