#!/usr/bin/env python3
"""Shell out to invarianteval CLI. No engine logic here."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _abs_if_relative(suite_dir: Path, value: str) -> str:
    candidate = suite_dir / value
    if candidate.exists():
        return str(candidate.resolve())
    return value


def _resolve_case_paths(suite_dir: Path, case: dict) -> None:
    case["input_file"] = _abs_if_relative(suite_dir, case["input_file"])
    if case.get("expected_file"):
        case["expected_file"] = _abs_if_relative(suite_dir, case["expected_file"])
    for assertion in case.get("assertions", []):
        if not isinstance(assertion, dict):
            continue
        for name, params in assertion.items():
            if isinstance(params, str) and "/" in params:
                assertion[name] = _abs_if_relative(suite_dir, params)
            elif isinstance(params, dict) and "schema" in params:
                params["schema"] = _abs_if_relative(suite_dir, params["schema"])


def _filter_suite(suite_path: Path, case_id: str, work: Path) -> Path:
    raw = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    suite_dir = suite_path.parent
    cases = [c for c in raw.get("cases", []) if c.get("id") == case_id]
    if not cases:
        raise SystemExit(f"Case {case_id!r} not found in {suite_path}")
    if raw.get("schema_file"):
        raw["schema_file"] = _abs_if_relative(suite_dir, raw["schema_file"])
    for case in cases:
        _resolve_case_paths(suite_dir, case)
    raw["cases"] = cases
    out = work / "suite.yaml"
    out.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return out


def _write_input(suite_dir: Path, case: dict, case_input: str | None) -> None:
    input_rel = case["input_file"]
    input_path = suite_dir / input_rel
    input_path.parent.mkdir(parents=True, exist_ok=True)
    if case_input is not None:
        input_path.write_text(case_input, encoding="utf-8")
    elif not input_path.exists():
        input_path.write_text("(agent-check placeholder input)\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check declared invariants before finalizing structured output."
    )
    parser.add_argument("--suite", type=Path, required=True, help="Path to suite.yaml")
    parser.add_argument("--case-id", default="agent-check", help="Case id in suite.yaml")
    parser.add_argument("--model-parsed", type=Path, required=True, help="JSON file")
    parser.add_argument("--final-output", type=Path, required=True, help="JSON file")
    parser.add_argument("--human-confirmed", type=Path, help="JSON object of field flags")
    parser.add_argument("--case-input", type=Path, help="Optional source text file")
    args = parser.parse_args()

    model_parsed = _load_json(args.model_parsed)
    final_output = _load_json(args.final_output)
    human_confirmed = _load_json(args.human_confirmed) if args.human_confirmed else {}
    case_input = args.case_input.read_text(encoding="utf-8") if args.case_input else None

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        suite_dir = work / "suite"
        suite_dir.mkdir()
        filtered = _filter_suite(args.suite, args.case_id, suite_dir)
        case = yaml.safe_load(filtered.read_text(encoding="utf-8"))["cases"][0]
        _write_input(suite_dir, case, case_input)

        fixtures = work / "fixtures"
        fixtures.mkdir()
        fixture = {
            "model_parsed": model_parsed,
            "raw": json.dumps(model_parsed),
            "final_output": final_output,
            "human_confirmed": human_confirmed,
            "model": "agent-check",
            "provider": "fixture",
            "case_input": case_input or "",
        }
        (fixtures / f"{args.case_id}.json").write_text(
            json.dumps(fixture, indent=2), encoding="utf-8"
        )

        cmd = [
            sys.executable,
            "-m",
            "invarianteval.cli",
            "run",
            str(filtered),
            "--provider",
            "fixture",
            "--fixtures",
            str(fixtures),
            "--fail-on-invariant",
        ]
        proc = subprocess.run(cmd, cwd=suite_dir.parent)
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
