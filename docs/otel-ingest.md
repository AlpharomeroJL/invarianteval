# OTel ingest

InvariantEval can turn production OpenTelemetry spans into replayable fixtures.

## Span attributes

| Attribute | Maps to |
|-----------|---------|
| `invarianteval.model_parsed` | JSON dict |
| `invarianteval.final_output` | JSON dict |
| `invarianteval.human_confirmed` | JSON dict |
| `invarianteval.case_input` | raw input text |
| `invarianteval.source_spans` | JSON dict of field → `[start, end]` |
| `invarianteval.case_id` | fixture filename |

## CLI

```bash
invarianteval ingest otel traces.ndjson --out fixtures/from-prod/
```

Single case extraction:

```bash
invarianteval add-case-from-otel traces.ndjson --case-id panel-001 --fixtures-out fixtures/pinned/
```

## API

`POST /ingest/otel` — multipart upload with `out_dir` query param (editor role).

## Sample data

`examples/fire-inspection-extraction/otel/sample-traces.ndjson` — synthetic OTLP-style NDJSON mirroring good and regressed panel cases.

## Workflow

1. Instrument your SUT to emit span attributes above
2. Export NDJSON from your collector or logging pipeline
3. Ingest → fixtures
4. Pin failing traces as suite cases
5. Local gate blocks regressions before deploy

Evidence grounding uses deterministic substring/span checks only — no NLP.
