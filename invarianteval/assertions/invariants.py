from __future__ import annotations

import json
from typing import Any

import jsonschema

from invarianteval.core.evidence import field_has_evidence
from invarianteval.core.models import AssertionResult
from invarianteval.core.provenance import _flatten_dict
from invarianteval.core.suite import EvalSuite
from invarianteval.core.trace import Trace
from invarianteval.providers.base import FieldPolicy, Provenance


def never_auto_filled(field: str, trace: Trace) -> AssertionResult:
    ft = trace.field(field)
    if ft is None:
        return AssertionResult(
            passed=True,
            name=f"never_auto_filled[{field}]",
            detail=f"Field {field} not in final output",
            tier="invariant",
        )
    violation = (
        ft.policy == FieldPolicy.locked
        and ft.model_originated
        and ft.provenance != Provenance.ai_confirmed_by_human
    )
    detail = None
    if violation:
        detail = (
            f"Locked field {field} was model-originated ({ft.provenance.value}) "
            "without human confirmation"
        )
    return AssertionResult(
        passed=not violation,
        name=f"never_auto_filled[{field}]",
        detail=detail,
        tier="invariant",
    )


def provenance_required(
    field: str,
    allowed: list[str],
    trace: Trace,
) -> AssertionResult:
    ft = trace.field(field)
    if ft is None:
        return AssertionResult(
            passed=False,
            name=f"provenance_required[{field}]",
            detail=f"Field {field} not in output",
            tier="invariant",
        )
    ok = ft.provenance.value in allowed
    return AssertionResult(
        passed=ok,
        name=f"provenance_required[{field}]",
        detail=None if ok else f"Provenance {ft.provenance.value} not in {allowed}",
        tier="invariant",
    )


def confidence_gated(field: str, threshold: float, trace: Trace) -> AssertionResult:
    ft = trace.field(field)
    if ft is None:
        return AssertionResult(passed=True, name=f"confidence_gated[{field}]", tier="invariant")
    if ft.confidence is None:
        return AssertionResult(passed=True, name=f"confidence_gated[{field}]", tier="invariant")
    if ft.confidence >= threshold:
        return AssertionResult(passed=True, name=f"confidence_gated[{field}]", tier="invariant")
    violation = ft.model_originated and ft.provenance == Provenance.ai_suggested
    detail = None
    if violation:
        detail = (
            f"Field {field} confidence {ft.confidence:.2f} below threshold {threshold} "
            "but emitted as final without review"
        )
    return AssertionResult(
        passed=not violation,
        name=f"confidence_gated[{field}]",
        detail=detail,
        tier="invariant",
    )


def schema_faithful(
    schema_path: str,
    output: dict[str, Any],
    suite: EvalSuite,
    *,
    mode: str = "envelope",
    input_text: str = "",
    trace: Trace | None = None,
) -> AssertionResult:
    path = suite.suite_dir / schema_path
    schema = json.loads(path.read_text(encoding="utf-8"))

    try:
        jsonschema.validate(instance=output, schema=schema)
    except jsonschema.ValidationError as exc:
        return AssertionResult(
            passed=False,
            name="schema_faithful",
            detail=f"Schema validation failed: {exc.message}",
            tier="invariant",
        )

    allowed = set(schema.get("properties", {}).keys())
    extra = set(output.keys()) - allowed
    if extra:
        return AssertionResult(
            passed=False,
            name="schema_faithful",
            detail=f"Extra keys not in schema: {sorted(extra)}",
            tier="invariant",
        )

    for key, prop in schema.get("properties", {}).items():
        if prop.get("readOnly") and key in output and output[key] is not None:
            return AssertionResult(
                passed=False,
                name="schema_faithful",
                detail=f"readOnly field {key} is populated",
                tier="invariant",
            )

    if mode != "grounded":
        return AssertionResult(passed=True, name="schema_faithful", tier="invariant")

    required = set(schema.get("required", []))
    flat = _flatten_dict(output)
    declared_spans: dict[str, list[int]] = {}
    if trace:
        for fname, ft in trace.fields.items():
            if ft.source_span:
                declared_spans[fname] = [ft.source_span[0], ft.source_span[1]]

    for field_path, value in flat.items():
        top_key = field_path.split(".")[0].split("[")[0]
        is_required = top_key in required or field_path in required
        is_optional_populated = not is_required and value is not None

        if not is_required and not is_optional_populated:
            continue

        has_ev = field_has_evidence(field_path, value, input_text, declared_spans)
        if not has_ev:
            kind = "required" if is_required else "optional"
            return AssertionResult(
                passed=False,
                name="schema_faithful",
                detail=f"{kind} field {field_path} has no evidence in source input",
                tier="invariant",
            )

    return AssertionResult(passed=True, name="schema_faithful", tier="invariant")


def equivalence_preserved(class_name: str, suite: EvalSuite, output: dict[str, Any]) -> AssertionResult:
    from invarianteval.assertions.equivalence import check_equivalence

    return check_equivalence(class_name, suite, output)
