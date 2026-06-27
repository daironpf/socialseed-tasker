from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from ariadne import MutationType, QueryType, SubscriptionType

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.exceptions import PermissionError
from socialseed_tasker.events.serializers import EventDTO

query = QueryType()
mutation = MutationType()
subscription = SubscriptionType()


@query.field("issue")
def resolve_issue(_, info, id: str):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    return container.issue_repo.get(id)


@query.field("issues")
def resolve_issues(_, info):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    return container.issue_repo.list()


@query.field("impact")
def resolve_impact(_, info, issueId: str, maxDepth: int = 5):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:impact"):
        raise PermissionError("forbidden")
    return container.application.calculate_impact(issueId, maxDepth, graph_repo=container.graph_repo, user_id=user_id)


@query.field("agentContext")
def resolve_agent_context(_, info, issueId: str, maxDepth: int = 3):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    ctx = container.application.generate_agent_context(
        issueId, maxDepth,
        graph_repo=container.graph_repo,
        issue_repo=container.issue_repo,
        parser=container.parser,
        user_id=user_id,
    )
    return {"issueId": issueId, "context": ctx}


@mutation.field("createIssue")
def resolve_create_issue(_, info, id: str, title: str, description: str = "", status: str = "open", metadata: Dict[str, Any] = None):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "create:issue"):
        raise PermissionError("forbidden")
    dto = IssueDTO(id=id, title=title, description=description or "", status=status, metadata=metadata or {})
    container.application.create_issue(issue=dto)
    evt = EventDTO(
        id=id,
        type="issue.created",
        source="graphql",
        payload={"id": id, "title": title},
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    container.events_bus.publish(evt)
    return container.issue_repo.get(id)


@mutation.field("addDependency")
def resolve_add_dependency(_, info, **args):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "add:dependency"):
        raise PermissionError("forbidden")
    edge = DependencyEdge(
        from_issue_id=args["from"],
        to_issue_id=args["to"],
        relation=args.get("relation", "DEPENDS_ON"),
        metadata={},
    )
    container.application.add_dependency(edge=edge)
    return {"from": args["from"], "to": args["to"], "relation": args.get("relation", "DEPENDS_ON")}


@mutation.field("triggerEvent")
def resolve_trigger_event(_, info, type: str, payload: Dict[str, Any] = None):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "admin"):
        raise PermissionError("forbidden")
    evt = EventDTO(
        id=f"{type}-{int(__import__('time').time() * 1000)}",
        type=type,
        source="graphql",
        payload=payload or {},
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    container.events_bus.publish(evt)
    return True


@subscription.source("issueEvents")
def source_issue_events(obj, info, issueId=None):
    container = info.context["container"]
    queue = []

    def handler(event):
        try:
            if issueId is None or (event.payload.get("id") == issueId):
                queue.append(event.to_json())
        except Exception:
            pass

    container.events_bus.subscribe("*", handler)
    try:
        while True:
            if queue:
                yield queue.pop(0)
            else:
                __import__("time").sleep(0.1)
    finally:
        container.events_bus.unsubscribe("*", handler)


@subscription.field("issueEvents")
def issue_events_resolver(event_json, info, issueId=None):
    return __import__("json").loads(event_json)


@subscription.source("webhookEvents")
def source_webhook_events(obj, info):
    container = info.context["container"]
    queue = []

    def handler(event):
        try:
            if event.type.startswith("webhook."):
                queue.append(event.to_json())
        except Exception:
            pass

    container.events_bus.subscribe("*", handler)
    try:
        while True:
            if queue:
                yield queue.pop(0)
            else:
                __import__("time").sleep(0.1)
    finally:
        container.events_bus.unsubscribe("*", handler)


@subscription.field("webhookEvents")
def webhook_events_resolver(event_json, info):
    return __import__("json").loads(event_json)
