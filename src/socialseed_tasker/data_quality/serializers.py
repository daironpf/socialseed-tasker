from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Dict, Optional

class RuleSpec(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    kind: str
    target: str
    config: Dict[str, Any] = {}
    enabled: bool = True

class ValidationResult(BaseModel):
    rule_id: str
    ok: bool
    message: Optional[str] = None
    record_id: Optional[str] = None
    details: Dict[str, Any] = {}
