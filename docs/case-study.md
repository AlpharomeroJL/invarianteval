# Case study — OTel ingest → gate blocks regression

## Setup

A structured extraction pipeline pulls fields from synthetic fire-panel inspection records. One field — `pass_fail_result` — is **locked**: it must never appear in final output unless a human explicitly confirmed it.

## V2 arc: production trace → pinned case

1. Production emits OTel spans with `invarianteval.*` attributes
2. `invarianteval ingest otel sample-traces.ndjson --out fixtures/from-prod/` creates replay fixtures
3. A regressed model trace is pinned as a suite case
4. `scripts/run-gate.ps1` blocks the release before the demo ships bad data

## The change
A model version bump (simulated in `fixtures/regressed/panel-001.json`) caused the model to start volunteering `pass_fail_result: "pass"` in its parsed output. The merge step included it in final output without setting `human_confirmed`.

A demo of the extraction UI would have looked fine — the field has a plausible value at high confidence.

## The catch

InvariantEval's `ProvenanceDeriver` compared `model_parsed` against `final_output`:

- `pass_fail_result` appeared in both → **model-originated**
- Policy is **locked**
- No `human_confirmed` flag → provenance derived as `ai_suggested`

`never_auto_filled` failed. The local gate (`scripts/run-gate.ps1` / `run-gate.sh`, fixture mode, `--fail-on-invariant`) exits non-zero. The summary shows exactly which case and invariant failed.

## The fix and the lesson

1. **Encode safety invariants, not just accuracy.** A 100% pass rate on accuracy metrics does not mean your evals are sufficient.
2. **Derive provenance, don't stipulate it.** The regression is real because the harness observed model output, not because someone labeled it.
3. **Run the gate on fixtures locally.** Deterministic checks beat flaky live-model runs — use `scripts/run-gate.ps1` before you push.

## Reproduce

```bash
invarianteval run examples/fire-inspection-extraction/suite.yaml \
  --provider fixture \
  --fixtures examples/fire-inspection-extraction/fixtures/regressed \
  --fail-on-invariant \
  --format summary
```

Expected: non-zero exit, invariant failure on `panel-001` / `never_auto_filled[pass_fail_result]`.
