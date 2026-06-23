from __future__ import annotations

from collections.abc import Callable
from typing import Any

from invarianteval.core.models import AssertionResult


def wrap_deepeval_metric(metric_fn: Callable[..., Any], name: str = "deepeval") -> Callable[..., AssertionResult]:
    def _run(*args: Any, **kwargs: Any) -> AssertionResult:
        try:
            result = metric_fn(*args, **kwargs)
            score = float(getattr(result, "score", result))
            passed = bool(getattr(result, "success", score >= 0.7))
            return AssertionResult(
                passed=passed,
                name=name,
                detail=str(getattr(result, "reason", "")),
                score=score,
                tier="judge",
            )
        except ImportError as exc:
            return AssertionResult(
                passed=False,
                name=name,
                detail=f"deepeval not installed: {exc}",
                tier="judge",
                score=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            return AssertionResult(
                passed=False,
                name=name,
                detail=str(exc),
                tier="judge",
                score=0.0,
            )

    return _run
