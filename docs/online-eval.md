# Online eval

Online eval samples production traces and runs **invariant-tier assertions only** in warn-only mode.

## Configuration

Per-organization settings in `online_eval_config`:

```yaml
online_eval:
  sample_rate: 0.05
  mode: warn          # never hard-block production
  alert_threshold: 3  # failures in rolling window
```

Seed org defaults: 5% sample rate, threshold 3 (demo org uses 100% for portfolio demos).

## API

```bash
POST /online/sample
{
  "suite_name": "fire-inspection-extraction",
  "fixture": { ... }
}
```

Returns `{ "sampled": true, "queue_id": 1 }` when the trace is enqueued.

`GET /online/alerts` — dashboard alert state and recent violations.

## Worker

```bash
python -m worker.main
```

Polls `online_eval_queue`, runs fixtures through the library `Runner`, stores results. Judge tier is not used for production hard blocks.

## Dashboard

**Online Eval** view shows alert status and recent invariant violations from production sampling.

## Design constraints

- **Warn-only** — production traffic is never blocked by eval noise
- **Invariants only** — deterministic safety checks, not subjective judge scores
- **SQLite polling** — sufficient for portfolio/self-hosted; Redis optional later
