from __future__ import annotations

from invarianteval.core.evidence import field_has_evidence, find_evidence
from invarianteval.core.provenance import ProvenanceDeriver
from invarianteval.providers.base import FieldPolicy


def test_find_evidence_substring() -> None:
    text = "Panel model ABC-100 is operational"
    ok, ev, span = find_evidence("panel_model", "ABC-100", text)
    assert ok
    assert ev is not None
    assert span is not None


def test_find_evidence_declared_span() -> None:
    text = "Panel ABC-100 status ok"
    ok, ev, span = find_evidence(
        "panel_model",
        "ABC-100",
        text,
        {"panel_model": [6, 13]},
    )
    assert ok
    assert ev == "ABC-100"


def test_deriver_populates_evidence() -> None:
    deriver = ProvenanceDeriver()
    input_text = "Device status operational for panel ABC-100"
    trace = deriver.derive(
        "t1",
        {"panel_model": "ABC-100"},
        {"panel_model": "ABC-100", "device_status": "operational"},
        {"panel_model": FieldPolicy.model_allowed, "device_status": FieldPolicy.locked},
        input_text=input_text,
    )
    assert trace.field("panel_model") is not None
    assert trace.field("panel_model").evidence_text is not None
    assert trace.field("device_status") is not None
    assert field_has_evidence("device_status", "operational", input_text)
