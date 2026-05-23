from __future__ import annotations
from socialseed_tasker.workers.app import create_celery
import os
import sys

def main():
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
