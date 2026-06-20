"""Seed database with live scrape data."""

import asyncio

from app.database import AsyncSessionLocal, init_db
from app.services.pipeline import run_full_pipeline


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        stats = await run_full_pipeline(db)
        await db.commit()
        print(f"Seed complete: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
