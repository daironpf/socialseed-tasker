from __future__ import annotations

import time
from typing import Any

import requests
from jsonschema import ValidationError, validate

from .openapi import extract_endpoints, load_spec


def validate_response(schema: dict, response: dict) -> dict:
    if schema is None:
        return {"ok": True, "errors": []}
    try:
        validate(instance=response, schema=schema)
        return {"ok": True, "errors": []}
    except ValidationError as exc:
        return {"ok": False, "errors": [str(exc.message)]}


def compare_contract(
    provider_url: str,
    contract_path: str,
    endpoints: list[str] | None = None,
    timeout: int = 5,
) -> dict:
    spec = load_spec(contract_path)
    eps = extract_endpoints(spec)
    if endpoints:
        eps = [e for e in eps if f"{e['method']} {e['path']}" in endpoints]
    results = []
    for e in eps:
        url = provider_url.rstrip("/") + e["path"]
        method = e["method"].lower()
        try:
            r = getattr(requests, method)(url, timeout=timeout)
            try:
                body = r.json()
            except Exception:
                body = {}
            res = validate_response(e.get("response_schema"), body)
        except Exception as exc:
            res = {"ok": False, "errors": [str(exc)]}
        results.append(
            {
                "method": e["method"],
                "path": e["path"],
                "ok": res["ok"],
                "errors": res["errors"],
            }
        )
    overall = all(r["ok"] for r in results)
    report = {
        "provider": provider_url,
        "contract": contract_path,
        "timestamp": int(time.time()),
        "overall": overall,
        "results": results,
    }
    return report
