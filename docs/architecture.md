# Architecture

## Overview

InvariantEval V2 is a monorepo with four layers:

1. **Python library** — runner, derived provenance, evidence grounding, assertions
2. **Integrations** — pytest plugin, DeepEval bridge, OTel ingest
3. **Platform** — FastAPI server, SQLite storage, online eval worker
4. **Dashboard** — React/Vite control plane

## System diagram

```
OTel spans / pytest / CLI
        │
        ▼
   Runner (library)
        │
        ├─► FastAPI ──► SQLite (runs, suites, orgs)
        │
        └─► Worker ──► online_eval_queue (warn-only)
                │
                ▼
           React dashboard
```

## Data flow

```
Input → Provider → model_parsed
     → SUT merge → final_output + human_confirmed
     → ProvenanceDeriver (+ source spans / evidence)
     → Trace
     → Assertions (deterministic → invariant → judge)
     → Run JSON / API / report
```

## Module layout

```
invarianteval/          library core
  core/evidence.py      substring/span grounding
  ingest/otel.py        production trace → fixtures
  assertions/equivalence.py
pytest_invarianteval/   pytest entry point
deepeval_bridge/        optional judge adapter
server/                 FastAPI + auth + RBAC
worker/                 online eval sampler
web/                    React dashboard
```

## Execution modes

| Mode | Provider | Use case |
|------|----------|----------|
| `fixture` | `FixtureProvider` | CI, gate scripts, regression |
| `live` | Ollama (+ OpenAI fallback) | Local dev |

## Online eval

Production traces enqueue to `online_eval_queue`. The worker runs invariant assertions in **warn-only** mode — never blocks live traffic. Alerts surface when failure rate exceeds `alert_threshold`.

## Auth

- JWT cookies/tokens for dashboard (`POST /auth/login`)
- Bearer API keys for automation (`POST /api-keys`)
- Roles: `viewer`, `editor`, `admin`

## Local gate

`scripts/run-gate.ps1` / `run-gate.sh` — good fixtures pass, regressed fixtures fail. No GitHub Actions required.
