from __future__ import annotations

import json
import sys

from socialseed_tasker.application.exceptions import PermissionError


def _print_json(obj: object) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error_and_exit(command: str, payload: dict, details: str = "") -> None:
    out = {
        "status": "error",
        "command": command,
        **payload,
        "error": str(details or "unknown error"),
        "details": details or "",
    }
    sys.stderr.write(json.dumps(out, ensure_ascii=False) + "\n")
    sys.stderr.flush()
    sys.exit(2)


def cmd_flag_set(args, container, user_id) -> None:
    try:
        if not container.rbac.has_permission(user_id, "admin"):
            raise PermissionError("forbidden")
        container.runtime_config.set(args.name, args.value)
        _print_json({"status": "ok", "command": "flag-set", "name": args.name, "value": args.value})
    except PermissionError as pexc:
        _error_and_exit("flag-set", {"name": args.name}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("flag-set", {"name": args.name}, details=str(exc))


def cmd_flag_get(args, container, user_id) -> None:
    try:
        if not container.rbac.has_permission(user_id, "admin"):
            raise PermissionError("forbidden")
        v = container.runtime_config.get(args.name, None)
        _print_json({"status": "ok", "command": "flag-get", "name": args.name, "value": v})
    except PermissionError as pexc:
        _error_and_exit("flag-get", {"name": args.name}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("flag-get", {"name": args.name}, details=str(exc))


def cmd_flag_list(args, container, user_id) -> None:
    try:
        if not container.rbac.has_permission(user_id, "admin"):
            raise PermissionError("forbidden")
        flags = container.runtime_config.list()
        _print_json({"status": "ok", "command": "flag-list", "flags": flags})
    except PermissionError as pexc:
        _error_and_exit("flag-list", {}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("flag-list", {}, details=str(exc))


def cmd_flag_delete(args, container, user_id) -> None:
    try:
        if not container.rbac.has_permission(user_id, "admin"):
            raise PermissionError("forbidden")
        container.runtime_config.delete(args.name)
        _print_json({"status": "ok", "command": "flag-delete", "name": args.name})
    except PermissionError as pexc:
        _error_and_exit("flag-delete", {"name": args.name}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("flag-delete", {"name": args.name}, details=str(exc))
