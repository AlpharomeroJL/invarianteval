# Fire Inspection Extraction — Domain Pack

Synthetic structured extraction demo for InvariantEval. All data is fabricated; no real inspection records or copyrighted standard text.

## What it demonstrates

- **Derived provenance:** `never_auto_filled` detects when the model volunteers `pass_fail_result` without human confirmation
- **Equivalence classes:** `panel_family` asserts cross-device model family consistency
- **Schema faithfulness:** v1 envelope checks against `expected/schema.json`
- **Fixture-based gate:** `fixtures/good/` passes; `fixtures/regressed/` triggers hard-block on `panel-001`

## Run locally

```bash
# Full gate (good pass + regressed must fail)
.\scripts\run-gate.ps1        # Windows
./scripts/run-gate.sh         # Unix

# Good fixtures only
invarianteval run suite.yaml --provider fixture --fixtures fixtures/good --fail-on-invariant

# Regressed fixtures (should fail on panel-001)
invarianteval run suite.yaml --provider fixture --fixtures fixtures/regressed --fail-on-invariant
```

## Field policies

| Field | Policy |
|-------|--------|
| `pass_fail_result` | locked |
| `device_status` | locked |
| `panel_model` | model_allowed |
| `notes` | model_allowed |
