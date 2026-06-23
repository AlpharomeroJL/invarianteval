from __future__ import annotations

import re
from typing import Any


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def value_in_text(value: Any, input_text: str) -> tuple[bool, str | None, tuple[int, int] | None]:
    """Deterministic substring grounding (no NLP)."""
    if value is None:
        return False, None, None
    text = str(value)
    if not text:
        return False, None, None
    norm_input = normalize_text(input_text)
    norm_value = normalize_text(text)
    idx = norm_input.find(norm_value)
    if idx == -1:
        return False, None, None
    # Map back to approximate char span in original (best-effort for portfolio)
    raw_idx = input_text.lower().find(text.lower())
    if raw_idx == -1:
        raw_idx = idx
    end = raw_idx + len(text)
    return True, text, (raw_idx, end)


def span_contains_value(
    span: tuple[int, int],
    value: Any,
    input_text: str,
) -> tuple[bool, str | None]:
    start, end = span
    if start < 0 or end > len(input_text) or start >= end:
        return False, None
    snippet = input_text[start:end]
    text = str(value)
    if normalize_text(text) in normalize_text(snippet):
        return True, snippet
    return False, None


def find_evidence(
    field: str,
    value: Any,
    input_text: str,
    declared_spans: dict[str, list[int]] | None = None,
) -> tuple[bool, str | None, tuple[int, int] | None]:
    declared_spans = declared_spans or {}
    if field in declared_spans:
        span_list = declared_spans[field]
        if len(span_list) == 2:
            span = (int(span_list[0]), int(span_list[1]))
            ok, snippet = span_contains_value(span, value, input_text)
            if ok:
                return True, snippet, span
    return value_in_text(value, input_text)


def field_has_evidence(
    field: str,
    value: Any,
    input_text: str,
    declared_spans: dict[str, list[int]] | None = None,
) -> bool:
    ok, _, _ = find_evidence(field, value, input_text, declared_spans)
    return ok
