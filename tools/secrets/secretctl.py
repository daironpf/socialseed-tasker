#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from socialseed_tasker.cli.wiring import build_default_container


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="secretctl")
    sub = p.add_subparsers(dest="cmd")

    put = sub.add_parser("put")
    put.add_argument("--name", required=True)
    put.add_argument("--file", required=True)
    put.add_argument("--meta", default=None)

    get = sub.add_parser("get")
    get.add_argument("--name", required=True)
    get.add_argument("--value", action="store_true")

    delete = sub.add_parser("delete")
    delete.add_argument("--name", required=True)

    rotate = sub.add_parser("rotate")
    rotate.add_argument("--name", required=True)
    rotate.add_argument("--interval", type=int, required=True)
    rotate.add_argument("--policy", required=True)

    rotate_run = sub.add_parser("rotate-run")
    rotate_run.add_argument("--id", required=True)

    audit = sub.add_parser("audit")
    audit.add_argument("--out", required=True)

    args = p.parse_args(argv)
    container = build_default_container()
    ss = container.secrets_store
    rot = container.secrets_rotator

    if args.cmd == "put":
        with open(args.file, "rb") as fh:
            b = fh.read()
        meta = json.loads(args.meta) if args.meta else {}
        ss.put_secret(args.name, b, metadata=meta, actor="cli")
        print("ok")
    elif args.cmd == "get":
        if args.value:
            res = ss.get_secret(args.name, reveal=True)
            sys.stdout.buffer.write(res["value"])
        else:
            res = ss.get_secret(args.name, reveal=False)
            print(json.dumps(res["metadata"], indent=2))
    elif args.cmd == "delete":
        ss.delete_secret(args.name, actor="cli")
        print("ok")
    elif args.cmd == "rotate":
        policy = json.loads(args.policy)
        rid = rot.schedule_rotation(args.name, args.interval, policy)
        print(rid)
    elif args.cmd == "rotate-run":
        res = rot.run_rotation(args.id)
        print(json.dumps(res, indent=2))
    elif args.cmd == "audit":
        raw = container.storage.get("secrets:audit") or b"[]"
        with open(args.out, "wb") as fh:
            fh.write(raw)
        print("wrote", args.out)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
