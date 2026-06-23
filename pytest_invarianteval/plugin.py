from __future__ import annotations

from pathlib import Path

import pytest

from invarianteval.core.runner import Runner
from invarianteval.core.suite import load_suite
from invarianteval.providers.fixture import FixtureProvider


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "invarianteval(suite, case_id, fixtures): run invariant eval gate for a case",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> None:
    marker = item.get_closest_marker("invarianteval")
    if not marker:
        return
    kwargs = marker.kwargs
    suite_path = Path(kwargs["suite"])
    fixtures_dir = Path(kwargs["fixtures"])
    case_id = kwargs.get("case_id")

    suite = load_suite(suite_path)
    if case_id:
        suite.cases = [c for c in suite.cases if c.id == case_id]
    provider = FixtureProvider(fixtures_dir)
    run = Runner(suite, provider, provider_mode="fixture").run()
    failures = [
        r
        for c in run.cases
        for r in c.assertion_results
        if not r.passed and r.tier == "invariant"
    ]
    if failures:
        msgs = [f"{r.name}: {r.detail}" for r in failures]
        pytest.fail("Invariant failures:\n" + "\n".join(msgs))
