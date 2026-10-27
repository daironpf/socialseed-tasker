from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from socialseed_tasker.data_quality.rules import SUPPORTED_KINDS


class RuleSpec(BaseModel):
    id: str
    name: str
    description: str | None = None
    kind: str
    target: str
    config: dict[str, Any] = {}
    enabled: bool = True

    @field_validator("kind")
    @classmethod
    def _check_kind(cls, v: str) -> str:
        if v not in SUPPORTED_KINDS:
            raise ValueError(
                f"unsupported rule kind '{v}'; expected one of: {', '.join(SUPPORTED_KINDS)}"
            )
        return v

class ValidationResult(BaseModel):
    rule_id: str
    ok: bool
    message: str | None = None
    record_id: str | None = None
    details: dict[str, Any] = {}
