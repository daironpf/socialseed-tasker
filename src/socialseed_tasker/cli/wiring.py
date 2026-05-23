"""Wiring helper — builds the default Container with concrete adapters."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

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
    if os.getenv("TASKER_INTEGRATION") == "1":
        delivery_worker.start()
    if os.getenv("TASKER_METRICS_ENABLED") == "1":
        start_exporter()
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
    )
