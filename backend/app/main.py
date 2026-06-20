from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.database import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _auto_seed_if_empty()
    yield
    await engine.dispose()


async def _auto_seed_if_empty() -> None:
    """Run demo seed on first startup when the database has no opportunities."""
    import logging

    from sqlalchemy import func, select

    from app.database import AsyncSessionLocal
    from app.models import Opportunity

    logger = logging.getLogger(__name__)
    try:
        async with AsyncSessionLocal() as db:
            count = (await db.execute(select(func.count()).select_from(Opportunity))).scalar() or 0
            if count == 0:
                logger.info("Database empty — running demo seed...")
                from app.scripts.demo_seed import run_demo_seed

                stats = await run_demo_seed(db)
                await db.commit()
                logger.info("Demo seed complete: %s", stats)
    except Exception as exc:
        logging.getLogger(__name__).warning("Auto-seed failed (non-fatal): %s", exc)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Lux Arbitrage API",
        description="Arbitrage intelligence platform for luxury fashion resale",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


@app.get("/health")
async def health():
    return {"status": "ok", "env": get_settings().app_env}
