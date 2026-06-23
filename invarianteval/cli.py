from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import typer

from invarianteval.core.baseline import compare_baseline, save_baseline
from invarianteval.core.runner import Runner
from invarianteval.core.suite import load_suite
from invarianteval.cost import summarize_run
from invarianteval.providers.fallback import FallbackProvider
from invarianteval.providers.fixture import FixtureProvider
from invarianteval.providers.ollama import OllamaProvider
from invarianteval.providers.openai import OpenAIProvider
from invarianteval.report import format_summary, render_report

app = typer.Typer(no_args_is_help=True, help="InvariantEval — safety-invariant eval gate")


class ProviderMode(StrEnum):
    fixture = "fixture"
    live = "live"


def _build_provider(
    mode: ProviderMode,
    fixtures_dir: Path | None,
    suite,
) -> FixtureProvider | FallbackProvider | OllamaProvider:
    if mode == ProviderMode.fixture:
        if not fixtures_dir:
            raise typer.BadParameter("--fixtures is required when --provider fixture")
        return FixtureProvider(fixtures_dir)

    primary = OllamaProvider()
    providers = [primary]
    if OpenAIProvider().health_check():
        providers.append(OpenAIProvider())
    return FallbackProvider(providers)


@app.command()
def run(
    suite_path: Path = typer.Argument(..., help="Path to suite.yaml"),
    provider: ProviderMode = typer.Option(ProviderMode.fixture, help="Execution mode"),
    fixtures: Path | None = typer.Option(None, help="Fixtures directory for replay"),
    baseline: Path | None = typer.Option(None, help="Baseline JSON for comparison"),
    output: Path | None = typer.Option(None, help="Write run JSON to path"),
    fail_on_invariant: bool = typer.Option(False, help="Exit 1 on invariant failure"),
    format: str | None = typer.Option(None, help="Output format: summary or github-summary"),
) -> None:
    """Run an eval suite."""
    suite = load_suite(suite_path)
    prov = _build_provider(provider, fixtures, suite)
    runner = Runner(suite, prov, provider_mode=provider.value)
    run_result = runner.run()

    if baseline:
        regressions, warnings = compare_baseline(run_result, baseline)
        if run_result.summary:
            run_result.summary.baseline_regressions = regressions
            run_result.summary.baseline_warnings = warnings

    if format in ("github-summary", "summary"):
        typer.echo(format_summary(run_result))
    else:
        typer.echo(summarize_run(run_result))

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(run_result.model_dump_json(indent=2), encoding="utf-8")

    exit_code = 0
    if fail_on_invariant and run_result.summary and run_result.summary.metrics.invariant_failures > 0:
        exit_code = 1
    if baseline and run_result.summary and run_result.summary.baseline_regressions:
        exit_code = 1
    raise typer.Exit(exit_code)


@app.command()
def record(
    suite_path: Path = typer.Argument(...),
    out: Path = typer.Option(..., help="Output fixtures directory"),
) -> None:
    """Record fixtures from a live provider run."""
    suite = load_suite(suite_path)
    prov = FallbackProvider([OllamaProvider(), OpenAIProvider()])
    runner = Runner(suite, prov, provider_mode="live")
    run_result = runner.run()
    out.mkdir(parents=True, exist_ok=True)

    for case in run_result.cases:
        fixture = {
            "model_parsed": case.model_parsed,
            "raw": json.dumps(case.model_parsed),
            "final_output": case.final_output,
            "human_confirmed": {},
            "model": case.model,
            "provider": case.provider,
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": case.latency_ms,
            "cost_usd": case.cost_usd,
        }
        (out / f"{case.case_id}.json").write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    typer.echo(f"Recorded {len(run_result.cases)} fixtures to {out}")


baseline_app = typer.Typer(help="Baseline management")
app.add_typer(baseline_app, name="baseline")


@baseline_app.command("update")
def baseline_update(
    suite_path: Path = typer.Argument(...),
    fixtures: Path = typer.Option(...),
    out: Path = typer.Option(..., help="Baseline JSON output path"),
) -> None:
    """Update baseline from a good fixture run."""
    suite = load_suite(suite_path)
    prov = FixtureProvider(fixtures)
    runner = Runner(suite, prov, provider_mode="fixture")
    run_result = runner.run()
    if run_result.summary:
        save_baseline(out, run_result.summary.metrics, suite.name)
    typer.echo(f"Baseline saved to {out}")


