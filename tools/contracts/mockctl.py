#!/usr/bin/env python3
from __future__ import annotations

import argparse

from .mock_server import MockServer


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="mockctl")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("start")
    s.add_argument("--spec", required=True)
    s.add_argument("--port", type=int, default=9000)
    s.add_argument("--overrides", default=None)
    s.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)
    if args.cmd == "start":
        ms = MockServer(
            spec_path=args.spec,
            port=args.port,
            overrides_dir=args.overrides,
            seed=args.seed,
        )
        ms.start()
        print(f"mock server started on port {args.port} (spec={args.spec})")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
