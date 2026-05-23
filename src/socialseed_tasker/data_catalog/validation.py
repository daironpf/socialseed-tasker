from __future__ import annotations
from fastapi import Request, HTTPException
from jsonschema import validate, ValidationError
from typing import Dict, Any
from socialseed_tasker.cli.wiring import build_default_container


def validate_payload(dataset_id: str, payload: Dict[str, Any], version: str | None = None) -> None:
    container = build_default_container()
    reg = container.schema_registry
    ds = reg.get_dataset(dataset_id)
    schema_name = ds["schema_name"]
    schema_version = version or ds["default_schema_version"]
    schema = reg.get_schema(schema_name, schema_version)
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"schema validation error: {exc.message}")


class ValidationMiddleware:
    @staticmethod
    async def validate_request(request: Request, dataset_id: str):
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="invalid json")
        validate_payload(dataset_id, body)
