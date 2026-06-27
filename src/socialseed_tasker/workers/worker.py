from __future__ import annotations
from socialseed_tasker.workers.app import create_celery
from socialseed_tasker.observability.tracing import init_tracing, get_tracer
import os
import sys

def main():
    try:
        init_tracing(celery_app=None, service_name=os.getenv("TASKER_OTEL_SERVICE", "tasker-worker"))
    except Exception:
        pass
    worker_tracer = get_tracer("tasker.worker")
    celery = create_celery()
    concurrency = os.getenv("TASKER_CELERY_WORKER_CONCURRENCY", "1")
    queues = os.getenv("TASKER_CELERY_QUEUES", "default")
    argv = [
        "worker",
        "--loglevel=info",
        f"--concurrency={concurrency}",
        f"-Q{queues}",
    ]
    celery.worker_main(argv)

if __name__ == "__main__":
    main()
