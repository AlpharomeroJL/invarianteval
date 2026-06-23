from __future__ import annotations

from pathlib import Path

from invarianteval.assertions.invariants import never_auto_filled
from invarianteval.core.provenance import ProvenanceDeriver
from invarianteval.core.runner import Runner
from invarianteval.core.suite import load_suite
from invarianteval.providers.base import FieldPolicy
from invarianteval.providers.fixture import FixtureProvider

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "fire-inspection-extraction"


def test_never_auto_filled_invariant() -> None:
    deriver = ProvenanceDeriver()
    trace = deriver.derive(
        "panel-001",
        model_parsed={"pass_fail_result": "pass"},
        final_output={"pass_fail_result": "pass"},
        field_policies={"pass_fail_result": FieldPolicy.locked},
    )
    result = never_auto_filled("pass_fail_result", trace)
    assert not result.passed
    assert "model-originated" in (result.detail or "")


def test_good_fixtures_pass() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    provider = FixtureProvider(EXAMPLE / "fixtures" / "good")
    runner = Runner(suite, provider, provider_mode="fixture")
    run = runner.run()
    assert run.summary is not None
    assert run.summary.metrics.invariant_failures == 0
    assert run.summary.metrics.invariant_pass_rate == 1.0


def test_regressed_fixtures_fail() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    provider = FixtureProvider(EXAMPLE / "fixtures" / "regressed")
    runner = Runner(suite, provider, provider_mode="fixture")
    run = runner.run()
    assert run.summary is not None
    assert run.summary.metrics.invariant_failures >= 1
    panel = next(c for c in run.cases if c.case_id == "panel-001")
    assert not panel.invariant_passed


def test_schema_faithful_extra_keys() -> None:
    from invarianteval.assertions.invariants import schema_faithful

    suite = load_suite(EXAMPLE / "suite.yaml")
    output = {"panel_model": "X", "device_status": "ok", "hallucinated_field": "bad"}
    result = schema_faithful("expected/schema.json", output, suite)
    assert not result.passed
    assert "hallucinated_field" in (result.detail or "") or "Extra keys" in (result.detail or "")


def test_equivalence_preserved() -> None:
    from invarianteval.assertions.invariants import equivalence_preserved

    suite = load_suite(EXAMPLE / "suite.yaml")
    output = {
        "devices": [
            {"device_id": "1", "model_family": "XF-200"},
            {"device_id": "2", "model_family": "XF-200"},
        ]
    }
    result = equivalence_preserved("panel_family", suite, output)
    assert result.passed

    broken = {
        "devices": [
            {"device_id": "1", "model_family": "XF-200"},
            {"device_id": "2", "model_family": "OTHER"},
        ]
    }
    result2 = equivalence_preserved("panel_family", suite, broken)
    assert not result2.passed
