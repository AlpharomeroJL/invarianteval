from __future__ import annotations

from pathlib import Path

from invarianteval.assertions.deterministic import (
    exact_match,
    field_present,
    numeric_range,
    regex_match,
    schema_valid,
)
from invarianteval.core.suite import load_suite

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "fire-inspection-extraction"


def test_deterministic_assertions() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    output = {"panel_model": "ABC-100", "device_status": "operational"}
    expected = {"panel_model": "ABC-100", "device_status": "operational"}

    assert schema_valid("expected/schema.json", {"panel_model": "ABC-100"}, suite).passed is False
    assert field_present("panel_model", output).passed
    assert exact_match("panel_model", expected, output).passed
    assert regex_match("panel_model", r"ABC-\d+", output).passed
    assert numeric_range("panel_model", 0, 100, {"count": 5}).passed is False
