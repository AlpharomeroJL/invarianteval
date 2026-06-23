from __future__ import annotations

import json
import re
from typing import Any

import jsonschema

from invarianteval.core.models import AssertionResult
from invarianteval.core.provenance import _flatten_dict
from invarianteval.core.suite import EvalSuite


def schema_valid(schema_path: str, output: dict[str, Any], suite: EvalSuite) -> AssertionResult:
    path = suite.suite_dir / schema_path
    schema = json.loads(path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=output, schema=schema)
        return AssertionResult(passed=True, name="schema_valid", tier="deterministic")
    except jsonschema.ValidationError as exc:
        return AssertionResult(
            passed=False,
            name="schema_valid",
            detail=str(exc.message),
            tier="deterministic",
        )


def exact_match(
    field: str, expected: dict[str, Any] | None, output: dict[str, Any]
) -> AssertionResult:
    flat = _flatten_dict(output)
    if expected is None:
        return AssertionResult(
            passed=False,
            name=f"exact_match[{field}]",
            detail="No expected output provided",
            tier="deterministic",
        )
    flat_expected = _flatten_dict(expected)
    if field not in flat_expected:
        return AssertionResult(
            passed=False,
            name=f"exact_match[{field}]",
            detail=f"Field {field} not in expected",
            tier="deterministic",
        )
    ok = flat.get(field) == flat_expected[field]
    return AssertionResult(
        passed=ok,
        name=f"exact_match[{field}]",
        detail=None if ok else f"expected {flat_expected[field]!r}, got {flat.get(field)!r}",
        tier="deterministic",
    )


def field_present(field: str, output: dict[str, Any]) -> AssertionResult:
    flat = _flatten_dict(output)
    ok = field in flat and flat[field] is not None
    return AssertionResult(
        passed=ok,
        name=f"field_present[{field}]",
        detail=None if ok else f"Field {field} missing or null",
        tier="deterministic",
    )


def regex_match(field: str, pattern: str, output: dict[str, Any]) -> AssertionResult:
    flat = _flatten_dict(output)
    value = flat.get(field)
    if value is None:
        return AssertionResult(
            passed=False,
            name=f"regex[{field}]",
            detail=f"Field {field} missing",
            tier="deterministic",
        )
    ok = bool(re.match(pattern, str(value)))
    return AssertionResult(
        passed=ok,
        name=f"regex[{field}]",
        detail=None if ok else f"Value {value!r} does not match {pattern!r}",
        tier="deterministic",
    )


def numeric_range(
    field: str,
    min_value: float | None,
    max_value: float | None,
    output: dict[str, Any],
) -> AssertionResult:
    flat = _flatten_dict(output)
    value = flat.get(field)
    if value is None:
        return AssertionResult(
            passed=False,
            name=f"numeric_range[{field}]",
            detail=f"Field {field} missing",
            tier="deterministic",
        )
    try:
        num = float(value)
    except (TypeError, ValueError):
        return AssertionResult(
            passed=False,
            name=f"numeric_range[{field}]",
            detail=f"Field {field} is not numeric: {value!r}",
            tier="deterministic",
        )
    if min_value is not None and num < min_value:
        return AssertionResult(
            passed=False,
            name=f"numeric_range[{field}]",
            detail=f"{num} < min {min_value}",
            tier="deterministic",
        )
    if max_value is not None and num > max_value:
        return AssertionResult(
            passed=False,
            name=f"numeric_range[{field}]",
            detail=f"{num} > max {max_value}",
            tier="deterministic",
        )
    return AssertionResult(passed=True, name=f"numeric_range[{field}]", tier="deterministic")
