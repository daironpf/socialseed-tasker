"""Allowed agent models and their runtime configuration requirements (#614)."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentModel:
    provider: str
    configuration_variables: tuple[str, ...]
    temperature_min: float = 0.0
    temperature_max: float = 2.0


AGENT_MODELS: Mapping[str, AgentModel] = {
    "claude-3.5-sonnet": AgentModel("anthropic", ("ANTHROPIC_API_KEY",), temperature_max=1.0),
    "claude-3-opus": AgentModel("anthropic", ("ANTHROPIC_API_KEY",), temperature_max=1.0),
    "gpt-4-turbo": AgentModel("openai", ("OPENAI_API_KEY",)),
    "gpt-4o": AgentModel("openai", ("OPENAI_API_KEY",)),
    "gemini-pro": AgentModel("google", ("GEMINI_API_KEY", "GOOGLE_API_KEY")),
    "llama-3": AgentModel("ollama", ("OLLAMA_BASE_URL",)),
}


class AgentModelConfigurationError(ValueError):
    """A safe, user-facing model configuration error without secret values."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.status_code = status_code


def validate_agent_model(
    model: str | None,
    temperature: float | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    """Reject missing, unsupported, unconfigured, or incompatible model settings."""
    if model is None or not model.strip():
        raise AgentModelConfigurationError(
            "model_required", "select an allowed model", status_code=422
        )

    spec = AGENT_MODELS.get(model)
    if spec is None:
        raise AgentModelConfigurationError(
            "model_not_allowed",
            f"{model!r} is not in the allowed model catalog",
            status_code=422,
        )

    if temperature is not None and (
        not math.isfinite(temperature)
        or temperature < spec.temperature_min
        or temperature > spec.temperature_max
    ):
        raise AgentModelConfigurationError(
            "model_parameter_incompatible",
            f"temperature for {model!r} must be between "
            f"{spec.temperature_min:g} and {spec.temperature_max:g}",
            status_code=422,
        )

    configuration = os.environ if environ is None else environ
    if not any(configuration.get(name, "").strip() for name in spec.configuration_variables):
        variables = " or ".join(spec.configuration_variables)
        raise AgentModelConfigurationError(
            "model_not_configured",
            f"{model!r} requires runtime configuration ({variables})",
            status_code=503,
        )
