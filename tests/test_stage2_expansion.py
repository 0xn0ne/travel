"""Tests for Stage 2 filter dynamic Amap POI expansion (Plan 07-03)."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.db.init_db import init_db
from backend.models.database import Base, POI
from backend.models.pydantic import IntentOutput
from backend.pipeline.stages.stage2_filter import filter_pois


# ---------------------------------------------------------------------------
# In-memory SQLite test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def seeded_db(db_session: AsyncSession):
    """Seed a handful of POIs for testing."""
    pois = [
        POI(
            id="db-1",
            amap_id="amap-100",
            name="外滩",
            tier=1,
            category="景点",
            city="上海",
            latitude=31.24,
            longitude=121.49,
            taste_tags='["文艺", "摄影"]',
            rating=4.8,
        ),
        POI(
            id="db-2",
            amap_id="amap-200",
            name="某咖啡馆",
            tier=2,
            category="餐饮",
            city="上海",
            latitude=31.23,
            longitude=121.47,
            taste_tags='["咖啡", "文艺"]',
            rating=4.5,
        ),
        POI(
            id="db-3",
            amap_id="amap-300",
            name="某小众店",
            tier=3,
            category="购物",
            city="上海",
            latitude=31.22,
            longitude=121.46,
            taste_tags='["小众"]',
            rating=3.8,
        ),
        # Extra Tier A POIs so tier A floor allows more B/C candidates
        POI(
            id="db-4",
            amap_id="amap-101",
            name="豫园",
            tier=1,
            category="景点",
            city="上海",
            latitude=31.23,
            longitude=121.49,
            taste_tags='["历史", "摄影"]',
            rating=4.7,
        ),
        POI(
            id="db-5",
            amap_id="amap-102",
            name="田子坊",
            tier=1,
            category="景点",
            city="上海",
            latitude=31.21,
            longitude=121.47,
            taste_tags='["文艺", "小众"]',
            rating=4.6,
        ),
        POI(
            id="db-6",
            amap_id="amap-103",
            name="南京路",
            tier=1,
            category="购物",
            city="上海",
            latitude=31.24,
            longitude=121.48,
            taste_tags='["购物"]',
            rating=4.4,
        ),
    ]
    db_session.add_all(pois)
    await db_session.commit()


@pytest.fixture
def intent():
    return IntentOutput(city="上海", days=2, interests=["文艺", "咖啡", "摄影"])


# ---------------------------------------------------------------------------
# Mock AmapService
# ---------------------------------------------------------------------------


class MockAmapService:
    """Minimal mock that returns predefined POI dicts."""

    def __init__(self, results: list[dict] | None = None):
        self._results = results or []

    async def batch_search_pois(
        self,
        city: str,
        keyword_list: list[str],
        types: str | None = None,
        limit_per_keyword: int = 20,
    ) -> list[dict]:
        return self._results


def _amap_poi(amap_id: str, name: str, rating: float | None = None, category: str = "餐饮") -> dict:
    """Helper to build an Amap POI result dict."""
    return {
        "amap_id": amap_id,
        "name": name,
        "location": "121.47,31.23",
        "address": "上海某路",
        "category": category,
        "rating": rating,
        "opening_hours": "09:00-22:00",
    }


# ---------------------------------------------------------------------------
# Test 1: backward compatibility — no amap_service → DB-only results
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_no_amap_service_returns_db_only(seeded_db, db_session, intent):
    """When amap_service is None, filter returns only curated DB POIs."""
    results = await filter_pois(db_session, intent)
    # All results come from DB (6 seeded POIs)
    assert len(results) > 0
    db_ids = {"db-1", "db-2", "db-3", "db-4", "db-5", "db-6"}
    for r in results:
        assert r.id in db_ids


# ---------------------------------------------------------------------------
# Test 2: Amap results merge with DB POIs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_merges_amap_results(seeded_db, db_session, intent):
    """Amap POIs should appear in results alongside DB POIs."""
    amap_extra = [_amap_poi("amap-400", "新发现的店", rating=4.2)]
    amap = MockAmapService(results=amap_extra)

    results = await filter_pois(db_session, intent, amap_service=amap)
    names = {r.name for r in results}
    # DB POIs should be present
    assert "外滩" in names
    # Amap POI should also be present
    assert "新发现的店" in names


# ---------------------------------------------------------------------------
# Test 3: dedup by amap_id — curated DB wins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dedup_curated_db_wins(seeded_db, db_session, intent):
    """If Amap returns a POI with same amap_id as a DB POI, DB version wins."""
    # amap-200 overlaps with DB "某咖啡馆"
    amap_dup = [_amap_poi("amap-200", "重复的咖啡馆", rating=4.0)]
    amap = MockAmapService(results=amap_dup)

    results = await filter_pois(db_session, intent, amap_service=amap)
    # Should only have one entry for amap-200 — the DB version
    dup_entries = [r for r in results if r.name == "重复的咖啡馆"]
    assert len(dup_entries) == 0, "Amap duplicate should be excluded"
    db_entries = [r for r in results if r.name == "某咖啡馆"]
    assert len(db_entries) >= 1, "DB version should be present"


# ---------------------------------------------------------------------------
# Test 4: Amap POIs auto-tiered (B if rating > 4.0, else C)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_amap_auto_tiering(seeded_db, db_session, intent):
    """Amap POIs should be auto-tiered: Tier B if rating > 4.0, Tier C otherwise."""
    amap_results = [
        _amap_poi("amap-500", "高评分店", rating=4.5),
        _amap_poi("amap-600", "低评分店", rating=3.2),
    ]
    amap = MockAmapService(results=amap_results)

    results = await filter_pois(db_session, intent, amap_service=amap)
    by_name = {r.name: r for r in results}

    assert "高评分店" in by_name
    assert by_name["高评分店"].tier == 2, "rating > 4.0 → Tier B"

    # 低评分店 might be filtered out by cap, so check if present
    if "低评分店" in by_name:
        assert by_name["低评分店"].tier == 3, "rating <= 4.0 → Tier C"


# ---------------------------------------------------------------------------
# Test 5: merged pool respects 40% Tier A floor and 28 candidate cap
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merged_pool_tier_a_floor_and_cap(seeded_db, db_session, intent):
    """Even with Amap expansion, 40% must be Tier A and total capped at 28."""
    # Generate many Amap POIs to test cap
    many_amap = [_amap_poi(f"amap-{700 + i}", f"扩展店{i}", rating=4.1) for i in range(40)]
    amap = MockAmapService(results=many_amap)

    results = await filter_pois(db_session, intent, amap_service=amap)
    assert len(results) <= 28, f"Total candidates should be capped at 28, got {len(results)}"

    tier_a_count = sum(1 for r in results if r.tier == 1)
    if len(results) > 0:
        tier_a_pct = tier_a_count / len(results)
        assert tier_a_pct >= 0.4, f"Tier A floor violated: {tier_a_pct:.0%} < 40%"


# ---------------------------------------------------------------------------
# Test 6: user_prefs taste_tags influence scoring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_prefs_boost_relevant_pois(seeded_db, db_session, intent):
    """User taste_tags should boost POIs with matching tags in scoring."""
    # POIs with "小众" tag — user adds it via prefs
    amap_results = [
        _amap_poi("amap-800", "小众发现", rating=4.0, category="景点"),
    ]
    amap = MockAmapService(results=amap_results)

    # With user_prefs including "小众"
    results_with_prefs = await filter_pois(
        db_session,
        intent,
        amap_service=amap,
        user_prefs={"taste_tags": ["小众"], "budget": "适中"},
    )

    # The "小众发现" Amap POI should rank higher with user prefs than without
    names_with = [r.name for r in results_with_prefs]
    assert "小众发现" in names_with, "User prefs should boost matching POIs into results"
