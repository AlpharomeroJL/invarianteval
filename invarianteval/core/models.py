from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssertionResult(BaseModel):
    passed: bool
    name: str
    detail: str | None = None
    score: float | None = None
    tier: Literal["deterministic", "invariant", "judge"] = "deterministic"


class CaseResult(BaseModel):
    case_id: str
    passed: bool
    invariant_passed: bool
    deterministic_passed: bool
    judge_score: float | None = None
    assertion_results: list[AssertionResult] = Field(default_factory=list)
    final_output: dict[str, Any] = Field(default_factory=dict)
    model_parsed: dict[str, Any] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    provider: str = ""
    model: str = ""


class RunMetrics(BaseModel):
    total_cases: int = 0
    passed_cases: int = 0
    invariant_pass_rate: float = 0.0
    deterministic_pass_rate: float = 0.0
    judge_score_mean: float | None = None
    cost_per_task_usd: float = 0.0
    latency_p95_ms: float = 0.0
    invariant_failures: int = 0


class RunSummary(BaseModel):
    metrics: RunMetrics
    baseline_warnings: list[str] = Field(default_factory=list)
    baseline_regressions: list[str] = Field(default_factory=list)


class Run(BaseModel):
    suite_name: str
    run_id: str
    started_at: str
    provider_mode: str
    seed: int | None = None
    model: str = ""
    cases: list[CaseResult] = Field(default_factory=list)
    summary: RunSummary | None = None

    @staticmethod
    def new_id() -> str:
        return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