@baseline_app.command("diff")
def baseline_diff(
    run_path: Path = typer.Argument(..., help="Run JSON file"),
    baseline_path: Path = typer.Argument(...),
) -> None:
    """Compare a run against baseline."""
    from invarianteval.core.models import Run

    run_result = Run.model_validate_json(run_path.read_text(encoding="utf-8"))
    regressions, warnings = compare_baseline(run_result, baseline_path)
    for r in regressions:
        typer.echo(f"REGRESSION: {r}")
    for w in warnings:
        typer.echo(f"WARNING: {w}")
    if regressions:
        raise typer.Exit(1)


@app.command("add-case")
def add_case(
    from_run: Path = typer.Option(..., help="Run JSON path"),
    case_id: str = typer.Option(...),
    suite_path: Path = typer.Option(...),
    fixtures_out: Path = typer.Option(...),
) -> None:
    """Add a case from a run trace to the suite fixtures."""
    from invarianteval.core.models import Run

    run_result = Run.model_validate_json(from_run.read_text(encoding="utf-8"))
    case = next((c for c in run_result.cases if c.case_id == case_id), None)
    if not case:
        raise typer.BadParameter(f"Case {case_id} not found in run")

    fixtures_out.mkdir(parents=True, exist_ok=True)
    fixture = {
        "model_parsed": case.model_parsed,
        "raw": json.dumps(case.model_parsed),
        "final_output": case.final_output,
        "human_confirmed": {},
        "model": case.model,
        "provider": case.provider,
        "latency_ms": case.latency_ms,
        "cost_usd": case.cost_usd,
    }
    (fixtures_out / f"{case_id}.json").write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    typer.echo(f"Fixture saved for {case_id}. Append case to {suite_path} manually or extend YAML writer.")


@app.command()
def report(
    run_path: Path = typer.Argument(...),
    output: Path = typer.Option(Path("report.html")),
) -> None:
    """Generate static HTML report from a run."""
    from invarianteval.core.models import Run

    run_result = Run.model_validate_json(run_path.read_text(encoding="utf-8"))
    render_report(run_result, output)
    typer.echo(f"Report written to {output}")


ingest_app = typer.Typer(help="Ingest production traces")
app.add_typer(ingest_app, name="ingest")


@ingest_app.command("otel")
def ingest_otel(
    traces_path: Path = typer.Argument(..., help="OTel NDJSON or OTLP JSON file"),
    out: Path = typer.Option(..., "--out", help="Output fixtures directory"),
    suite: Path | None = typer.Option(None, help="Optional suite.yaml to append cases"),
) -> None:
    """Ingest OTel spans into fixture JSON files."""
    from invarianteval.ingest.otel import ingest_otel_file

    case_ids = ingest_otel_file(traces_path, out)
    typer.echo(f"Ingested {len(case_ids)} fixtures to {out}: {', '.join(case_ids)}")
    if suite:
        typer.echo(f"Add cases to {suite} manually or use add-case from a run JSON.")


@app.command("add-case-from-otel")
def add_case_from_otel(
    traces_path: Path = typer.Argument(...),
    case_id: str = typer.Option(..., help="Span case id or name"),
    fixtures_out: Path = typer.Option(...),
) -> None:
    """Extract a single case fixture from OTel traces."""
    from invarianteval.ingest.otel import load_spans, span_to_fixture

    spans = load_spans(traces_path)
    for idx, span in enumerate(spans):
        fixture = span_to_fixture(span, f"trace-{idx:04d}")
        cid = fixture.pop("_case_id")
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(cid))
        if safe_id == case_id or str(cid) == case_id:
            fixtures_out.mkdir(parents=True, exist_ok=True)
            (fixtures_out / f"{safe_id}.json").write_text(
                json.dumps(fixture, indent=2), encoding="utf-8"
            )
            typer.echo(f"Fixture saved: {fixtures_out / f'{safe_id}.json'}")
            return
    raise typer.BadParameter(f"Case {case_id} not found in {traces_path}")


def _register_server_commands() -> None:
    try:
        from server.cli import server_app
    except ImportError:
        return
    app.add_typer(server_app, name="server")


_register_server_commands()


if __name__ == "__main__":
    app()
