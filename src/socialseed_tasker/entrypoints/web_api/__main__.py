"""Main entry point for running the API directly with python -m."""

import os
from contextlib import suppress

import uvicorn

from socialseed_tasker.bootstrap.container import Container
from socialseed_tasker.entrypoints.web_api.app import create_app


def main() -> None:
    """Run the API server."""
    container = Container.from_env()
    repository = container.get_repository()
    app = create_app(repository)

    if os.environ.get("TASKER_DEMO_MODE", "").lower() in ("1", "true", "yes"):
        _seed_demo_data(repository)

    config = uvicorn.Config(
        app,
        host=container.config.api_host,
        port=container.config.api_port,
        reload=container.config.debug,
        log_level="info" if not container.config.debug else "debug",
    )
    server = uvicorn.Server(config)
    server.run()


def _seed_demo_data(repository) -> None:
    """Populate the database with demo data if not already present."""
    existing = repository.list_components(project="demo-platform")
    if existing:
        return

    from socialseed_tasker.core.task_management.actions import (
        add_dependency_action,
        create_issue_action,
    )
    from socialseed_tasker.core.task_management.entities import Component

    components_data = [
        {"name": "api-gateway", "description": "Central API gateway routing requests to microservices"},
        {"name": "user-service", "description": "User authentication, profiles, and permissions"},
        {"name": "order-service", "description": "Order processing, state machine, and lifecycle"},
        {"name": "notification-service", "description": "Email, SMS, and push notification delivery"},
    ]

    issues_data = [
        {
            "title": "Implement rate limiting on API gateway",
            "component": "api-gateway",
            "description": "Add token bucket rate limiting to prevent abuse.",
            "priority": "HIGH",
            "labels": ["security", "performance"],
        },
        {
            "title": "Add JWT token refresh endpoint",
            "component": "user-service",
            "description": "Create /auth/refresh endpoint to rotate access tokens.",
            "priority": "HIGH",
            "labels": ["auth", "security"],
        },
        {
            "title": "Implement user profile caching with Redis",
            "component": "user-service",
            "description": "Cache user profiles to reduce database load.",
            "priority": "MEDIUM",
            "labels": ["performance", "caching"],
        },
        {
            "title": "Add order state machine with saga pattern",
            "component": "order-service",
            "description": "Implement distributed transaction handling using saga pattern.",
            "priority": "CRITICAL",
            "labels": ["architecture", "distributed-systems"],
        },
        {
            "title": "Create order cancellation workflow",
            "component": "order-service",
            "description": "Handle order cancellation with refund triggers.",
            "priority": "HIGH",
            "labels": ["orders", "workflow"],
        },
        {
            "title": "Implement email notification templates",
            "component": "notification-service",
            "description": "Create HTML email templates for order events.",
            "priority": "MEDIUM",
            "labels": ["email", "templates"],
        },
        {
            "title": "Add SMS fallback for critical alerts",
            "component": "notification-service",
            "description": "Fall back to SMS when email delivery fails.",
            "priority": "LOW",
            "labels": ["sms", "reliability"],
        },
        {
            "title": "Implement health check aggregation endpoint",
            "component": "api-gateway",
            "description": "Aggregate health status from all downstream services.",
            "priority": "MEDIUM",
            "labels": ["monitoring", "health"],
        },
    ]

    dependencies = [
        ("Add order state machine with saga pattern", "Add JWT token refresh endpoint"),
        ("Create order cancellation workflow", "Add order state machine with saga pattern"),
        ("Implement email notification templates", "Create order cancellation workflow"),
        ("Add SMS fallback for critical alerts", "Implement email notification templates"),
        ("Implement health check aggregation endpoint", "Implement rate limiting on API gateway"),
        ("Implement user profile caching with Redis", "Add JWT token refresh endpoint"),
    ]

    comp_map = {}
    for cd in components_data:
        comp = Component(name=cd["name"], project="demo-platform", description=cd["description"])
        repository.create_component(comp)
        comp_map[cd["name"]] = str(comp.id)

    issue_map = {}
    for idata in issues_data:
        issue = create_issue_action(
            repository,
            title=idata["title"],
            component_id=comp_map[idata["component"]],
            description=idata["description"],
            priority=idata["priority"],
            labels=idata["labels"],
        )
        issue_map[idata["title"]] = str(issue.id)

    for source_title, target_title in dependencies:
        with suppress(Exception):
            add_dependency_action(repository, issue_map[source_title], issue_map[target_title])


if __name__ == "__main__":
    main()
