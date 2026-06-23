from __future__ import annotations

from pathlib import Path
from typing import Any

from invarianteval.core.case import AssertionSpec, EvalCase
from invarianteval.core.suite import (
    EquivalenceClass,
    EvalSuite,
    ModelConfig,
    _parse_assertion,
    load_suite,
)
from invarianteval.providers.base import FieldPolicy

INVARIANT_ASSERTION_NAMES = frozenset(
    {
        "never_auto_filled",
        "provenance_required",
        "schema_faithful",
        "equivalence_preserved",
        "confidence_gated",
    }
)


def suite_from_policy(policy: dict[str, Any], *, suite_dir: Path | None = None) -> EvalSuite:
    base = suite_dir or Path.cwd()
    field_policies: dict[str, FieldPolicy] = {}
    for key, value in (policy.get("field_policies") or {}).items():
        field_policies[key] = FieldPolicy(value)

    equivalence_classes: dict[str, EquivalenceClass] = {}
    for name, spec in (policy.get("equivalence_classes") or {}).items():
        equivalence_classes[name] = EquivalenceClass(**spec)

    assertions = [_parse_assertion(item) for item in policy.get("assertions", [])]
    cases: list[EvalCase] = []
    if assertions:
        cases.append(
            EvalCase(
                id="mcp-check",
                input_file=str(base / "mcp-check-input.txt"),
                assertions=assertions,
            )
        )

    model_raw = policy.get("model") or {}
    return EvalSuite(
        name=policy.get("name", "mcp-inline"),
        seed=policy.get("seed"),
        schema_file=policy.get("schema_file"),
        field_policies=field_policies,
        equivalence_classes=equivalence_classes,
        cases=cases,
        suite_dir=base,
        model=ModelConfig(**model_raw) if model_raw else ModelConfig(),
    )


def collect_invariant_specs(suite: EvalSuite) -> list[AssertionSpec]:
    specs: list[AssertionSpec] = []
    for case in suite.cases:
        for spec in case.assertions:
            if spec.name == "judged":
                continue
            if spec.name in INVARIANT_ASSERTION_NAMES:
                specs.append(spec)
    return _dedupe_specs(specs)


def _dedupe_specs(specs: list[AssertionSpec]) -> list[AssertionSpec]:
    seen: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
    out: list[AssertionSpec] = []
    for spec in specs:
        key = (spec.name, tuple(sorted((k, str(v)) for k, v in spec.params.items())))
        if key in seen:
            continue
        seen.add(key)
        out.append(spec)
    return out


def load_suite_for_check(suite_path: str | None, policy: dict[str, Any] | None) -> EvalSuite:
    if suite_path and policy:
        raise ValueError("Provide suite_path or policy, not both")
    if suite_path:
        return load_suite(Path(suite_path))
    if policy:
        return suite_from_policy(policy)
    raise ValueError("suite_path or policy is required")
