from __future__ import annotations

from typing import Any

from invarianteval.providers.base import Provider, ProviderResult


class FallbackProvider:
    """Routes to the first healthy provider in an ordered list."""

    name = "fallback"

    def __init__(self, providers: list[Provider]) -> None:
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider")
        self.providers = providers

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str,
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult:
        last_error: Exception | None = None
        for provider in self.providers:
            if not provider.health_check():
                continue
            try:
                return provider.complete(
                    prompt,
                    schema=schema,
                    model=model,
                    seed=seed,
                    case_id=case_id,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        msg = f"All providers failed: {last_error}"
        raise RuntimeError(msg)

    def health_check(self) -> bool:
        return any(p.health_check() for p in self.providers)
