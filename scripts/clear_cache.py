"""Clear expired (or all) AmapCache entries."""

import asyncio
import argparse
import sys

sys.path.insert(0, "src/backend")

from backend.db.init_db import init_db, engine
from backend.models.database import AmapCache
from sqlalchemy import delete, select, func


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Delete all cache entries")
    args = parser.parse_args()

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        if args.all:
            result = await session.execute(delete(AmapCache))
            print(f"Deleted all {result.rowcount} cache entries")
        else:
            from datetime import datetime

            result = await session.execute(delete(AmapCache).where(AmapCache.expires_at < datetime.utcnow()))
            print(f"Deleted {result.rowcount} expired cache entries")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
