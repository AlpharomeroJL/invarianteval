from __future__ import annotations

from typing import Any

from invarianteval.assertions import deterministic, invariants, judge
from invarianteval.core.case import AssertionSpec
from invarianteval.core.models import AssertionResult
from invarianteval.core.suite import EvalSuite
from invarianteval.core.trace import Trace
from invarianteval.providers.base import Provider


def build_assertions(
    specs: list[AssertionSpec],
    *,
    suite: EvalSuite,
    final_output: dict[str, Any],
    expected: dict[str, Any] | None,
    trace: Trace,
    provider: Provider,
    seed: int | None,
    input_text: str = "",
) -> list[AssertionResult]:
    results: list[AssertionResult] = []
    for spec in specs:
        results.append(
            _run_assertion(
                spec,
                suite=suite,
                final_output=final_output,
                expected=expected,
                trace=trace,
                provider=provider,
                seed=seed,
                input_text=input_text,
            )
        )
    return results


def _run_assertion(
    spec: AssertionSpec,
    *,
    suite: EvalSuite,
    final_output: dict[str, Any],
    expected: dict[str, Any] | None,
    trace: Trace,
    provider: Provider,
    seed: int | None,
    input_text: str,
) -> AssertionResult:
    name = spec.name
    params = spec.params

    if name == "schema_valid":
        schema_path = params.get("schema") or params.get("field") or params.get("value", "")
        return deterministic.schema_valid(schema_path, final_output, suite)
    if name == "schema_faithful":
        schema_path = params.get("schema") or params.get("field") or params.get("value", "")
        mode = params.get("mode", "envelope")
        return invariants.schema_faithful(
            schema_path,
            final_output,
            suite,
            mode=mode,
            input_text=input_text,
            trace=trace,
        )
    if name == "exact_match":
        field = params.get("field", params.get("value", ""))
        return deterministic.exact_match(field, expected, final_output)
    if name == "field_present":
        field = params.get("field", params.get("value", ""))
        return deterministic.field_present(field, final_output)
    if name == "regex":
        return deterministic.regex_match(params["field"], params["pattern"], final_output)
    if name == "numeric_range":
        return deterministic.numeric_range(
            params["field"],
            params.get("min"),
            params.get("max"),
            final_output,
        )
    if name == "never_auto_filled":
        field = params.get("field", params.get("value", ""))
        return invariants.never_auto_filled(field, trace)
    if name == "provenance_required":
        return invariants.provenance_required(
            params["field"],
            params.get("allowed", []),
            trace,
        )
    if name == "confidence_gated":
        return invariants.confidence_gated(
            params["field"],
            float(params.get("threshold", 0.8)),
            trace,
        )
    if name == "equivalence_preserved":
        class_name = params.get("class") or params.get("field") or params.get("value", "")
        return invariants.equivalence_preserved(class_name, suite, final_output)
    if name == "judged":
        judge_cfg = params.get("judge", {})
        return judge.judged(
            params.get("rubric", ""),
            suite.suite_dir,
            final_output,
            provider,
            judge_model=judge_cfg.get("name", suite.model.name),
            threshold=float(params.get("threshold", 0.7)),
            seed=seed,
        )

    return AssertionResult(
        passed=False,
        name=name,
        detail=f"Unknown assertion: {name}",
        tier="deterministic",
    )
