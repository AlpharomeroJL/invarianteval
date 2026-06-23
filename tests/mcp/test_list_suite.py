from __future__ import annotations

from pathlib import Path

import pytest

from invarianteval.mcp.list_suite import list_invariants

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "examples/fire-inspection-extraction/suite.yaml"


@pytest.mark.mcp
def test_list_invariants_fire_suite() -> None:
    result = list_invariants(str(SUITE))
    assert result["name"] == "fire-inspection-extraction"
    assert "pass_fail_result" in result["field_policies"]
    assert result["field_policies"]["pass_fail_result"] == "locked"
    assert "panel_family" in result["equivalence_classes"]
    panel_001 = next(c for c in result["cases"] if c["id"] == "panel-001")
    names = {a["name"] for a in panel_001["assertions"]}
    assert "never_auto_filled" in names
    assert "provenance_required" in names
