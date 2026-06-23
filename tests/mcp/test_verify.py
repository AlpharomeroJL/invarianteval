from __future__ import annotations

import json
from pathlib import Path

import pytest

from invarianteval.mcp.verify import check_invariants

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "examples/fire-inspection-extraction/suite.yaml"
GOOD = ROOT / "examples/fire-inspection-extraction/fixtures/good/panel-001.json"
REGRESSED = ROOT / "examples/fire-inspection-extraction/fixtures/regressed/panel-001.json"
PANEL_001_INPUT = ROOT / "examples/fire-inspection-extraction/data/2026-06-23/panel-001.txt"


def _load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.mcp
def test_check_invariants_good_panel_001() -> None:
    fx = _load_fixture(GOOD)
    case_input = PANEL_001_INPUT.read_text(encoding="utf-8")
    result = check_invariants(
        suite_path=str(SUITE),
        model_parsed=fx["model_parsed"],
        final_output=fx["final_output"],
        human_confirmed=fx.get("human_confirmed"),
        case_input=case_input,
    )
    assert result["passed"] is True
    assert result["invariant_passed"] is True
    assert result["failures"] == []


@pytest.mark.mcp
def test_check_invariants_regressed_panel_001() -> None:
    fx = _load_fixture(REGRESSED)
    case_input = PANEL_001_INPUT.read_text(encoding="utf-8")
    result = check_invariants(
        suite_path=str(SUITE),
        model_parsed=fx["model_parsed"],
        final_output=fx["final_output"],
        human_confirmed=fx.get("human_confirmed"),
        case_input=case_input,
    )
    assert result["passed"] is False
    assert result["invariant_passed"] is False
    assert any("never_auto_filled" in f["name"] for f in result["failures"])
