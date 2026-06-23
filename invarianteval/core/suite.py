from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from invarianteval.core.case import AssertionSpec, EvalCase
from invarianteval.providers.base import FieldPolicy


class EquivalenceClass(BaseModel):
    fields: list[str]
    rule: str = "equal"
    mapping: dict[str, str] | None = None
    groups: list[list[str]] | None = None
    tolerance: float | None = None


class ModelConfig(BaseModel):
    provider: str = "ollama"
    name: str = "qwen2.5:7b"
    pinned_digest: str | None = None


class EvalSuite(BaseModel):
    name: str
    data_snapshot: str | None = None
    model: ModelConfig = Field(default_factory=ModelConfig)
    seed: int | None = None
    schema_file: str | None = None
    field_policies: dict[str, FieldPolicy] = Field(default_factory=dict)
    equivalence_classes: dict[str, EquivalenceClass] = Field(default_factory=dict)
    cases: list[EvalCase] = Field(default_factory=list)
    suite_dir: Path = Field(default=Path("."), exclude=True)

    def schema_path(self) -> Path | None:
        if not self.schema_file:
            return None
        return self.suite_dir / self.schema_file


def _parse_assertion(item: Any) -> AssertionSpec:
    if isinstance(item, str):
        return AssertionSpec(name=item, params={})
    if isinstance(item, dict):
        if len(item) != 1:
            raise ValueError(f"Invalid assertion spec: {item}")
        name, params = next(iter(item.items()))
        if isinstance(params, str):
            return AssertionSpec(name=name, params={"field": params})
        if isinstance(params, dict):
            return AssertionSpec(name=name, params=params)
        return AssertionSpec(name=name, params={"value": params})
    raise ValueError(f"Invalid assertion: {item}")


def load_suite(path: Path) -> EvalSuite:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    suite_dir = path.parent

    field_policies: dict[str, FieldPolicy] = {}
    for key, value in (raw.get("field_policies") or {}).items():
        field_policies[key] = FieldPolicy(value)

    equivalence_classes: dict[str, EquivalenceClass] = {}
    for name, spec in (raw.get("equivalence_classes") or {}).items():
        equivalence_classes[name] = EquivalenceClass(**spec)

    cases: list[EvalCase] = []
    for case_raw in raw.get("cases", []):
        assertions = [_parse_assertion(a) for a in case_raw.get("assertions", [])]
        cases.append(
            EvalCase(
                id=case_raw["id"],
                input_file=case_raw["input_file"],
                expected_file=case_raw.get("expected_file"),
                assertions=assertions,
                metadata=case_raw.get("metadata", {}),
            )
        )

    model_raw = raw.get("model", {})
    return EvalSuite(
        name=raw["name"],
        data_snapshot=raw.get("data_snapshot"),
        model=ModelConfig(**model_raw) if model_raw else ModelConfig(),
        seed=raw.get("seed"),
        schema_file=raw.get("schema_file"),
        field_policies=field_policies,
        equivalence_classes=equivalence_classes,
        cases=cases,
        suite_dir=suite_dir,
    )
