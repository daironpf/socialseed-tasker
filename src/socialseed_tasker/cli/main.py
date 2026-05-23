"""Thin CLI entrypoint — parses args, wires adapters, delegates to application use cases."""

from __future__ import annotations

import argparse
import json
import os
import sys

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.exceptions import GraphPortError, ParserError, PermissionError
from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.observability.logging import get_logger
from celery.result import AsyncResult
from socialseed_tasker.workers.app import create_celery

logger = get_logger("tasker.cli")


def _print_json(obj: object, stream: object = None) -> None:
    stream = stream or sys.stdout
    stream.write(json.dumps(obj, ensure_ascii=False))
    stream.write("\n")
    stream.flush()


def _error_and_exit(command: str, payload: dict, details: str = "") -> None:
    logger.error("cli.error", extra={"command": command, "error": str(details or "unknown error"), **payload})
    out = {
        "status": "error",
        "command": command,
        **payload,
        "error": str(details or "unknown error"),
        "details": details or "",
    }
    _print_json(out, stream=sys.stderr)
    sys.exit(2)


def cmd_agent_context(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        if not container.rbac.has_permission(user_id, "read:context"):
            raise PermissionError("forbidden")
        usecase = container.application.generate_agent_context
        ctx = usecase(
            issue_id=args.issue_id,
            max_depth=int(args.max_depth),
            graph_repo=container.graph_repo,
            issue_repo=container.issue_repo,
            parser=container.parser,
            user_id=user_id,
        )
        _print_json(
            {"status": "ok", "command": "agent-context", "issue_id": args.issue_id, "context": ctx}
        )
    except PermissionError as pexc:
        _error_and_exit("agent-context", {"issue_id": args.issue_id}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("agent-context", {"issue_id": args.issue_id}, details=str(exc))


def cmd_calculate_impact(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        if not container.rbac.has_permission(user_id, "read:impact"):
            raise PermissionError("forbidden")
        usecase = container.application.calculate_impact
        impact = usecase(
            issue_id=args.issue_id,
            max_depth=int(args.max_depth),
            graph_repo=container.graph_repo,
            user_id=user_id,
        )
        _print_json(
            {
                "status": "ok",
                "command": "calculate-impact",
                "issue_id": args.issue_id,
                "impact_set": list(impact),
            }
        )
    except PermissionError as pexc:
        _error_and_exit("calculate-impact", {"issue_id": args.issue_id}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("calculate-impact", {"issue_id": args.issue_id}, details=str(exc))


def cmd_create_issue(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        if not container.rbac.has_permission(user_id, "create:issue"):
            raise PermissionError("forbidden")
        dto = IssueDTO(
            id=args.id,
            title=args.title,
            description=(args.description or ""),
            status=(args.status or "open"),
            metadata={},
        )
        container.issue_repo.save(dto)
        _print_json(
            {
                "status": "ok",
                "command": "create-issue",
                "issue": {"id": dto.id, "title": dto.title, "status": dto.status},
            }
        )
    except PermissionError as pexc:
        _error_and_exit("create-issue", {"id": args.id}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("create-issue", {"id": args.id}, details=str(exc))


def cmd_add_dependency(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        if not container.rbac.has_permission(user_id, "add:dependency"):
            raise PermissionError("forbidden")
        edge = DependencyEdge(
            from_issue_id=args.from_id,
            to_issue_id=args.to,
            relation=(args.relation or "DEPENDS_ON"),
            metadata={},
        )
        container.graph_repo.add_dependency(edge)
        _print_json(
            {
                "status": "ok",
                "command": "add-dependency",
                "edge": {
                    "from": edge.from_issue_id,
                    "to": edge.to_issue_id,
                    "relation": edge.relation,
                },
            }
        )
    except PermissionError as pexc:
        _error_and_exit("add-dependency", {"from": args.from_id, "to": args.to}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("add-dependency", {"from": args.from_id, "to": args.to}, details=str(exc))


def cmd_parse_file(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        if not container.rbac.has_permission(user_id, "admin"):
            raise PermissionError("forbidden")
        parser = container.parser
        ast = parser.parse_file(args.path)
        symbols = parser.extract_symbols(ast)
        imports = parser.extract_imports(ast)
        _print_json(
            {
                "status": "ok",
                "command": "parse-file",
                "path": args.path,
                "symbols": symbols,
                "imports": imports,
            }
        )
    except PermissionError as pexc:
        _error_and_exit("parse-file", {"path": args.path}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("parse-file", {"path": args.path}, details=str(exc))


def cmd_enqueue_task(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        if not container.rbac.has_permission(user_id, "admin") and not container.rbac.has_permission(user_id, "background:enqueue"):
            raise PermissionError("forbidden")
        celery = create_celery()
        payload = json.loads(args.payload)
        if args.task == "parse_and_index_files":
            task = celery.send_task("tasker.parse_and_index_files", args=[payload.get("file_paths", [])])
        elif args.task == "batch_embed_and_store":
            task = celery.send_task("tasker.batch_embed_and_store", args=[payload.get("docs", []), payload.get("store_key", "default")])
        elif args.task == "run_graph_analysis":
            task = celery.send_task("tasker.run_graph_analysis", args=[payload.get("issue_id"), int(payload.get("depth", 3))])
        else:
            _error_and_exit("enqueue-task", {}, details=f"Unknown task {args.task}")
        _print_json({"status": "ok", "command": "enqueue-task", "task_id": task.id})
    except PermissionError as pexc:
        _error_and_exit("enqueue-task", {}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("enqueue-task", {}, details=str(exc))

def cmd_task_status(args: argparse.Namespace, container: object, user_id: str | None) -> None:
    try:
        celery = create_celery()
        res = AsyncResult(args.task_id, app=celery)
        out = {"status": res.status}
        if res.ready():
            out["result"] = res.result
        _print_json({"status": "ok", "command": "task-status", "task_id": args.task_id, "task": out})
    except Exception as exc:
        _error_and_exit("task-status", {"task_id": args.task_id}, details=str(exc))

def main(argv: list[str] | None = None) -> None:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(prog="tasker")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("agent-context")
    p.add_argument("--issue-id", required=True)
    p.add_argument("--max-depth", default="3")
    p.add_argument("--format", default="json")

    p = sub.add_parser("calculate-impact")
    p.add_argument("--issue-id", required=True)
    p.add_argument("--max-depth", default="5")

    p = sub.add_parser("create-issue")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description")
    p.add_argument("--status")

    p = sub.add_parser("add-dependency")
    p.add_argument("--from", dest="from_id", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--relation")

    p = sub.add_parser("parse-file")
    p.add_argument("--path", required=True)

    p = sub.add_parser("enqueue-task")
    p.add_argument("--task", required=True, help="Task name to enqueue")
    p.add_argument("--payload", required=True, help="JSON payload for the task")

    p = sub.add_parser("task-status")
    p.add_argument("--task-id", required=True)

    # Add --token to all subcommands
    for name, subp in list(sub.choices.items()):
        subp.add_argument("--token")

    args = parser.parse_args(argv)
    container = build_default_container()

    logger.info("cli.invoke", extra={"command": args.command, "args": vars(args)})

    token = getattr(args, "token", None) or os.getenv("TASKER_AUTH_TOKEN")
    user_id = None
    if token:
        user_id = container.auth.verify_token(token)
        if user_id is None:
            _error_and_exit(args.command, {}, details="unauthenticated")
    else:
        _error_and_exit(args.command, {}, details="unauthenticated")

    from socialseed_tasker.cli.rate_limit_cli import check_cli_rate
    if not check_cli_rate(container, user_id):
        _error_and_exit(args.command, {}, details="rate_limited")

    if args.command == "agent-context":
        cmd_agent_context(args, container, user_id)
    elif args.command == "calculate-impact":
        cmd_calculate_impact(args, container, user_id)
    elif args.command == "create-issue":
        cmd_create_issue(args, container, user_id)
    elif args.command == "add-dependency":
        cmd_add_dependency(args, container, user_id)
    elif args.command == "parse-file":
        cmd_parse_file(args, container, user_id)
    elif args.command == "enqueue-task":
        cmd_enqueue_task(args, container, user_id)
    elif args.command == "task-status":
        cmd_task_status(args, container, user_id)
    else:
        _error_and_exit("unknown", {}, details=f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
