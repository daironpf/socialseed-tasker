from __future__ import annotations

from contextlib import suppress

import typer
from rich.panel import Panel

from socialseed_tasker.application.actions import (
    add_dependency_action,
    create_issue_action,
)
from socialseed_tasker.domain.entities import Component
from socialseed_tasker.cli.commands.shared import console, get_repository

seed_app = typer.Typer(help="Seed demo data for first-time users")

_SEED_COMPONENTS = [
    {"name": "api-gateway", "description": "Central API gateway routing requests to microservices"},
    {"name": "user-service", "description": "User authentication, profiles, and permissions"},
    {"name": "order-service", "description": "Order processing, state machine, and lifecycle"},
    {"name": "notification-service", "description": "Email, SMS, and push notification delivery"},
]

_SEED_ISSUES = [
    {
        "title": "Implement rate limiting on API gateway",
        "component": "api-gateway",
        "description": "Add token bucket rate limiting to prevent abuse. Configure per-endpoint limits.",
        "priority": "HIGH",
        "labels": ["security", "performance"],
    },
    {
        "title": "Add JWT token refresh endpoint",
        "component": "user-service",
        "description": "Create /auth/refresh endpoint to rotate access tokens without re-authentication.",
        "priority": "HIGH",
        "labels": ["auth", "security"],
    },
    {
        "title": "Implement user profile caching with Redis",
        "component": "user-service",
        "description": "Cache user profiles to reduce database load. Set TTL of 5 minutes.",
        "priority": "MEDIUM",
        "labels": ["performance", "caching"],
    },
    {
        "title": "Add order state machine with saga pattern",
        "component": "order-service",
        "description": "Implement distributed transaction handling using saga pattern for order creation.",
        "priority": "CRITICAL",
        "labels": ["architecture", "distributed-systems"],
    },
    {
        "title": "Create order cancellation workflow",
        "component": "order-service",
        "description": "Handle order cancellation with refund triggers and inventory restoration.",
        "priority": "HIGH",
        "labels": ["orders", "workflow"],
    },
    {
        "title": "Implement email notification templates",
        "component": "notification-service",
        "description": "Create HTML email templates for order confirmation, shipping, and delivery.",
        "priority": "MEDIUM",
        "labels": ["email", "templates"],
    },
    {
        "title": "Add SMS fallback for critical alerts",
        "component": "notification-service",
        "description": "When email delivery fails for critical notifications, fall back to SMS via Twilio.",
        "priority": "LOW",
        "labels": ["sms", "reliability"],
    },
    {
        "title": "Implement health check aggregation endpoint",
        "component": "api-gateway",
        "description": "Create /health endpoint that aggregates health status from all downstream services.",
        "priority": "MEDIUM",
        "labels": ["monitoring", "health"],
    },
]

_SEED_DEPENDENCIES = [
    # order-service saga depends on user-service auth
    ("Add order state machine with saga pattern", "Add JWT token refresh endpoint"),
    # order cancellation depends on saga
    ("Create order cancellation workflow", "Add order state machine with saga pattern"),
    # email templates needed for order confirmation
    ("Implement email notification templates", "Create order cancellation workflow"),
    # SMS fallback depends on email templates
    ("Add SMS fallback for critical alerts", "Implement email notification templates"),
    # health check depends on rate limiting
    ("Implement health check aggregation endpoint", "Implement rate limiting on API gateway"),
    # user profile caching depends on auth
    ("Implement user profile caching with Redis", "Add JWT token refresh endpoint"),
]


@seed_app.command("run")
def seed_run(
    force: bool = typer.Option(False, "--force", "-f", help="Delete existing demo data and re-seed"),
    project_name: str = typer.Option("demo-platform", "--project", "-p", help="Project name for seed data"),
) -> None:
    """Populate the database with demo components, issues, and dependencies.

    Creates a realistic microservices project with 4 components, 8 issues,
    and 6 dependency relationships to demonstrate the full dependency graph.
    """
    repo = get_repository()

    if force:
        existing = repo.list_components(project=project_name)
        for comp in existing:
            issues = repo.list_issues(component_id=str(comp.id))
            for issue in issues:
                with suppress(Exception):
                    repo.delete_issue(str(issue.id))
            with suppress(Exception):
                repo.delete_component(str(comp.id))
        console.print("[info]Cleared existing demo data.[/info]")

    existing_components = repo.list_components(project=project_name)
    if existing_components:
        console.print(f"[info]Demo data already exists for project '{project_name}'.[/info]")
        console.print("[info]Use [cyan]--force[/cyan] to re-seed.[/info]")
        return

    # Create components
    comp_map: dict[str, str] = {}
    for comp_data in _SEED_COMPONENTS:
        component = Component(name=comp_data["name"], project=project_name, description=comp_data["description"])
        repo.create_component(component)
        comp_map[comp_data["name"]] = str(component.id)
        console.print(f"[success]Component:[/success] {component.name}")

    # Create issues
    issue_map: dict[str, str] = {}
    for issue_data in _SEED_ISSUES:
        comp_id = comp_map[issue_data["component"]]
        issue, _ = create_issue_action(
            repo,
            title=issue_data["title"],
            component_id=comp_id,
            description=issue_data["description"],
            priority=issue_data["priority"],
            labels=issue_data["labels"],
        )
        issue_map[issue_data["title"]] = str(issue.id)
        console.print(f"  [dim]Issue:[/dim] {issue.title}")

    # Create dependencies
    for source_title, target_title in _SEED_DEPENDENCIES:
        source_id = issue_map[source_title]
        target_id = issue_map[target_title]
        add_dependency_action(repo, source_id, target_id)
        console.print(f"  [dim]Dependency:[/dim] {source_title[:40]}... -> {target_title[:40]}...")

    console.print(
        Panel(
            f"[bold]Demo data seeded successfully![/bold]\n\n"
            f"Project: {project_name}\n"
            f"Components: {len(_SEED_COMPONENTS)}\n"
            f"Issues: {len(_SEED_ISSUES)}\n"
            f"Dependencies: {len(_SEED_DEPENDENCIES)}\n\n"
            f"[bold]Try these commands:[/bold]\n"
            f"  tasker issue list --project {project_name}\n"
            f"  tasker dependency blocked\n"
            f"  tasker analyze impact <issue-id>",
            title="[bold]Seed Complete[/bold]",
            border_style="green",
        )
    )
