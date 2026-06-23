from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.platform


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_and_run(client):
    login = client.post("/auth/login", json={"email": "admin@demo.local", "password": "admin"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    run = client.post(
        "/runs",
        headers=headers,
        json={
            "suite_path": "examples/fire-inspection-extraction/suite.yaml",
            "fixtures_path": "examples/fire-inspection-extraction/fixtures/good",
        },
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]
    detail = client.get(f"/runs/{run_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["suite_name"] == "fire-inspection-extraction"


def test_online_sample(client):
    login = client.post("/auth/login", json={"email": "admin@demo.local", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    good_fixture = json.loads(
        Path("examples/fire-inspection-extraction/fixtures/good/panel-001.json").read_text(
            encoding="utf-8"
        )
    )
    r = client.post(
        "/online/sample",
        headers=headers,
        json={"suite_name": "fire-inspection-extraction", "fixture": good_fixture},
    )
    assert r.status_code == 200

