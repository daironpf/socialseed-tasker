from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypeVar, cast

from ariadne import MutationType, QueryType, SubscriptionType

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.exceptions import PermissionError
from socialseed_tasker.events.serializers import EventDTO

query = QueryType()
mutation = MutationType()
subscription = SubscriptionType()

Resolver = TypeVar("Resolver", bound=Callable[..., Any])


def _field(registry: Any, name: str) -> Callable[[Resolver], Resolver]:
    return cast(Callable[[Resolver], Resolver], registry.field(name))


@_field(query, "issue")
def resolve_issue(_: Any, info: Any, id: str) -> Any:
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    return container.issue_repo.get(id)


@_field(query, "issues")
def resolve_issues(_: Any, info: Any) -> Any:
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    return container.issue_repo.list()


@_field(query, "impact")
def resolve_impact(_: Any, info: Any, issueId: str, maxDepth: int = 5) -> Any:  # noqa: N803  # nombre de argumento del esquema GraphQL
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:impact"):
        raise PermissionError("forbidden")
    return container.application.calculate_impact(issueId, maxDepth, graph_repo=container.graph_repo, user_id=user_id)


@_field(query, "agentContext")
def resolve_agent_context(_: Any, info: Any, issueId: str, maxDepth: int = 3) -> Any:  # noqa: N803  # nombre de argumento del esquema GraphQL
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


@_field(mutation, "createIssue")
def resolve_create_issue(
    _: Any,
    info: Any,
    id: str,
    title: str,
    description: str = "",
    status: str = "open",
    metadata: dict[str, Any] | None = None,
) -> Any:
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


@_field(mutation, "addDependency")
def resolve_add_dependency(_: Any, info: Any, **args: Any) -> Any:
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


@_field(mutation, "triggerEvent")
def resolve_trigger_event(
    _: Any, info: Any, type: str, payload: dict[str, Any] | None = None
) -> Any:
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


@_field(subscription, "issueEvents")
def source_issue_events(obj: Any, info: Any, issueId: Any = None) -> Any:  # noqa: N803  # nombre de argumento del esquema GraphQL
    container = info.context["container"]
    queue = []

    def handler(event: Any) -> Any:
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


@_field(subscription, "issueEvents")
def issue_events_resolver(event_json: Any, info: Any, issueId: Any = None) -> Any:  # noqa: N803  # nombre de argumento del esquema GraphQL
    return __import__("json").loads(event_json)


@_field(subscription, "webhookEvents")
def source_webhook_events(obj: Any, info: Any) -> Any:
    container = info.context["container"]
    queue = []

    def handler(event: Any) -> Any:
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


@_field(subscription, "webhookEvents")
def webhook_events_resolver(event_json: Any, info: Any) -> Any:
    return __import__("json").loads(event_json)
