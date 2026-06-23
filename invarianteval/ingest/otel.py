from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ATTR_MODEL = "invarianteval.model_parsed"
ATTR_FINAL = "invarianteval.final_output"
ATTR_CONFIRMED = "invarianteval.human_confirmed"
ATTR_INPUT = "invarianteval.case_input"
ATTR_SPANS = "invarianteval.source_spans"
ATTR_CASE_ID = "invarianteval.case_id"


def _parse_attr(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _extract_spans(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if "attributes" in doc:
        return [doc]
    spans: list[dict[str, Any]] = []
    for rs in doc.get("resourceSpans", []):
        for ss in rs.get("scopeSpans", []):
            spans.extend(ss.get("spans", []))
    return spans


def span_to_fixture(span: dict[str, Any], fallback_id: str) -> dict[str, Any]:
    attrs = span.get("attributes", {})
    case_id = _parse_attr(attrs.get(ATTR_CASE_ID)) or span.get("name") or fallback_id
    return {
        "model_parsed": _parse_attr(attrs.get(ATTR_MODEL)) or {},
        "final_output": _parse_attr(attrs.get(ATTR_FINAL)) or {},
        "human_confirmed": _parse_attr(attrs.get(ATTR_CONFIRMED)) or {},
        "source_spans": _parse_attr(attrs.get(ATTR_SPANS)) or {},
        "case_input": _parse_attr(attrs.get(ATTR_INPUT)) or "",
        "raw": json.dumps(_parse_attr(attrs.get(ATTR_MODEL)) or {}),
        "model": attrs.get("invarianteval.model", "unknown"),
        "provider": attrs.get("invarianteval.provider", "otel"),
        "input_tokens": int(attrs.get("invarianteval.input_tokens", 0)),
        "output_tokens": int(attrs.get("invarianteval.output_tokens", 0)),
        "latency_ms": float(attrs.get("invarianteval.latency_ms", 0)),
        "cost_usd": float(attrs.get("invarianteval.cost_usd", 0)),
        "_case_id": str(case_id),
    }


def load_spans(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    all_spans: list[dict[str, Any]] = []
    if text.startswith("["):
        for doc in json.loads(text):
            all_spans.extend(_extract_spans(doc))
    else:
        for line in text.splitlines():
            line = line.strip()
            if line:
                all_spans.extend(_extract_spans(json.loads(line)))
    return all_spans


def ingest_otel_file(path: Path, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    case_ids: list[str] = []
    for idx, span in enumerate(load_spans(path)):
        fixture = span_to_fixture(span, f"trace-{idx:04d}")
        case_id = fixture.pop("_case_id")
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_id)
        (out_dir / f"{safe_id}.json").write_text(json.dumps(fixture, indent=2), encoding="utf-8")
        case_ids.append(safe_id)
    return case_ids
