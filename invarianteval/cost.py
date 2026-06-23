from __future__ import annotations

from invarianteval.core.models import CaseResult, Run, RunMetrics


def aggregate_metrics(cases: list[CaseResult]) -> RunMetrics:
    if not cases:
        return RunMetrics()

    total = len(cases)
    passed = sum(1 for c in cases if c.passed)
    invariant_passed = sum(1 for c in cases if c.invariant_passed)
    deterministic_passed = sum(1 for c in cases if c.deterministic_passed)

    invariant_failures = sum(
        1
        for c in cases
        for r in c.assertion_results
        if r.tier == "invariant" and not r.passed
    )

    judge_scores = [c.judge_score for c in cases if c.judge_score is not None]
    judge_mean = sum(judge_scores) / len(judge_scores) if judge_scores else None

    costs = [c.cost_usd for c in cases]
    latencies = sorted(c.latency_ms for c in cases)
    p95_idx = min(len(latencies) - 1, int(len(latencies) * 0.95))

    return RunMetrics(
        total_cases=total,
        passed_cases=passed,
        invariant_pass_rate=invariant_passed / total,
        deterministic_pass_rate=deterministic_passed / total,
        judge_score_mean=judge_mean,
        cost_per_task_usd=sum(costs) / total,
        latency_p95_ms=latencies[p95_idx] if latencies else 0.0,
        invariant_failures=invariant_failures,
    )


def summarize_run(run: Run) -> str:
    if not run.summary:
        return "No summary"
    m = run.summary.metrics
    lines = [
        f"Suite: {run.suite_name}",
        f"Cases: {m.passed_cases}/{m.total_cases} passed",
        f"Invariant pass rate: {m.invariant_pass_rate:.1%}",
        f"Deterministic pass rate: {m.deterministic_pass_rate:.1%}",
        f"Invariant failures: {m.invariant_failures}",
    ]
    if m.judge_score_mean is not None:
        lines.append(f"Judge score (informational): {m.judge_score_mean:.2f}")
    lines.append(f"Cost per task: ${m.cost_per_task_usd:.4f}")
    lines.append(f"Latency p95: {m.latency_p95_ms:.0f}ms")
    return "\n".join(lines)
