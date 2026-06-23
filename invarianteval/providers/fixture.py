from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from invarianteval.providers.base import ProviderResult


class FixtureProvider:
    """Replays recorded provider outputs for deterministic CI."""

    name = "fixture"

    def __init__(self, fixtures_dir: Path) -> None:
        self.fixtures_dir = fixtures_dir

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str = "",
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult:
        if not case_id:
            raise ValueError("FixtureProvider requires case_id")
        path = self.fixtures_dir / f"{case_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProviderResult(
            raw=data.get("raw", ""),
            parsed=data.get("model_parsed"),
            model=data.get("model", model),
            provider=data.get("provider", self.name),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            latency_ms=data.get("latency_ms", 0.0),
            cost_usd=data.get("cost_usd", 0.0),
            final_output=data.get("final_output"),
            human_confirmed=data.get("human_confirmed", {}),
            confidence=data.get("confidence", {}),
            source_spans=data.get("source_spans", {}),
            case_input=data.get("case_input") or prompt,
        )

    def health_check(self) -> bool:
        return self.fixtures_dir.is_dir()
