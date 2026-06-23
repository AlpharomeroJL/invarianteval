from __future__ import annotations

from typing import Any

from invarianteval.core.models import AssertionResult
from invarianteval.core.provenance import _flatten_dict
from invarianteval.core.suite import EquivalenceClass, EvalSuite


def _resolve_path(output: dict[str, Any], path: str) -> Any:
    flat = _flatten_dict(output)
    return flat.get(path)


def check_equivalence(
    class_name: str,
    suite: EvalSuite,
    output: dict[str, Any],
) -> AssertionResult:
    eq_class = suite.equivalence_classes.get(class_name)
    if eq_class is None:
        return AssertionResult(
            passed=False,
            name=f"equivalence_preserved[{class_name}]",
            detail=f"Unknown equivalence class: {class_name}",
            tier="invariant",
        )

    rule = eq_class.rule
    if rule == "equal":
        return _check_equal(class_name, eq_class, output)
    if rule == "one_of":
        return _check_one_of(class_name, eq_class, output)
    if rule == "implies":
        return _check_implies(class_name, eq_class, output)
    if rule == "numeric_tolerance":
        return _check_numeric_tolerance(class_name, eq_class, output)

    return AssertionResult(
        passed=False,
        name=f"equivalence_preserved[{class_name}]",
        detail=f"Unsupported rule: {rule}",
        tier="invariant",
    )


def _check_equal(class_name: str, eq_class: EquivalenceClass, output: dict[str, Any]) -> AssertionResult:
    values = [_resolve_path(output, f) for f in eq_class.fields]
    if any(v is None for v in values):
        missing = [f for f, v in zip(eq_class.fields, values, strict=True) if v is None]
        return AssertionResult(
            passed=False,
            name=f"equivalence_preserved[{class_name}]",
            detail=f"Missing fields: {missing}",
            tier="invariant",
        )
    ok = len(set(str(v) for v in values)) == 1
    return AssertionResult(
        passed=ok,
        name=f"equivalence_preserved[{class_name}]",
        detail=None if ok else f"Values differ: {dict(zip(eq_class.fields, values, strict=True))}",
        tier="invariant",
    )


def _check_one_of(class_name: str, eq_class: EquivalenceClass, output: dict[str, Any]) -> AssertionResult:
    groups = eq_class.groups or []
    values = [_resolve_path(output, f) for f in eq_class.fields]
    if any(v is None for v in values):
        missing = [f for f, v in zip(eq_class.fields, values, strict=True) if v is None]
        return AssertionResult(
            passed=False,
            name=f"equivalence_preserved[{class_name}]",
            detail=f"Missing fields: {missing}",
            tier="invariant",
        )
    for group in groups:
        if all(str(v) in [str(x) for x in group] for v in values):
            return AssertionResult(
                passed=True,
                name=f"equivalence_preserved[{class_name}]",
                tier="invariant",
            )
    return AssertionResult(
        passed=False,
        name=f"equivalence_preserved[{class_name}]",
        detail=f"Values {values} not in same group from {groups}",
        tier="invariant",
    )


def _check_implies(class_name: str, eq_class: EquivalenceClass, output: dict[str, Any]) -> AssertionResult:
    if len(eq_class.fields) < 2:
        return AssertionResult(
            passed=False,
            name=f"equivalence_preserved[{class_name}]",
            detail="implies requires at least 2 fields",
            tier="invariant",
        )
    source_field, target_field = eq_class.fields[0], eq_class.fields[1]
    source_val = _resolve_path(output, source_field)
    target_val = _resolve_path(output, target_field)
    mapping = eq_class.mapping or {}
    if source_val is None:
        return AssertionResult(passed=True, name=f"equivalence_preserved[{class_name}]", tier="invariant")
    expected = mapping.get(str(source_val))
    if expected is None:
        return AssertionResult(
            passed=False,
            name=f"equivalence_preserved[{class_name}]",
            detail=f"No mapping for {source_field}={source_val!r}",
            tier="invariant",
        )
    ok = str(target_val) == str(expected)
    return AssertionResult(
        passed=ok,
        name=f"equivalence_preserved[{class_name}]",
        detail=None if ok else f"Expected {target_field}={expected!r}, got {target_val!r}",
        tier="invariant",
    )


def _check_numeric_tolerance(
    class_name: str, eq_class: EquivalenceClass, output: dict[str, Any]
) -> AssertionResult:
    tolerance = eq_class.tolerance if eq_class.tolerance is not None else 0.0
    values = []
    for f in eq_class.fields:
        v = _resolve_path(output, f)
        if v is None:
            return AssertionResult(
                passed=False,
                name=f"equivalence_preserved[{class_name}]",
                detail=f"Missing field: {f}",
                tier="invariant",
            )
        try:
            values.append(float(v))
        except (TypeError, ValueError):
            return AssertionResult(
                passed=False,
                name=f"equivalence_preserved[{class_name}]",
                detail=f"Non-numeric value at {f}: {v!r}",
                tier="invariant",
            )
    if not values:
        return AssertionResult(passed=True, name=f"equivalence_preserved[{class_name}]", tier="invariant")
    ref = values[0]
    ok = all(abs(v - ref) <= tolerance for v in values)
    return AssertionResult(
        passed=ok,
        name=f"equivalence_preserved[{class_name}]",
        detail=None if ok else f"Values exceed tolerance {tolerance}: {values}",
        tier="invariant",
    )
