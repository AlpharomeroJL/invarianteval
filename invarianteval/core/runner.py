from __future__ import annotations

from collections.abc import Callable
from typing import Any

from invarianteval.assertions.registry import build_assertions
from invarianteval.core.models import CaseResult, Run, RunSummary
from invarianteval.core.provenance import ProvenanceDeriver
from invarianteval.core.suite import EvalSuite
from invarianteval.cost import aggregate_metrics
from invarianteval.providers.base import Provider, ProviderResult


def default_merge(provider_result: ProviderResult) -> tuple[dict[str, Any], dict[str, bool]]:
    """Default SUT merge: final output equals model parsed unless fixture provides override."""
    if provider_result.final_output is not None:
        return provider_result.final_output, provider_result.human_confirmed
    return provider_result.parsed or {}, provider_result.human_confirmed


class Runner:
    def __init__(
        self,
        suite: EvalSuite,
        provider: Provider,
        *,
        provider_mode: str = "fixture",
        merge_fn: Callable[[ProviderResult], tuple[dict[str, Any], dict[str, bool]]] | None = None,
    ) -> None:
        self.suite = suite
        self.provider = provider
        self.provider_mode = provider_mode
        self.merge_fn = merge_fn or default_merge
        self.deriver = ProvenanceDeriver()

    def run(self) -> Run:
        run = Run(
            suite_name=self.suite.name,
            run_id=Run.new_id(),
            started_at=Run.new_id(),
            provider_mode=self.provider_mode,
            seed=self.suite.seed,
            model=self.suite.model.name,
        )

        schema: dict[str, Any] | None = None
        schema_path = self.suite.schema_path()
        if schema_path and schema_path.exists():
            import json

            schema = json.loads(schema_path.read_text(encoding="utf-8"))

        for case in self.suite.cases:
            run.cases.append(self._run_case(case, schema))

        run.summary = RunSummary(metrics=aggregate_metrics(run.cases))
        return run

    def _run_case(self, case, schema: dict[str, Any] | None) -> CaseResult:
        input_path = case.input_path(self.suite.suite_dir)
        prompt = input_path.read_text(encoding="utf-8")

        provider_result = self.provider.complete(
            prompt,
            schema=schema,
            model=self.suite.model.name,
            seed=self.suite.seed,
            case_id=case.id,
        )

        final_output, human_confirmed = self.merge_fn(provider_result)
        model_parsed = provider_result.parsed or {}

        trace = self.deriver.derive(
            case_id=case.id,
            model_parsed=model_parsed,
            final_output=final_output,
            field_policies=self.suite.field_policies,
            human_confirmed=human_confirmed,
            confidence=provider_result.confidence,
            input_text=provider_result.case_input or prompt,
            source_spans=provider_result.source_spans,
        )

        expected: dict[str, Any] | None = None
        expected_path = case.expected_path(self.suite.suite_dir)
        if expected_path and expected_path.exists():
            import json

            expected = json.loads(expected_path.read_text(encoding="utf-8"))

        assertion_results = build_assertions(
            case.assertions,
            suite=self.suite,
            final_output=final_output,
            expected=expected,
            trace=trace,
            provider=self.provider,
            seed=self.suite.seed,
            input_text=prompt,
        )

        invariant_passed = all(r.passed for r in assertion_results if r.tier == "invariant")
        deterministic_passed = all(
            r.passed for r in assertion_results if r.tier == "deterministic"
        )
        judge_scores = [r.score for r in assertion_results if r.tier == "judge" and r.score is not None]
        judge_score = sum(judge_scores) / len(judge_scores) if judge_scores else None

        passed = invariant_passed and deterministic_passed

        return CaseResult(
            case_id=case.id,
            passed=passed,
            invariant_passed=invariant_passed,
            deterministic_passed=deterministic_passed,
            judge_score=judge_score,
            assertion_results=assertion_results,
            final_output=final_output,
            model_parsed=model_parsed,
            trace=trace.to_dict(),
            cost_usd=provider_result.cost_usd,
            latency_ms=provider_result.latency_ms,
            provider=provider_result.provider,
            model=provider_result.model,
        )
