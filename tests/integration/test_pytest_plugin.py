import pytest


@pytest.mark.invarianteval(
    suite="examples/fire-inspection-extraction/suite.yaml",
    case_id="panel-001",
    fixtures="examples/fire-inspection-extraction/fixtures/good",
)
def test_panel_001_invariants() -> None:
    """Marker drives invariant check in plugin hook."""
    pass
