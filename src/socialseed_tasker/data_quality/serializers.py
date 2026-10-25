from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Any, Dict, Optional

from socialseed_tasker.data_quality.rules import SUPPORTED_KINDS

class RuleSpec(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    kind: str
    target: str
    config: Dict[str, Any] = {}
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
    message: Optional[str] = None
    record_id: Optional[str] = None
    details: Dict[str, Any] = {}
