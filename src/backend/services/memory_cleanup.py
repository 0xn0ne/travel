"""Memory cleanup service — quarterly decay and trip_context expiry (MEM-01).

Per D-12, D-13, D-14:
- trip_context memories expire after 7 days
- Quarterly cleanup: remove access_count <= 3 from prior quarters
- Then remove bottom 20% by access_count from prior quarters
- Current quarter memories are exempt
"""

from datetime import datetime, timezone

from sqlalchemy import delete, func, select

from backend.models.database import AgentMemory


def _quarter_start(now: datetime) -> datetime:
    """Return the start datetime of the quarter containing `now`."""
    q_month = ((now.month - 1) // 3) * 3 + 1
    return datetime(now.year, q_month, 1, tzinfo=timezone.utc)


async def cleanup_memories(db_session) -> dict:
    """Run memory cleanup and return stats.

    Args:
        db_session: AsyncSession

    Returns:
        dict with keys: removed_expired_context, removed_low_access, removed_bottom_pct
    """
    now = datetime.now(timezone.utc)
    quarter_start = _quarter_start(now)

    # Step 1: Expire trip_context memories older than 7 days
    from datetime import timedelta

    expiry_cutoff = now - timedelta(days=7)
    result = await db_session.execute(
        delete(AgentMemory)
        .where(AgentMemory.category == "trip_context")
        .where(AgentMemory.created_at < expiry_cutoff)
    )
    removed_expired_context = result.rowcount

    # Step 2: Remove pre-quarter memories with access_count <= 3
    result = await db_session.execute(
        delete(AgentMemory)
        .where(AgentMemory.created_at < quarter_start)
        .where(AgentMemory.access_count <= 3)
    )
    removed_low_access = result.rowcount

    # Step 3: Remove bottom 20% of remaining pre-quarter memories by access_count
    count_result = await db_session.execute(
        select(func.count()).select_from(AgentMemory).where(
            AgentMemory.created_at < quarter_start
        )
    )
    remaining = count_result.scalar() or 0

    removed_bottom_pct = 0
    if remaining > 0:
        cutoff_count = max(1, remaining // 5)

        sub = (
            select(AgentMemory.id)
            .where(AgentMemory.created_at < quarter_start)
            .order_by(AgentMemory.access_count.asc())
            .limit(cutoff_count)
        )
        result = await db_session.execute(
            delete(AgentMemory).where(AgentMemory.id.in_(sub))
        )
        removed_bottom_pct = result.rowcount

    await db_session.flush()

    return {
        "removed_expired_context": removed_expired_context,
        "removed_low_access": removed_low_access,
        "removed_bottom_pct": removed_bottom_pct,
    }


async def run_cleanup() -> dict:
    """CLI entry point: create a session and run cleanup."""
    from backend.db.init_db import AsyncSessionFactory, _get_engine

    _get_engine()
    async with AsyncSessionFactory() as session:
        async with session.begin():
            stats = await cleanup_memories(session)
    return stats


if __name__ == "__main__":
    import asyncio

    stats = asyncio.run(run_cleanup())
    print(f"Cleanup complete: {stats}")
