from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from invarianteval.providers.base import ProviderResult

# Approximate pricing for gpt-4o-mini (USD per 1M tokens)
_INPUT_COST_PER_M = 0.15
_OUTPUT_COST_PER_M = 0.60


class OpenAIProvider:
    """Opt-in cloud fallback provider."""

    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str = "gpt-4o-mini",
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI provider")

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if seed is not None:
            payload["seed"] = seed
        if schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "output", "schema": schema, "strict": True},
            }

        start = time.perf_counter()
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        latency_ms = (time.perf_counter() - start) * 1000

        raw = body["choices"][0]["message"]["content"]
        parsed: dict[str, Any] | None = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None

        usage = body.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = (input_tokens * _INPUT_COST_PER_M + output_tokens * _OUTPUT_COST_PER_M) / 1_000_000

        return ProviderResult(
            raw=raw,
            parsed=parsed,
            model=model,
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
        )

    def health_check(self) -> bool:
        return bool(self.api_key)
