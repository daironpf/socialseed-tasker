from __future__ import annotations

import argparse
import json

from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.graphviz.builder import build_graph, compute_impact


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="tasker-graphviz")
    sub = p.add_subparsers(dest="cmd")

    b = sub.add_parser("build")
    b.add_argument("--out", required=True)

    i = sub.add_parser("impact")
    i.add_argument("--node", required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--max-depth", type=int, default=5)

    e = sub.add_parser("export-svg")
    e.add_argument("--out", required=True)

    args = p.parse_args(argv)
    container = build_default_container()
    g = build_graph(container)

    if args.cmd == "build":
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(g.to_json(), fh, indent=2)
        print("wrote", args.out)

    elif args.cmd == "impact":
        imp = compute_impact(g, args.node, max_depth=args.max_depth)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"node": args.node, "impact": imp}, fh, indent=2)
        print("wrote", args.out)

    elif args.cmd == "export-svg":
        nodes = g.to_json()["nodes"]
        edges = g.to_json()["edges"]
        width = 800
        y_step = 40
        svg_lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}">']
        id_to_y: dict[str, int] = {}
        for idx, n in enumerate(nodes):
            y = 20 + idx * y_step
            id_to_y[n["id"]] = y
            svg_lines.append(
                f'<text x="10" y="{y}" font-family="monospace">{n["id"]}: {n["label"]}</text>'
            )
        for e in edges:
            y1 = id_to_y.get(e["from"], 0)
            y2 = id_to_y.get(e["to"], 0)
            svg_lines.append(
                f'<line x1="200" y1="{y1 - 5}" x2="400" y2="{y2 - 5}" stroke="black" />'
            )
        svg_lines.append("</svg>")
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(svg_lines))
        print("wrote", args.out)

    else:
        p.print_help()


if __name__ == "__main__":
    main()
