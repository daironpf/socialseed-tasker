Background Workers and Task Queue

Overview
- Uses Celery with Redis broker and result backend.
- Tasks are defined in socialseed_tasker/workers/tasks.py and include:
  - parse_and_index_files(file_paths)
  - batch_embed_and_store(docs, store_key)
  - run_graph_analysis(issue_id, depth)

Configuration environment variables
- TASKER_CELERY_BROKER_URL default redis://localhost:6379/0
- TASKER_CELERY_RESULT_BACKEND default redis://localhost:6379/1
- TASKER_CELERY_TASK_TIME_LIMIT default 300
- TASKER_CELERY_WORKER_CONCURRENCY default 1
- TASKER_CELERY_QUEUES default default

CLI integration
- enqueue-task --task <name> --payload '<json>'
- task-status --task-id <id>

Local development
- Start services:
  docker compose -f docker-compose.celery.yml up -d
- Start worker (if not using compose):
  python -m socialseed_tasker.workers.worker

Operational notes
- Tasks use JSON serialization for portability.
- Keep tasks idempotent where possible.
- Monitor Redis and worker logs for failures.
