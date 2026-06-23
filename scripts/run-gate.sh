#!/usr/bin/env bash
# Local eval gate — run before push/PR. No GitHub Actions required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUITE="$ROOT/examples/fire-inspection-extraction/suite.yaml"
GOOD="$ROOT/examples/fire-inspection-extraction/fixtures/good"
REGRESSED="$ROOT/examples/fire-inspection-extraction/fixtures/regressed"
BASELINE="$ROOT/examples/fire-inspection-extraction/baseline.json"

echo "==> Core tests (library only, no platform deps)"
python -m pytest -q

echo ""
echo "==> Good fixtures (must pass)"
invarianteval run "$SUITE" \
  --provider fixture \
  --fixtures "$GOOD" \
  --baseline "$BASELINE" \
  --fail-on-invariant

echo ""
echo "==> Regressed fixtures (must fail — proves gate catches auto-fill)"
if invarianteval run "$SUITE" \
  --provider fixture \
  --fixtures "$REGRESSED" \
  --fail-on-invariant \
  --format github-summary 2>/dev/null; then
  echo "ERROR: regressed fixtures should have failed"
  exit 1
fi
echo "OK: regressed fixtures correctly blocked"

echo ""
echo "Gate passed."
