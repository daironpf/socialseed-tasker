#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.contracts.validator import compare_contract


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="contractctl")
    sub = p.add_subparsers(dest="cmd")
    run = sub.add_parser("run")
    run.add_argument("--provider", required=True)
    run.add_argument("--spec", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--endpoints", nargs="*", default=[])
    args = p.parse_args(argv)
    if args.cmd == "run":
        report = compare_contract(
            args.provider, args.spec, endpoints=args.endpoints or None
        )
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print("wrote", args.out)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
