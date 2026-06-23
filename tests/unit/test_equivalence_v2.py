from __future__ import annotations

from pathlib import Path

from invarianteval.assertions.equivalence import check_equivalence
from invarianteval.core.suite import EquivalenceClass, EvalSuite

ROOT = Path(__file__).resolve().parents[2]


def _suite(**classes) -> EvalSuite:
    return EvalSuite(
        name="test",
        equivalence_classes=classes,
        suite_dir=ROOT / "examples" / "fire-inspection-extraction",
    )


def test_implies_rule() -> None:
    suite = _suite(
        status_implies_pass=EquivalenceClass(
            fields=["device_status", "pass_fail_result"],
            rule="implies",
            mapping={"operational": "pass", "needs_service": "inconclusive"},
        )
    )
    ok = check_equivalence(
        "status_implies_pass",
        suite,
        {"device_status": "operational", "pass_fail_result": "pass"},
    )
    assert ok.passed
    bad = check_equivalence(
        "status_implies_pass",
        suite,
        {"device_status": "operational", "pass_fail_result": "fail"},
    )
    assert not bad.passed


def test_numeric_tolerance() -> None:
    suite = _suite(
        score_range=EquivalenceClass(
            fields=["devices[0].score", "devices[1].score"],
            rule="numeric_tolerance",
            tolerance=0.01,
        )
    )
    output = {
        "devices": [
            {"score": 1.0},
            {"score": 1.005},
        ]
    }
    assert check_equivalence("score_range", suite, output).passed
    output["devices"][1]["score"] = 2.0
    assert not check_equivalence("score_range", suite, output).passed


def test_one_of_rule() -> None:
    suite = _suite(
        zone=EquivalenceClass(
            fields=["devices[0].zone", "devices[1].zone"],
            rule="one_of",
            groups=[["A", "B"], ["C", "D"]],
        )
    )
    assert check_equivalence(
        "zone",
        suite,
        {"devices": [{"zone": "A"}, {"zone": "B"}]},
    ).passed
    assert not check_equivalence(
        "zone",
        suite,
        {"devices": [{"zone": "A"}, {"zone": "C"}]},
    ).passed
