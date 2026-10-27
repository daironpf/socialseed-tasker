from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    key: str | None = Field(None, description="Feature store key to fetch features")
    features: dict[str, Any] | None = Field(None, description="Inline features if not using feature store")
    params: dict[str, Any] | None = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    model: str
    version: str
    prediction: Any
    input_hash: str
    seed: int
    latency_ms: float
    meta: dict[str, Any] = Field(default_factory=dict)
