from __future__ import annotations
import os
from celery import Celery

DEFAULT_BROKER = os.getenv("TASKER_CELERY_BROKER_URL", "redis://localhost:6379/0")
DEFAULT_BACKEND = os.getenv("TASKER_CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

def create_celery(app_name: str = "tasker") -> Celery:
    celery = Celery(app_name, broker=os.getenv("TASKER_CELERY_BROKER_URL", DEFAULT_BROKER),
                    backend=os.getenv("TASKER_CELERY_RESULT_BACKEND", DEFAULT_BACKEND))
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_time_limit=int(os.getenv("TASKER_CELERY_TASK_TIME_LIMIT", "300")),
        worker_prefetch_multiplier=int(os.getenv("TASKER_CELERY_PREFETCH_MULTIPLIER", "1")),
        task_acks_late=True,
    )
    return celery
