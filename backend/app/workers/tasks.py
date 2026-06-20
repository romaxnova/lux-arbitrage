import asyncio

from app.database import AsyncSessionLocal
from app.services.pipeline import run_full_pipeline, run_matching, run_scoring
from app.workers.celery_app import celery_app


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.run_scrape_pipeline")
def run_scrape_pipeline():
    async def _run():
        async with AsyncSessionLocal() as db:
            stats = await run_full_pipeline(db)
            await db.commit()
            return stats

    return run_async(_run())


@celery_app.task(name="app.workers.tasks.run_matching_batch")
def run_matching_batch():
    async def _run():
        async with AsyncSessionLocal() as db:
            count = await run_matching(db)
            await db.commit()
            return count

    return run_async(_run())


@celery_app.task(name="app.workers.tasks.run_scoring_batch")
def run_scoring_batch():
    async def _run():
        async with AsyncSessionLocal() as db:
            count = await run_scoring(db)
            await db.commit()
            return count

    return run_async(_run())
