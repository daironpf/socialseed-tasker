from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class InferenceRequest(BaseModel):
    key: Optional[str] = Field(None, description="Feature store key to fetch features")
    features: Optional[Dict[str, Any]] = Field(None, description="Inline features if not using feature store")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    model: str
    version: str
    prediction: Any
    input_hash: str
    seed: int
    latency_ms: float
    meta: Dict[str, Any] = Field(default_factory=dict)
