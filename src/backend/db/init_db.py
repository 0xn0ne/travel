"""Database initialization and session management."""

import asyncio

from alembic.config import Config as AlembicConfig
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import get_settings
from backend.models.database import Base

_engine = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    global _engine, AsyncSessionFactory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            connect_args={"timeout": 30},
        )

        @event.listens_for(_engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

        AsyncSessionFactory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


async def init_db() -> None:
    """Ensure all tables exist via create_all(), then stamp Alembic to head.

    create_all() is idempotent — it skips existing tables. We stamp the
    Alembic version table so future migration-aware tools know the DB is current.
    We cannot use ``asyncio.to_thread(command.upgrade, ...)`` because alembic's
    env.py calls ``asyncio.run()`` internally, which deadlocks inside an
    already-running event loop.
    """
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Stamp alembic to head so the version table is up-to-date
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS alembic_version "
                "(version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            )
        )
        # Determine the latest revision from the migration scripts
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(AlembicConfig("alembic.ini"))
        head = script.get_current_head()
        if head:
            await conn.execute(text("DELETE FROM alembic_version"))
            await conn.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:ver)"),
                {"ver": head},
            )


async def get_async_session():
    """FastAPI dependency that yields an async database session."""
    _get_engine()
    async with AsyncSessionFactory() as session:
        yield session
