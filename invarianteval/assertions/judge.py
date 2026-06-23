from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from invarianteval.core.models import AssertionResult
from invarianteval.providers.base import Provider


def judged(
    rubric_path: str,
    suite_dir: Path,
    output: dict[str, Any],
    provider: Provider,
    judge_model: str,
    threshold: float = 0.7,
    seed: int | None = None,
) -> AssertionResult:
    """LLM-as-judge — supporting signal only, never sole CI blocker."""
    rubric_file = suite_dir / rubric_path
    rubric = rubric_file.read_text(encoding="utf-8")

    prompt = f"""You are an evaluation judge. Score the output against the rubric.

Rubric:
{rubric}

Output to evaluate:
{json.dumps(output, indent=2)}

Respond with JSON only: {{"score": 0.0-1.0, "explanation": "..."}}
"""
    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "number"},
            "explanation": {"type": "string"},
        },
        "required": ["score", "explanation"],
    }

    try:
        result = provider.complete(prompt, schema=schema, model=judge_model, seed=seed)
        parsed = json.loads(result.raw) if result.raw else {}
        score = float(parsed.get("score", 0.0))
        explanation = parsed.get("explanation", "")
        passed = score >= threshold
        return AssertionResult(
            passed=passed,
            name="judged",
            detail=explanation,
            score=score,
            tier="judge",
        )
    except Exception as exc:  # noqa: BLE001
        return AssertionResult(
            passed=False,
            name="judged",
            detail=f"Judge failed: {exc}",
            score=0.0,
            tier="judge",
        )
