from __future__ import annotations

from pathlib import Path

from invarianteval.assertions.invariants import schema_faithful
from invarianteval.core.provenance import ProvenanceDeriver
from invarianteval.core.suite import load_suite
from invarianteval.providers.base import FieldPolicy

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "fire-inspection-extraction"


def test_schema_grounded_required_field_missing_evidence() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    input_text = "Some unrelated text without panel model"
    output = {"panel_model": "ABC-100", "device_status": "operational"}
    deriver = ProvenanceDeriver()
    trace = deriver.derive(
        "t",
        {},
        output,
        {"panel_model": FieldPolicy.model_allowed, "device_status": FieldPolicy.locked},
        input_text=input_text,
    )
    result = schema_faithful(
        "expected/schema.json",
        output,
        suite,
        mode="grounded",
        input_text=input_text,
        trace=trace,
    )
    assert not result.passed
    assert "no evidence" in (result.detail or "")


def test_schema_grounded_hallucinated_optional() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    input_text = "Panel ABC-100 device operational"
    output = {
        "panel_model": "ABC-100",
        "device_status": "operational",
        "notes": "Hallucinated note not in source",
    }
    deriver = ProvenanceDeriver()
    trace = deriver.derive("t", output, output, {}, input_text=input_text)
    result = schema_faithful(
        "expected/schema.json",
        output,
        suite,
        mode="grounded",
        input_text=input_text,
        trace=trace,
    )
    assert not result.passed


def test_schema_grounded_passes_with_evidence() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    input_text = "Panel ABC-100 device operational status"
    output = {"panel_model": "ABC-100", "device_status": "operational"}
    deriver = ProvenanceDeriver()
    trace = deriver.derive("t", {"panel_model": "ABC-100"}, output, {}, input_text=input_text)
    result = schema_faithful(
        "expected/schema.json",
        output,
        suite,
        mode="grounded",
        input_text=input_text,
        trace=trace,
    )
    assert result.passed
