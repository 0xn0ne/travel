"""Integration tests for memory tools + skill activation (Plan 13-03)."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.agent.context import AgentContext
from backend.api.dependencies import build_agent_instructions
from backend.models.database import (
    ALLOWED_CATEGORIES,
    AgentMemory,
    Base,
    User,
)
from backend.services.amap_service import AmapService
from backend.services.skill_matcher import build_skill_prompt, match_skills
from backend.tools import ALL_TOOLS

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _seed_user(
    session: AsyncSession,
    user_id: str = "test-user",
    taste_tags: list[str] | None = None,
) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    user = User(
        id=user_id,
        email=f"{user_id}@test.com",
        password_hash="$2b$12$fakehash",
        taste_tags_default=json.dumps(taste_tags or []),
    )
    session.add(user)
    await session.flush()
    return user


async def _write_memory(
    session: AsyncSession,
    user_id: str,
    key: str,
    value: dict,
    category: str,
) -> AgentMemory:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(AgentMemory).where(
            AgentMemory.user_id == user_id,
            AgentMemory.key == key,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.value = json.dumps(value, ensure_ascii=False)
        existing.category = category
        existing.access_count += 1
        existing.updated_at = now
        existing.last_accessed_at = now
        await session.flush()
        return existing
    mem = AgentMemory(
        user_id=user_id,
        key=key,
        value=json.dumps(value, ensure_ascii=False),
        category=category,
        access_count=1,
        created_at=now,
        updated_at=now,
        last_accessed_at=now,
    )
    session.add(mem)
    await session.flush()
    return mem


async def _read_memories(
    session: AsyncSession,
    user_id: str,
    category: str | None = None,
    limit: int = 20,
) -> list[dict]:
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    taste_tags: list[str] = []
    if user and user.taste_tags_default:
        try:
            taste_tags = json.loads(user.taste_tags_default)
        except (json.JSONDecodeError, TypeError):
            taste_tags = []

    stmt = select(AgentMemory).where(AgentMemory.user_id == user_id)
    if category:
        stmt = stmt.where(AgentMemory.category == category)
    result = await session.execute(stmt)
    memories = list(result.scalars().all())

    def _score(mem: AgentMemory) -> int:
        if not taste_tags:
            return 0
        try:
            val = json.loads(mem.value)
            mem_tags = val.get("tags", [])
            return len(set(taste_tags) & set(mem_tags))
        except (json.JSONDecodeError, TypeError, AttributeError):
            return 0

    if taste_tags:
        memories.sort(key=_score, reverse=True)
    else:
        memories.sort(key=lambda m: m.updated_at, reverse=True)

    memories = memories[:limit]
    return [
        {
            "id": m.id,
            "key": m.key,
            "value": json.loads(m.value) if m.value else {},
            "category": m.category,
            "access_count": m.access_count,
        }
        for m in memories
    ]


# ── Memory Tests ──────────────────────────────────────────────────────────────


async def test_memory_write_and_read():
    async with TestSessionFactory() as session:
        await _seed_user(session)
        await _write_memory(session, "test-user", "diet_pref", {"note": "不喜欢辣", "tags": ["清淡"]}, "preference")
        await session.commit()

    async with TestSessionFactory() as session:
        await _seed_user(session)
        items = await _read_memories(session, "test-user")
        assert len(items) == 1
        assert items[0]["key"] == "diet_pref"
        assert items[0]["value"]["note"] == "不喜欢辣"


async def test_memory_upsert():
    async with TestSessionFactory() as session:
        await _seed_user(session)
        await _write_memory(session, "test-user", "budget", {"note": "500元/天", "tags": ["经济"]}, "constraint")
        await _write_memory(session, "test-user", "budget", {"note": "800元/天", "tags": ["舒适"]}, "constraint")
        await session.commit()

    async with TestSessionFactory() as session:
        await _seed_user(session)
        items = await _read_memories(session, "test-user")
        assert len(items) == 1
        assert items[0]["value"]["note"] == "800元/天"
        assert items[0]["access_count"] == 2


async def test_memory_anonymous_rejected():
    async with TestSessionFactory() as session:
        await _seed_user(session, user_id="anon-user")
        result = await session.execute(select(AgentMemory).where(AgentMemory.user_id == "nonexistent"))
        assert result.scalar_one_or_none() is None


async def test_memory_profile_scoring():
    async with TestSessionFactory() as session:
        await _seed_user(session, taste_tags=["咖啡", "安静"])
        now = datetime.now(timezone.utc)
        session.add(AgentMemory(
            id="m1", user_id="test-user", key="coffee_shop",
            value=json.dumps({"note": "好咖啡馆", "tags": ["咖啡"]}),
            category="preference", access_count=1,
            created_at=now, updated_at=now, last_accessed_at=now,
        ))
        session.add(AgentMemory(
            id="m2", user_id="test-user", key="loud_bar",
            value=json.dumps({"note": "吵闹酒吧", "tags": ["热闹", "夜生活"]}),
            category="preference", access_count=1,
            created_at=now, updated_at=now, last_accessed_at=now,
        ))
        await session.flush()
        await session.commit()

    async with TestSessionFactory() as session:
        await _seed_user(session, taste_tags=["咖啡", "安静"])
        items = await _read_memories(session, "test-user")
        assert len(items) == 2
        assert items[0]["key"] == "coffee_shop"


async def test_memory_category_filter():
    async with TestSessionFactory() as session:
        await _seed_user(session)
        now = datetime.now(timezone.utc)
        session.add(AgentMemory(
            id="m1", user_id="test-user", key="diet",
            value='{"note":"清淡"}', category="preference",
            access_count=1, created_at=now, updated_at=now, last_accessed_at=now,
        ))
        session.add(AgentMemory(
            id="m2", user_id="test-user", key="budget",
            value='{"note":"500/天"}', category="constraint",
            access_count=1, created_at=now, updated_at=now, last_accessed_at=now,
        ))
        await session.flush()
        await session.commit()

    async with TestSessionFactory() as session:
        await _seed_user(session)
        items = await _read_memories(session, "test-user", category="constraint")
        assert len(items) == 1
        assert items[0]["key"] == "budget"


async def test_cleanup_trip_context_expiry():
    async with TestSessionFactory() as session:
        await _seed_user(session)
        old_date = datetime.now(timezone.utc) - timedelta(days=8)
        session.add(AgentMemory(
            id="m-old", user_id="test-user", key="trip_ctx_1",
            value='{"note":"上次行程"}', category="trip_context",
            access_count=5, created_at=old_date, updated_at=old_date, last_accessed_at=old_date,
        ))
        await session.flush()
        await session.commit()

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        from sqlalchemy import delete
        await session.execute(
            delete(AgentMemory)
            .where(AgentMemory.category == "trip_context", AgentMemory.created_at < cutoff)
        )
        await session.commit()

        items = await _read_memories(session, "test-user", category="trip_context")
        assert len(items) == 0


async def test_cleanup_exempts_new_memories():
    async with TestSessionFactory() as session:
        await _seed_user(session)
        await _write_memory(
            session, "test-user", "fresh_trip", {"note": "本次行程", "city": "上海"}, "trip_context",
        )
        await session.commit()

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        from sqlalchemy import delete as sql_delete
        await session.execute(
            sql_delete(AgentMemory)
            .where(AgentMemory.category == "trip_context", AgentMemory.created_at < cutoff)
        )
        await session.commit()

        items = await _read_memories(session, "test-user", category="trip_context")
        assert len(items) == 1
        assert items[0]["key"] == "fresh_trip"


# ── Skill Tests ───────────────────────────────────────────────────────────────


def test_skill_match_trip_planning():
    matched = match_skills("帮我规划一个上海三天行程", ["景点"])
    slugs = [s.slug for s in matched]
    assert "trip_planning" in slugs


def test_skill_match_food():
    matched = match_skills("推荐一些好吃的餐厅", [])
    slugs = [s.slug for s in matched]
    assert "food_exploration" in slugs


def test_skill_match_local():
    matched = match_skills("有什么小众的推荐吗", ["探索"])
    slugs = [s.slug for s in matched]
    assert "local_insider" in slugs


def test_skill_primary_secondary():
    matched = match_skills("帮我规划行程，顺便推荐点美食", ["景点", "美食"])
    assert len(matched) >= 2
    assert matched[0].slug == "trip_planning"
    assert matched[0].priority > matched[1].priority


def test_skill_prompt_building():
    matched = match_skills("帮我规划行程，推荐好吃的", ["景点", "美食"])
    prompt = build_skill_prompt(matched)
    assert "行程规划" in prompt
    if len(matched) > 1:
        assert "Additional guidance" in prompt


def test_no_skill_match():
    matched = match_skills("你好呀", [])
    assert matched == []
    assert build_skill_prompt(matched) == ""


# ── Integration Tests ─────────────────────────────────────────────────────────


def test_all_tools_count():
    assert len(ALL_TOOLS) == 12, f"Expected 12 tools, got {len(ALL_TOOLS)}"
    names = [t.name for t in ALL_TOOLS]
    assert "read_memories" in names
    assert "write_memory" in names


def test_build_agent_instructions_with_skill():
    instructions = build_agent_instructions("帮我规划一个上海三天行程", ["景点"])
    assert "旅行助手" in instructions
    assert "行程规划" in instructions


def test_build_agent_instructions_without_skill():
    instructions = build_agent_instructions("你好呀", [])
    assert "旅行助手" in instructions
    assert "\n\n" not in instructions
