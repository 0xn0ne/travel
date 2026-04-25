"""Pydantic schemas for pipeline stages and API contracts.

These are the type contracts Plans 03-06 implement against.
PipelineEvent lives in pipeline/events.py (created in Plan 03), NOT here.
"""

from typing import Literal

from pydantic import BaseModel, Field

# --- Pipeline stage outputs ---


class IntentOutput(BaseModel):
    """Stage 1 output — extracted user travel intent.

    Fields per INTENT-02:
    - city: single city (multi-city rejected per INTENT-03)
    - days: 1-3 per requirements
    - budget_level: D3 cost level (经济/适中/宽裕)
    - pace: D1 play type (悠闲/适中/紧凑)
    - rating_level: D7 rating (一般/较好/极好)
    - interests: taste_tags from controlled vocabulary
    """

    city: str  # single city only (multi-city rejected per INTENT-03)
    days: int = Field(ge=1, le=3)  # 1-3 days per requirements
    budget_level: str = "适中"  # 经济/适中/宽裕 (D3 cost level)
    pace: str = "适中"  # 悠闲/适中/紧凑 (D1 play type)
    rating_level: str = "较好"  # D7 rating: 一般/较好/极好 (default "较好")
    interests: list[str] = []  # taste_tags from controlled vocabulary
    special_requests: str | None = None  # avoidance items, preferences
    time_constraints: str | None = None
    weather_considered: bool = False  # 近期待规划（7天内）且有天气数据时为true


class POICandidate(BaseModel):
    id: str
    name: str
    tier: int
    category: str
    taste_tags: list[str]
    highlight_note: str | None = None
    permanent_features: list[str] = []
    walk_time_minutes: int | None = None
    rating: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    district: str | None = None
    region_key: str | None = None
    cover_image_url: str | None = None
    is_free: bool | None = None
    ticket_url: str | None = None
    description: str | None = None
    suggested_route: str | None = None
    suggested_duration_minutes: int | None = None


class POIVisit(BaseModel):
    poi_id: str
    name: str
    time_slot: str  # "09:00-10:30"
    highlight_note: str | None = None
    vibe_description: str
    walk_to_next_minutes: int | None = None
    tier: int | None = None
    latitude: float | None = None  # POI coordinate from pois table
    longitude: float | None = None  # POI coordinate from pois table


class ItineraryDay(BaseModel):
    day_number: int
    theme: str
    pois: list[POIVisit]


class Itinerary(BaseModel):
    title: str
    summary: str
    days: list[ItineraryDay]
    total_walking_minutes: int = 0


class FlaggedSegment(BaseModel):
    from_poi: str
    to_poi: str
    walk_minutes: int
    is_acceptable: bool  # ≤15 min


class ValidationResult(BaseModel):
    is_valid: bool
    flagged_segments: list[FlaggedSegment]
    total_walking_minutes: int


# --- API request/response ---


class GenerateRequest(BaseModel):
    user_input: str
    scenario_id: str | None = None
    group: str | None = None  # for blind test: A, B, C


class GenerateResponse(BaseModel):
    itinerary_id: str
    itinerary: Itinerary


class CandidatePoiRequest(BaseModel):
    destinations: list[str]
    date_range: list[int] | None = None
    trip_days: int | None = Field(default=None, ge=1, le=7)
    styles: list[str] = []
    crowd_preference: str | None = None
    budget: str | None = None
    extra_info: str | None = None
    scenario_id: str | None = None
    group: str | None = None


class CandidatePoiResponse(BaseModel):
    city: str
    trip_days: int
    user_input: str
    candidates: list[POICandidate]


class GenerateFromPoisRequest(BaseModel):
    user_input: str
    selected_pois: list[POICandidate]
    city: str
    trip_days: int = Field(ge=1, le=7)
    scenario_id: str | None = None
    group: str | None = None


# --- Phase 3: Adjustment & Feedback ---


class ChangeItem(BaseModel):
    action: Literal["add", "replace", "delete"]
    day_number: int
    position: int
    old_poi: POIVisit | None = None
    new_poi: POIVisit | None = None


class AdjustmentPreview(BaseModel):
    changes: list[ChangeItem]
    updated_itinerary: Itinerary


class AdjustmentRequest(BaseModel):
    itinerary_id: str
    adjustment_text: str
    conversation_history: list[dict] = []


class FeedbackRequest(BaseModel):
    itinerary_id: str
    rating: Literal["准", "一般", "不准"]
    comment: str | None = None
