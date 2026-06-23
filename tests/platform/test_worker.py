from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.platform


def test_worker_process_good_fixture():
    pytest.importorskip("sqlalchemy")

    from server.db import OnlineEvalQueue
    from worker.main import process_queue_item

    fixture = json.loads(
        Path("examples/fire-inspection-extraction/fixtures/good/panel-001.json").read_text(
            encoding="utf-8"
        )
    )
    item = OnlineEvalQueue(
        id=1,
        org_id=1,
        suite_name="fire-inspection-extraction",
        fixture_payload=fixture,
    )
    suite = Path("examples/fire-inspection-extraction/suite.yaml")
    failed, detail = process_queue_item(item, suite)
    assert failed is False
    assert detail == "ok"
