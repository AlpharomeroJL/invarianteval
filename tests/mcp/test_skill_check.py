from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "examples/fire-inspection-extraction/suite.yaml"
CHECK = ROOT / "agent-skill/invarianteval/check.py"
GOOD = ROOT / "examples/fire-inspection-extraction/fixtures/good/panel-001.json"
REGRESSED = ROOT / "examples/fire-inspection-extraction/fixtures/regressed/panel-001.json"


def _run_check(fixture_path: Path) -> int:
    fx = json.loads(fixture_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        model_path = work / "model.json"
        final_path = work / "final.json"
        model_path.write_text(json.dumps(fx["model_parsed"]), encoding="utf-8")
        final_path.write_text(json.dumps(fx["final_output"]), encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                str(CHECK),
                "--suite",
                str(SUITE),
                "--case-id",
                "panel-001",
                "--model-parsed",
                str(model_path),
                "--final-output",
                str(final_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return proc.returncode


def test_skill_check_good_panel_001() -> None:
    assert _run_check(GOOD) == 0


def test_skill_check_regressed_panel_001() -> None:
    assert _run_check(REGRESSED) != 0
