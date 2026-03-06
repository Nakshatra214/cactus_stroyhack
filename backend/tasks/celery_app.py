"""
Celery application configuration.
"""
from celery import Celery
from config import settings

celery_app = Celery(
    "storyhack",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)
