from __future__ import annotations

from typing import Any

from invarianteval.assertions.registry import build_assertions
from invarianteval.core.provenance import ProvenanceDeriver
from invarianteval.mcp._policy import collect_invariant_specs, load_suite_for_check
from invarianteval.mcp._stub import StubProvider


def check_invariants(
    *,
    suite_path: str | None = None,
    policy: dict[str, Any] | None = None,
    model_parsed: dict[str, Any],
    final_output: dict[str, Any],
    human_confirmed: dict[str, bool] | None = None,
    case_input: str = "",
) -> dict[str, Any]:
    suite = load_suite_for_check(suite_path, policy)
    specs = collect_invariant_specs(suite)
    if not specs:
        return {
            "passed": True,
            "invariant_passed": True,
            "failures": [],
            "detail": "No invariant-tier assertions declared in suite",
        }

    trace = ProvenanceDeriver().derive(
        case_id="mcp-check",
        model_parsed=model_parsed,
        final_output=final_output,
        field_policies=suite.field_policies,
        human_confirmed=human_confirmed,
        input_text=case_input,
    )

    results = build_assertions(
        specs,
        suite=suite,
        final_output=final_output,
        expected=None,
        trace=trace,
        provider=StubProvider(),
        seed=suite.seed,
        input_text=case_input,
    )

    invariant_results = [r for r in results if r.tier == "invariant"]
    failures = [
        {"name": r.name, "detail": r.detail, "tier": r.tier}
        for r in invariant_results
        if not r.passed
    ]
    invariant_passed = all(r.passed for r in invariant_results)
    return {
        "passed": invariant_passed,
        "invariant_passed": invariant_passed,
        "failures": failures,
    }
