from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from invarianteval.core.models import Run, RunMetrics


def load_baseline(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_baseline(path: Path, metrics: RunMetrics, suite_name: str) -> None:
    payload = {
        "suite_name": suite_name,
        "metrics": metrics.model_dump(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def compare_baseline(
    run: Run,
    baseline_path: Path,
    *,
    judge_margin: float = 0.1,
) -> tuple[list[str], list[str]]:
    """Return (hard_regressions, warnings). Invariant failures are hard; judge is warn-only."""
    regressions: list[str] = []
    warnings: list[str] = []

    if not run.summary:
        return regressions, warnings

    metrics = run.summary.metrics

    if metrics.invariant_failures > 0:
        regressions.append(
            f"Invariant failures: {metrics.invariant_failures} "
            f"(pass rate {metrics.invariant_pass_rate:.1%})"
        )

    if not baseline_path.exists():
        warnings.append("No baseline file found; skipping metric comparison")
        return regressions, warnings

    baseline = load_baseline(baseline_path)
    base_metrics = RunMetrics(**baseline.get("metrics", {}))

    if metrics.deterministic_pass_rate < base_metrics.deterministic_pass_rate:
        regressions.append(
            f"Deterministic pass rate regressed: "
            f"{base_metrics.deterministic_pass_rate:.1%} -> {metrics.deterministic_pass_rate:.1%}"
        )

    if (
        metrics.judge_score_mean is not None
        and base_metrics.judge_score_mean is not None
        and base_metrics.judge_score_mean - metrics.judge_score_mean > judge_margin
    ):
        warnings.append(
            f"Judge score dropped: {base_metrics.judge_score_mean:.2f} -> "
            f"{metrics.judge_score_mean:.2f} (margin {judge_margin})"
        )

    if metrics.cost_per_task_usd > base_metrics.cost_per_task_usd * 1.5:
        warnings.append(
            f"Cost per task increased: ${base_metrics.cost_per_task_usd:.4f} -> "
            f"${metrics.cost_per_task_usd:.4f}"
        )

    if metrics.latency_p95_ms > base_metrics.latency_p95_ms * 1.5:
        warnings.append(
            f"Latency p95 increased: {base_metrics.latency_p95_ms:.0f}ms -> "
            f"{metrics.latency_p95_ms:.0f}ms"
        )

    return regressions, warnings
