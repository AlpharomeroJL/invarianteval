from __future__ import annotations

from pathlib import Path

from invarianteval.ingest.otel import ingest_otel_file

ROOT = Path(__file__).resolve().parents[2]


def test_otel_ingest(tmp_path: Path) -> None:
    src = ROOT / "examples" / "fire-inspection-extraction" / "otel" / "sample-traces.ndjson"
    out = tmp_path / "fixtures"
    ids = ingest_otel_file(src, out)
    assert len(ids) >= 2
    assert (out / "panel-001.json").exists()
    assert (out / "panel-001-regressed.json").exists()
