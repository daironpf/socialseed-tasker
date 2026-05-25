from __future__ import annotations

import hashlib
import json
import random
from typing import Any

import yaml


def load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        txt = fh.read()
    try:
        return json.loads(txt)
    except Exception:
        return yaml.safe_load(txt)


def extract_endpoints(spec: dict) -> list[dict]:
    out = []
    paths = spec.get("paths", {})
    for p, methods in sorted(paths.items(), key=lambda x: x[0]):
        for m, info in sorted(methods.items(), key=lambda x: x[0]):
            responses = info.get("responses", {})
            resp_schema = None
            if "200" in responses:
                resp_schema = (
                    responses["200"]
                    .get("content", {})
                    .get("application/json", {})
                    .get("schema")
                )
            else:
                for code in sorted(responses.keys()):
                    resp_schema = (
                        responses[code]
                        .get("content", {})
                        .get("application/json", {})
                        .get("schema")
                    )
                    if resp_schema:
                        break
            out.append(
                {
                    "method": m.upper(),
                    "path": p,
                    "operation": info.get("operationId"),
                    "response_schema": resp_schema,
                }
            )
    return out


def _seed_from_path(path: str) -> int:
    h = hashlib.sha256(path.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def generate_example(schema: dict | None, seed: int | None = None) -> Any:
    if schema is None:
        return {}
    s = seed or 42
    rnd = random.Random(s)
    t = schema.get("type")
    if t == "object":
        props = schema.get("properties", {})
        out = {}
        for k in sorted(props.keys()):
            out[k] = generate_example(
                props[k],
                seed=(s + int(hashlib.sha256(k.encode()).hexdigest()[:6], 16)),
            )
        return out
    if t == "array":
        item = schema.get("items", {})
        return [generate_example(item, seed=s)]
    if t == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            return "2020-01-01T00:00:00Z"
        enum = schema.get("enum")
        if enum:
            return enum[0]
        return f"str-{rnd.randint(1, 1000)}"
    if t == "integer":
        minimum = schema.get("minimum", 0)
        return int(minimum) + 1
    if t == "number":
        return float(schema.get("minimum", 0)) + 0.1
    if t == "boolean":
        return True
    return None
