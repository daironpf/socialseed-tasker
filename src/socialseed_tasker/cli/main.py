"""Thin CLI entrypoint — parses args, wires adapters, delegates to application use cases."""

from __future__ import annotations

import argparse
import json
import sys

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.exceptions import GraphPortError, ParserError
from socialseed_tasker.cli.wiring import build_default_container


def _print_json(obj: object, stream: object = None) -> None:
    stream = stream or sys.stdout
    stream.write(json.dumps(obj, ensure_ascii=False))
    stream.write("\n")
    stream.flush()


def _error_and_exit(command: str, payload: dict, details: str = "") -> None:
    out = {
        "status": "error",
        "command": command,
        **payload,
        "error": str(details or "unknown error"),
        "details": details or "",
    }
    _print_json(out, stream=sys.stderr)
    sys.exit(2)


def cmd_agent_context(args: argparse.Namespace, container: object) -> None:
    try:
        usecase = container.application.generate_agent_context
        ctx = usecase(issue_id=args.issue_id, max_depth=int(args.max_depth))
        _print_json(
            {"status": "ok", "command": "agent-context", "issue_id": args.issue_id, "context": ctx}
        )
    except Exception as exc:
        _error_and_exit("agent-context", {"issue_id": args.issue_id}, details=str(exc))


def cmd_calculate_impact(args: argparse.Namespace, container: object) -> None:
    try:
        usecase = container.application.calculate_impact
        impact = usecase(issue_id=args.issue_id, max_depth=int(args.max_depth))
        _print_json(
            {
                "status": "ok",
                "command": "calculate-impact",
                "issue_id": args.issue_id,
                "impact_set": list(impact),
            }
        )
    except Exception as exc:
        _error_and_exit("calculate-impact", {"issue_id": args.issue_id}, details=str(exc))


def cmd_create_issue(args: argparse.Namespace, container: object) -> None:
    try:
        usecase = container.application.create_issue
        dto = IssueDTO(
            id=args.id,
            title=args.title,
            description=(args.description or ""),
            status=(args.status or "open"),
            metadata={},
        )
        usecase(issue=dto)
        _print_json(
            {
                "status": "ok",
                "command": "create-issue",
                "issue": {"id": dto.id, "title": dto.title, "status": dto.status},
            }
        )
    except Exception as exc:
        _error_and_exit("create-issue", {"id": args.id}, details=str(exc))


def cmd_add_dependency(args: argparse.Namespace, container: object) -> None:
    try:
        usecase = container.application.add_dependency
        edge = DependencyEdge(
            from_issue_id=args.from_id,
            to_issue_id=args.to,
            relation=(args.relation or "DEPENDS_ON"),
            metadata={},
        )
        usecase(edge=edge)
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
    except Exception as exc:
        _error_and_exit("add-dependency", {"from": args.from_id, "to": args.to}, details=str(exc))


def cmd_parse_file(args: argparse.Namespace, container: object) -> None:
    try:
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
    except Exception as exc:
        _error_and_exit("parse-file", {"path": args.path}, details=str(exc))


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

    args = parser.parse_args(argv)
    container = build_default_container()

    if args.command == "agent-context":
        cmd_agent_context(args, container)
    elif args.command == "calculate-impact":
        cmd_calculate_impact(args, container)
    elif args.command == "create-issue":
        cmd_create_issue(args, container)
    elif args.command == "add-dependency":
        cmd_add_dependency(args, container)
    elif args.command == "parse-file":
        cmd_parse_file(args, container)
    else:
        _error_and_exit("unknown", {}, details=f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
