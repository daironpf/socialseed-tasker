"""Guard the analysis examples in ``API_REFERENCE.md`` against OpenAPI (#608).

Both reference copies document the root-cause contract with the legacy
``test_failure``/``component_id`` fields. These checks keep the examples in
sync with ``TestFailureRequest`` and with the deprecated alias.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from socialseed_tasker.infrastructure.web_api.app import create_app

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = [
    ROOT / "API_REFERENCE.md",
    ROOT / "docs" / "API_REFERENCE.md",
    ROOT / ".agent" / "skills" / "api-client.md",
]

FENCE = re.compile(r"```(?:bash|json|http|python)\n(.*?)```", re.DOTALL)
ENDPOINT = re.compile(r"(?:/api/v1)?/analyze/(root-cause|link-test)")


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return create_app().openapi()


def _request_schema(spec: dict[str, Any], endpoint: str) -> dict[str, Any]:
    path = f"/api/v1/analyze/{endpoint}"
    schema = spec["paths"][path]["post"]["requestBody"]["content"]["application/json"]["schema"]
    name = schema["$ref"].rsplit("/", 1)[-1]
    return spec["components"]["schemas"][name]


def _examples(document: Path) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {"root-cause": [], "link-test": []}
    for block in FENCE.findall(document.read_text(encoding="utf-8")):
        match = ENDPOINT.search(block)
        if match is None:
            continue
        if "-d '" in block:
            raw = block.split("-d '", 1)[1]
        else:
            start = block.find("{")
            if start < 0:
                continue
            raw = block[start:]
        try:
            payload, _ = json.JSONDecoder().raw_decode(raw)
        except json.JSONDecodeError:
            continue
        found[match.group(1)].append(payload)
    return found


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda path: path.name)
def test_documented_analysis_examples_match_openapi(
    document: Path, spec: dict[str, Any]
) -> None:
    examples = {
        endpoint: payloads
        for endpoint, payloads in _examples(document).items()
        if payloads
    }
    assert "link-test" in examples, f"{document} has no link-test example"
    for endpoint, payloads in examples.items():
        schema = _request_schema(spec, endpoint)
        for payload in payloads:
            jsonschema.validate(payload, schema)
            assert "test_failure" not in payload
            assert "component_id" not in payload


def test_root_cause_is_deprecated_and_shares_link_test_contract(
    spec: dict[str, Any],
) -> None:
    root_cause = spec["paths"]["/api/v1/analyze/root-cause"]["post"]
    link_test = spec["paths"]["/api/v1/analyze/link-test"]["post"]
    assert root_cause["deprecated"] is True
    assert "link-test" in root_cause["description"]
    assert link_test.get("deprecated", False) is False
    assert _request_schema(spec, "root-cause") == _request_schema(spec, "link-test")
