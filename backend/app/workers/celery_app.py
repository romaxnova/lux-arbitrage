from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "lux_arbitrage",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

interval = max(1, min(settings.scraper_interval_minutes, 59))
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.run_scrape_pipeline": {"queue": "default"},
        "app.workers.tasks.run_matching_batch": {"queue": "default"},
        "app.workers.tasks.run_scoring_batch": {"queue": "default"},
    },
    beat_schedule={
        "scrape-periodic": {
            "task": "app.workers.tasks.run_scrape_pipeline",
            "schedule": crontab(minute=f"*/{interval}") if interval < 60 else crontab(minute=0),
        },
    },
)
