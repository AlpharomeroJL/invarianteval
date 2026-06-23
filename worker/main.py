from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from invarianteval.core.case import EvalCase
from invarianteval.core.runner import Runner
from invarianteval.core.suite import load_suite
from invarianteval.providers.base import ProviderResult
from invarianteval.providers.fixture import FixtureProvider
from server.db import OnlineEvalConfig, OnlineEvalQueue, SessionLocal, init_db

EXAMPLE_SUITE = Path("examples/fire-inspection-extraction/suite.yaml")


def default_merge(provider_result: ProviderResult):
    if provider_result.final_output is not None:
        return provider_result.final_output, provider_result.human_confirmed
    return provider_result.parsed or {}, provider_result.human_confirmed


def process_queue_item(item: OnlineEvalQueue, suite_path: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        fixtures_dir = Path(tmp)
        case_id = f"online-{item.id}"
        fixture = dict(item.fixture_payload)
        fixture.setdefault("provider", "online")
        (fixtures_dir / f"{case_id}.json").write_text(json.dumps(fixture), encoding="utf-8")

        suite = load_suite(suite_path)
        suite.cases = [
            EvalCase(
                id=case_id,
                input_file="data/2026-06-23/panel-001.txt",
                assertions=suite.cases[0].assertions if suite.cases else [],
            )
        ]
        provider = FixtureProvider(fixtures_dir)
        run = Runner(suite, provider, provider_mode="fixture", merge_fn=default_merge).run()
        failures = [
            r
            for c in run.cases
            for r in c.assertion_results
            if not r.passed and r.tier == "invariant"
        ]
        if failures:
            return True, failures[0].detail or failures[0].name
        return False, "ok"


def run_worker(poll_seconds: int = 5) -> None:
    init_db()
    while True:
        db = SessionLocal()
        try:
            items = (
                db.query(OnlineEvalQueue)
                .filter(OnlineEvalQueue.processed == False)  # noqa: E712
                .limit(10)
                .all()
            )
            for item in items:
                config = (
                    db.query(OnlineEvalConfig)
                    .filter(OnlineEvalConfig.org_id == item.org_id)
                    .first()
                )
                mode = config.mode if config else "warn"
                failed, detail = process_queue_item(item, EXAMPLE_SUITE)
                item.processed = True
                item.invariant_failed = failed
                item.result_detail = f"[{mode}] {detail}"
                db.commit()
        finally:
            db.close()
        time.sleep(poll_seconds)


if __name__ == "__main__":
    run_worker()
