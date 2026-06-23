from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from invarianteval.providers.base import FieldPolicy, Provenance


class FieldTrace(BaseModel):
    field: str
    value: Any
    provenance: Provenance
    model_originated: bool
    policy: FieldPolicy
    confidence: float | None = None
    source_span: tuple[int, int] | None = None
    evidence_text: str | None = None


class Trace(BaseModel):
    case_id: str
    input_text: str = ""
    fields: dict[str, FieldTrace] = Field(default_factory=dict)

    def field(self, name: str) -> FieldTrace | None:
        return self.fields.get(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            name: {
                "value": ft.value,
                "provenance": ft.provenance.value,
                "model_originated": ft.model_originated,
                "policy": ft.policy.value,
                "confidence": ft.confidence,
                "source_span": list(ft.source_span) if ft.source_span else None,
                "evidence_text": ft.evidence_text,
            }
            for name, ft in self.fields.items()
        }
