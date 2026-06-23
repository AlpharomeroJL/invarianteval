from __future__ import annotations

import json
import time
from typing import Any

import httpx

from invarianteval.providers.base import ProviderResult


class OllamaProvider:
    """Local Ollama provider with native structured output via format=."""

    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str,
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {},
        }
        if seed is not None:
            payload["options"]["seed"] = seed
        if schema is not None:
            payload["format"] = schema

        start = time.perf_counter()
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
        latency_ms = (time.perf_counter() - start) * 1000

        raw = body.get("message", {}).get("content", "")
        parsed: dict[str, Any] | None = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None

        prompt_tokens = body.get("prompt_eval_count", 0)
        output_tokens = body.get("eval_count", 0)

        return ProviderResult(
            raw=raw,
            parsed=parsed,
            model=model,
            provider=self.name,
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=0.0,
        )

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
