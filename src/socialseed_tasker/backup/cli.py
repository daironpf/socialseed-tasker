# src/socialseed_tasker/backup/cli.py
from __future__ import annotations
import argparse
import os
import sys
from socialseed_tasker.backup.core import export_data, verify_export, restore_data, list_exports
from socialseed_tasker.cli.wiring import build_default_container

def main(argv=None):
    p = argparse.ArgumentParser(prog="tasker-backup")
    sub = p.add_subparsers(dest="cmd")
    ex = sub.add_parser("export")
    ex.add_argument("--out", required=True)
    ex.add_argument("--no-storage", action="store_true")
    ex.add_argument("--encrypt", action="store_true")
    ex.add_argument("--passphrase", default=None)
    vr = sub.add_parser("verify")
    vr.add_argument("--file", required=True)
    rs = sub.add_parser("restore")
    rs.add_argument("--file", required=True)
    rs.add_argument("--passphrase", default=None)
    ls = sub.add_parser("list")
    args = p.parse_args(argv)

    container = build_default_container()
    if args.cmd == "export":
        out = args.out
        include_storage = not args.no_storage
        path = export_data(out, issue_repo=container.issue_repo, graph_repo=container.graph_repo, storage=container.storage if include_storage else None, include_storage=include_storage, encrypt=args.encrypt, passphrase=args.passphrase)
        print("Exported to", path)
    elif args.cmd == "verify":
        ok = verify_export(args.file)
        print("Verified" if ok else "Invalid")
        sys.exit(0 if ok else 2)
    elif args.cmd == "restore":
        restore_data(args.file, issue_repo=container.issue_repo, graph_repo=container.graph_repo, storage=container.storage, decrypt_passphrase=args.passphrase)
        print("Restore complete")
    elif args.cmd == "list":
        exports = list_exports(os.getcwd())
        for e in exports:
            print(e)
    else:
        p.print_help()
