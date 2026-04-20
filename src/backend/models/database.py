"""SQLAlchemy ORM models for all entities."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


ALLOWED_CATEGORIES = {"preference", "constraint", "feedback", "trip_context"}


class POI(Base):
    __tablename__ = "pois"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    amap_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(50), index=True)
    tier: Mapped[int] = mapped_column(Integer)  # 1=A, 2=B, 3=C
    category: Mapped[str] = mapped_column(String(50))
    latitude: Mapped[float]
    longitude: Mapped[float]
    address: Mapped[str | None] = mapped_column(String(500))
    taste_tags: Mapped[str] = mapped_column(Text)  # JSON array of tags
    highlight_note: Mapped[str | None] = mapped_column(Text)  # Tier A only
    permanent_features: Mapped[str | None] = mapped_column(Text)  # JSON, Tier A/B
    opening_hours: Mapped[str | None] = mapped_column(String(200))
    rating: Mapped[float | None]
    is_chain: Mapped[bool] = mapped_column(default=False)
    walk_time_minutes: Mapped[int | None] = mapped_column(Integer)  # from previous POI
    last_verified: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    user_input: Mapped[str] = mapped_column(Text)  # the prompt shown to all groups
    city: Mapped[str] = mapped_column(String(50))
    tags: Mapped[str] = mapped_column(Text)  # JSON array
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class ItineraryRow(Base):
    __tablename__ = "itineraries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )  # nullable for blind test (no auth)
    scenario_id: Mapped[str | None] = mapped_column(ForeignKey("scenarios.id"), nullable=True)
    group: Mapped[str | None] = mapped_column(String(1), nullable=True)  # A, B, or C
    city: Mapped[str] = mapped_column(String(50))
    raw_response: Mapped[str] = mapped_column(Text)  # LLM raw output
    parsed_itinerary: Mapped[str] = mapped_column(Text)  # JSON
    generation_config: Mapped[str] = mapped_column(Text)  # JSON: which pipeline params
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    participant_id: Mapped[str] = mapped_column(String(50))
    group: Mapped[str] = mapped_column(String(1))
    preferred_itinerary_id: Mapped[str] = mapped_column(String(36))
    preference_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class User(Base):
    """User account for authentication (AUTH-01, AUTH-02).

    Stores email + bcrypt password hash. JWT tokens are validated server-side
    but not stored (simplified JWT per D-01).
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # bcrypt hashed
    taste_tags_default: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    budget_default: Mapped[str] = mapped_column(String(20), default="适中")
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class AmapCache(Base):
    __tablename__ = "amap_cache"

    query_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    response_json: Mapped[str] = mapped_column(Text)
    api_method: Mapped[str] = mapped_column(String(50))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class FeedbackLog(Base):
    __tablename__ = "feedback_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    itinerary_id: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rating: Mapped[str] = mapped_column(String(10))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class AgentMemory(Base):
    """Per-user agent memory store (MEM-01, MEM-02).

    Structured key-value storage scoped to 4 categories.
    Upsert by (user_id, key). Profile-scored retrieval for read.
    """

    __tablename__ = "agent_memories"
    __table_args__ = (
        Index("ix_agent_memories_user_category", "user_id", "category"),
        Index("uq_agent_memories_user_key", "user_id", "key", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    key: Mapped[str] = mapped_column(String(200), index=True)
    value: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    access_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow)
    last_accessed_at: Mapped[datetime] = mapped_column(default=_utcnow)

    @validates("category")
    def _validate_category(self, key: str, value: str) -> str:
        if value not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Invalid category '{value}'. Must be one of: {ALLOWED_CATEGORIES}"
            )
        return value
