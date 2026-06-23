from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from invarianteval.assertions.judge import judged
from invarianteval.core.models import Run, RunMetrics, RunSummary
from invarianteval.providers.base import ProviderResult
from invarianteval.report import render_report


class MockJudgeProvider:
    name = "mock"

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str = "",
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult:
        return ProviderResult(
            raw=json.dumps({"score": 0.85, "explanation": "Good extraction"}),
            parsed={"score": 0.85, "explanation": "Good extraction"},
            model="mock",
            provider="mock",
        )

    def health_check(self) -> bool:
        return True


def test_judged_supporting_signal(tmp_path: Path) -> None:
    rubric = tmp_path / "rubric.md"
    rubric.write_text("Score completeness of extraction.", encoding="utf-8")
    result = judged(
        "rubric.md",
        tmp_path,
        {"panel_model": "ABC"},
        MockJudgeProvider(),  # type: ignore[arg-type]
        judge_model="mock",
    )
    assert result.tier == "judge"
    assert result.score == 0.85


def test_render_report(tmp_path: Path) -> None:
    run = Run(
        suite_name="test",
        run_id="test-run",
        started_at="2026-01-01T00:00:00Z",
        provider_mode="fixture",
        summary=RunSummary(metrics=RunMetrics(total_cases=1, passed_cases=1)),
        cases=[],
    )
    out = tmp_path / "report.html"
    render_report(run, out)
    assert "InvariantEval Report" in out.read_text(encoding="utf-8")
