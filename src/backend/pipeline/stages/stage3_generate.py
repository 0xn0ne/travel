"""Stage 3: Generate itinerary using SOUL prompt + POI candidates."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from backend.llm.output_parsers import parse_itinerary_output
from backend.models.pydantic import IntentOutput, Itinerary, POICandidate

if TYPE_CHECKING:
    from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)


def _load_prompt(filename: str) -> str:
    path = Path(__file__).parent.parent.parent.parent.parent / "data" / "prompts" / filename
    return path.read_text(encoding="utf-8")


def _format_pois_for_prompt(
    tier_a: list[POICandidate],
    tier_b: list[POICandidate],
) -> tuple[str, str]:
    """Format POI candidates into the user template sections."""

    def format_single(poi: POICandidate) -> str:
        tier_label = {1: "Tier A", 2: "Tier B", 3: "Tier C"}.get(poi.tier, "Tier ?")
        highlight = f"推荐理由：{poi.highlight_note}\n" if poi.highlight_note else ""
        features = " | ".join(poi.taste_tags)
        permanent = " | ".join(poi.permanent_features) if poi.permanent_features else ""
        return (
            f"【{poi.name}】\n"
            f"  ID: {poi.id}\n"
            f"  等级：{tier_label}\n"
            f"  分类：{poi.category} | 标签：{features}\n"
            f"  {highlight}" + (f"  特色：{permanent}\n" if permanent else "")
        )

    tier_a_str = "\n\n".join(format_single(p) for p in tier_a)
    tier_b_str = "\n\n".join(format_single(p) for p in tier_b[:50])

    return tier_a_str, tier_b_str


def _build_user_preferences(intent: IntentOutput) -> str:
    """Build natural language summary of user preferences for the template."""
    parts = [f"城市：{intent.city}", f"{intent.days}天"]
    if intent.pace:
        pace_map = {"悠闲": "节奏从容", "适中": "节奏适中", "紧凑": "节奏紧凑"}
        parts.append(pace_map.get(intent.pace, f"节奏{intent.pace}"))
    if intent.interests:
        parts.append(f"喜欢{'、'.join(intent.interests)}")
    if intent.budget_level:
        parts.append(f"预算{intent.budget_level}")
    if intent.special_requests:
        parts.append(intent.special_requests)
    return "，".join(parts)


_MAX_POIS_PER_DAY = 4


def _enforce_max_pois_per_day(itinerary: Itinerary) -> Itinerary:
    """Post-processing check: truncate days with >4 POIs, log warning."""
    truncated = False
    for day in itinerary.days:
        if len(day.pois) > _MAX_POIS_PER_DAY:
            logger.warning(f"Day {day.day_number} has {len(day.pois)} POIs (>{_MAX_POIS_PER_DAY}), truncating.")
            day.pois = day.pois[:_MAX_POIS_PER_DAY]
            truncated = True
    if truncated:
        logger.warning("Itinerary had days exceeding max POI limit — truncated.")
    return itinerary


async def generate_itinerary(
    llm_client: "LLMClient",
    intent: IntentOutput,
    poi_candidates: list[POICandidate],
    user_input: str,
    group: str | None = None,
    enrichment_context: str = "",
) -> tuple[str, Itinerary]:
    """Generate itinerary using SOUL prompt + POI candidates. Returns (raw_response, itinerary)."""

    system_prompt = _load_prompt("soul_system.md")
    user_template = _load_prompt("soul_user_template.md")

    tier_a = [p for p in poi_candidates if p.tier == 1]
    tier_b = [p for p in poi_candidates if p.tier == 2]
    tier_a_str, tier_b_str = _format_pois_for_prompt(tier_a, tier_b)

    user_preferences = _build_user_preferences(intent)

    user_message = user_template.format(
        USER_PREFERENCES=user_preferences,
        TIER_A_POIS=tier_a_str,
        TIER_B_MATCHING_POIS=tier_b_str,
        DAYS=intent.days,
        CITY=intent.city,
    )

    if enrichment_context:
        user_message += f"\n\n## 智能推荐补充信息\n{enrichment_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    raw = await llm_client.generate_json(
        messages,
        temperature=0.7,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    itinerary = await parse_itinerary_output(raw)
    itinerary = _enforce_max_pois_per_day(itinerary)
    return raw, itinerary
