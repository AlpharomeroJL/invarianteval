from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class FieldPolicy(StrEnum):
    locked = "locked"
    model_allowed = "model_allowed"


class Provenance(StrEnum):
    human_entered = "human_entered"
    ai_suggested = "ai_suggested"
    ai_confirmed_by_human = "ai_confirmed_by_human"


class ProviderResult(BaseModel):
    raw: str
    parsed: dict[str, Any] | None = None
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    final_output: dict[str, Any] | None = None
    human_confirmed: dict[str, bool] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    source_spans: dict[str, list[int]] = Field(default_factory=dict)
    case_input: str | None = None


@runtime_checkable
class Provider(Protocol):
    name: str

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str,
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult: ...

    def health_check(self) -> bool: ...
