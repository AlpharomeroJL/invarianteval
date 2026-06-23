from __future__ import annotations

from typing import Any

from invarianteval.providers.base import ProviderResult


class StubProvider:
    """Provider stub for invariant-only checks (no live model calls)."""

    name = "stub"

    def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        model: str,
        seed: int | None = None,
        case_id: str | None = None,
    ) -> ProviderResult:
        del prompt, schema, model, seed, case_id
        return ProviderResult(raw="", parsed={}, model="stub", provider=self.name)

    def health_check(self) -> bool:
        return False
