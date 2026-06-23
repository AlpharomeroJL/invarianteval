# CLAUDE.md — Agentic build notes

This repo was built with deliberate human architecture and agentic execution.

## Human-owned decisions

- **Derived provenance** over stipulated labels (the moat)
- **Fixture-based local gate** — no GitHub Actions, no paid account
- **Bounded v1 contracts** for `schema_faithful` and `equivalence_preserved`
- **Judge as supporting signal** — invariants hard-block, judge warns only
- **Scope cuts** — no React dashboard, no SaaS, no OTel in v1

## Agent-delegated work

- Package scaffold, provider implementations, assertion library
- Test suite (derivation table tests, good/regressed fixture integration)
- Local gate scripts (`scripts/run-gate.ps1`, `run-gate.sh`), Docker Compose
- Documentation drafts from the build plan

## Conventions

- Python 3.11+, Pydantic v2, Typer CLI, hatchling
- `ruff check .` and `pytest -q` before merge
- Fixture JSON committed per case under `fixtures/good/` and `fixtures/regressed/`

## Commands

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
.\scripts\run-gate.ps1   # or ./scripts/run-gate.sh
```
