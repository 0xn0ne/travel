"""Database initialization and session management."""

import asyncio

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import get_settings

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
    """Run Alembic migrations to create/update database schema."""
    _get_engine()
    alembic_cfg = AlembicConfig("alembic.ini")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


async def get_async_session():
    """FastAPI dependency that yields an async database session."""
    _get_engine()
    async with AsyncSessionFactory() as session:
        yield session
