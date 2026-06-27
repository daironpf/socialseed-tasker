from __future__ import annotations
import argparse
import json
from socialseed_tasker.cli.wiring import build_default_container


def cmd_register_schema(args):
    container = build_default_container()
    reg = container.schema_registry
    with open(args.file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    reg.register_schema(args.name, args.version, schema, compatibility=args.compatibility)
    print("ok")


def cmd_get_schema(args):
    container = build_default_container()
    reg = container.schema_registry
    s = reg.get_schema(args.name, args.version)
    print(json.dumps(s, indent=2))


def cmd_register_dataset(args):
    container = build_default_container()
    reg = container.schema_registry
    reg.register_dataset(args.dataset_id, args.title, args.description, args.schema_name, args.default_schema_version, args.owner, tags=args.tags or [])
    print("ok")


def main(argv=None):
    p = argparse.ArgumentParser(prog="tasker-registry")
    sub = p.add_subparsers(dest="cmd")
    rs = sub.add_parser("register-schema")
    rs.add_argument("--name", required=True)
    rs.add_argument("--version", required=True)
    rs.add_argument("--file", required=True)
    rs.add_argument("--compatibility", default="BACKWARD")
    gs = sub.add_parser("get-schema")
    gs.add_argument("--name", required=True)
    gs.add_argument("--version", required=True)
    rd = sub.add_parser("register-dataset")
    rd.add_argument("--dataset-id", required=True)
    rd.add_argument("--title", required=True)
    rd.add_argument("--description", required=True)
    rd.add_argument("--schema-name", required=True)
    rd.add_argument("--default-schema-version", required=True)
    rd.add_argument("--owner", required=True)
    rd.add_argument("--tags", nargs="*", default=[])
    args = p.parse_args(argv)
    if args.cmd == "register-schema":
        cmd_register_schema(args)
    elif args.cmd == "get-schema":
        cmd_get_schema(args)
    elif args.cmd == "register-dataset":
        cmd_register_dataset(args)
    else:
        p.print_help()
