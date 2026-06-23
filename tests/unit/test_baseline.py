from __future__ import annotations

from pathlib import Path

from invarianteval.core.baseline import compare_baseline
from invarianteval.core.runner import Runner
from invarianteval.core.suite import load_suite
from invarianteval.providers.fixture import FixtureProvider

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "fire-inspection-extraction"


def test_baseline_compare_regressed() -> None:
    suite = load_suite(EXAMPLE / "suite.yaml")
    provider = FixtureProvider(EXAMPLE / "fixtures" / "regressed")
    run = Runner(suite, provider, provider_mode="fixture").run()
    regressions, warnings = compare_baseline(run, EXAMPLE / "baseline.json")
    assert len(regressions) >= 1
