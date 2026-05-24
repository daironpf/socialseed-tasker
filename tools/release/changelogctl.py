#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os

from tools.release.changelog import generate_changelog


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="changelogctl")
    sub = p.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("--from", dest="from_ref", required=True)
    g.add_argument("--to", dest="to_ref", required=True)
    g.add_argument("--out", dest="out", required=True)
    g.add_argument("--template", dest="template", default=None)
    g.add_argument("--no-prs", dest="no_prs", action="store_true")
    args = p.parse_args(argv)
    if args.cmd == "generate":
        gh_token = os.getenv("RELEASE_GH_TOKEN")
        repo = os.getenv("RELEASE_GH_REPO")
        include_prs = not args.no_prs
        generate_changelog(
            args.out,
            args.from_ref,
            args.to_ref,
            template_path=args.template,
            include_prs=include_prs,
            gh_token=gh_token,
            repo=repo,
        )
    else:
        p.print_help()


if __name__ == "__main__":
    main()
