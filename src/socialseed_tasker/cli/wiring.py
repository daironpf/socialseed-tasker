"""Wiring helper — builds the default Container with concrete adapters."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from socialseed_tasker.config.runtime import RuntimeConfig
from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser
from socialseed_tasker.observability.exporter import start_exporter
from socialseed_tasker.observability.logging import get_logger
from socialseed_tasker.auth.auth import load_auth_provider
from socialseed_tasker.auth.rbac import RBAC
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.redis_storage import RedisStorage
from socialseed_tasker.events.webhooks import WebhookManager
from socialseed_tasker.events.bus import EventBus
from socialseed_tasker.events.delivery import DeliveryWorker
from socialseed_tasker.auth.oauth import SessionStore
from socialseed_tasker.infrastructure.memory_rate_limiter import MemoryRateLimiter
from socialseed_tasker.tenancy.store import TenantStore
from socialseed_tasker.infrastructure.tenant_storage import NamespacedStorage
try:
    from socialseed_tasker.infrastructure.redis_rate_limiter import RedisRateLimiter
    _REDIS_RATE_AVAILABLE = True
except Exception:
    _REDIS_RATE_AVAILABLE = False

import socialseed_tasker.application as application_module


@dataclass
class Container:
    """Wiring container holding all adapter and repository instances."""

    graph: object
    parser: object
    issue_repo: object
    graph_repo: object
    embedding: object | None
    storage: object | None
    logger: object
    application: object
    auth: object
    rbac: object
    events: object
    events_bus: object
    delivery_worker: object
    session_store: object
    rate_limiter: object
    tenant_store: object
    tenant_scoped_storage: object
    tenancy_token_map: object
    runtime_config: object
    privacy_handlers: object
    feature_store: object
    ml_runner: object
    ml_batch_worker: object
    schema_registry: object


def build_default_container() -> Container:
    """Construct and return a default Container wired to Neo4j + TreeSitter."""
    logger = get_logger("tasker")
    graph = Neo4jGraphAdapter()
    parser = TreeSitterParser()
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)
    auth = load_auth_provider()
    rbac = RBAC()
    users_env = os.getenv("TASKER_AUTH_USERS")
    if users_env:
        try:
            users = json.loads(users_env)
            for uid, info in users.items():
                perms = info.get("permissions", [])
                for p in perms:
                    rbac.grant(uid, p)
        except Exception:
            pass
    redis_url = os.getenv("TASKER_REDIS_URL")
    if redis_url:
        try:
            storage = RedisStorage(url=redis_url)
        except Exception:
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
    events = WebhookManager(storage=storage)
    events_bus = EventBus()
    delivery_worker = DeliveryWorker(storage=storage)
    session_store = SessionStore(storage=storage)
    redis_url = os.getenv("TASKER_REDIS_URL")
    if redis_url and _REDIS_RATE_AVAILABLE:
        try:
            rate_limiter = RedisRateLimiter(redis_url, rate_per_min=int(os.getenv("TASKER_RATE_USER_PER_MIN", "120")), burst=int(os.getenv("TASKER_RATE_BURST", "20")))
        except Exception:
            rate_limiter = MemoryRateLimiter(rate_per_min=int(os.getenv("TASKER_RATE_USER_PER_MIN", "120")), burst=int(os.getenv("TASKER_RATE_BURST", "20")))
    else:
        rate_limiter = MemoryRateLimiter(rate_per_min=int(os.getenv("TASKER_RATE_USER_PER_MIN", "120")), burst=int(os.getenv("TASKER_RATE_BURST", "20")))
    if os.getenv("TASKER_INTEGRATION") == "1":
        delivery_worker.start()
    if os.getenv("TASKER_METRICS_ENABLED") == "1":
        start_exporter()

    try:
        from socialseed_tasker.observability.tracing import init_tracing
        init_tracing(service_name=os.getenv("TASKER_OTEL_SERVICE", "tasker"))
    except Exception:
        pass

    runtime_config = RuntimeConfig(storage=storage, poll_interval=int(os.getenv("TASKER_CONFIG_POLL_SECONDS", "5")))
    tenant_store = TenantStore(storage)
    tenant_scoped_storage = lambda tenant_id: NamespacedStorage(storage, tenant_id=tenant_id)
    tenancy_token_map = {}

    from socialseed_tasker.privacy import handlers as privacy_handlers_module
    privacy_handlers = privacy_handlers_module

    from socialseed_tasker.ml.feature_store import FeatureStore
    from socialseed_tasker.ml.runner import ModelRunner
    from socialseed_tasker.ml.batch_worker import BatchWorker
    feature_store = FeatureStore(storage)
    ml_runner = ModelRunner(storage=storage, feature_store=feature_store)
    ml_batch_worker = BatchWorker(storage=storage, runner=ml_runner)

    from socialseed_tasker.data_catalog.registry import SchemaRegistry
    schema_registry = SchemaRegistry(storage)
    return Container(
        graph=graph,
        parser=parser,
        issue_repo=issue_repo,
        graph_repo=graph_repo,
        embedding=None,
        storage=storage,
        logger=logger,
        application=application_module,
        auth=auth,
        rbac=rbac,
        events=events,
        events_bus=events_bus,
        delivery_worker=delivery_worker,
        session_store=session_store,
        rate_limiter=rate_limiter,
        runtime_config=runtime_config,
        tenant_store=tenant_store,
        tenant_scoped_storage=tenant_scoped_storage,
        tenancy_token_map=tenancy_token_map,
        privacy_handlers=privacy_handlers,
        feature_store=feature_store,
        ml_runner=ml_runner,
        ml_batch_worker=ml_batch_worker,
        schema_registry=schema_registry,
    )
