from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from invarianteval.core.models import Run

REPORT_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>InvariantEval Report — {{ run.suite_name }}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }
    h1 { font-size: 1.5rem; }
    table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
    th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
    th { background: #f5f5f5; }
    .fail { color: #b00020; font-weight: 600; }
    .pass { color: #1b5e20; }
    .warn { color: #e65100; }
    .metrics { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
    .metric { background: #f9f9f9; padding: 1rem; border-radius: 4px; }
    .trace { font-size: 0.85rem; font-family: monospace; }
  </style>
</head>
<body>
  <h1>InvariantEval Report</h1>
  <p><strong>Suite:</strong> {{ run.suite_name }} &nbsp;|&nbsp;
     <strong>Run:</strong> {{ run.run_id }} &nbsp;|&nbsp;
     <strong>Mode:</strong> {{ run.provider_mode }}</p>

  {% if run.summary %}
  <div class="metrics">
    <div class="metric"><strong>Pass rate</strong><br>{{ "%.0f"|format(run.summary.metrics.passed_cases / run.summary.metrics.total_cases * 100) }}%</div>
    <div class="metric"><strong>Invariant pass</strong><br>{{ "%.0f"|format(run.summary.metrics.invariant_pass_rate * 100) }}%</div>
    <div class="metric"><strong>Invariant failures</strong><br>{{ run.summary.metrics.invariant_failures }}</div>
    <div class="metric"><strong>Cost / task</strong><br>${{ "%.4f"|format(run.summary.metrics.cost_per_task_usd) }}</div>
    <div class="metric"><strong>Latency p95</strong><br>{{ "%.0f"|format(run.summary.metrics.latency_p95_ms) }}ms</div>
    {% if run.summary.metrics.judge_score_mean is not none %}
    <div class="metric"><strong>Judge (info)</strong><br>{{ "%.2f"|format(run.summary.metrics.judge_score_mean) }}</div>
    {% endif %}
  </div>
  {% endif %}

  <h2>Cases</h2>
  <table>
    <thead>
      <tr>
        <th>Case</th>
        <th>Status</th>
        <th>Invariants</th>
        <th>Cost</th>
        <th>Latency</th>
        <th>Failures</th>
      </tr>
    </thead>
    <tbody>
      {% for case in run.cases %}
      <tr>
        <td>{{ case.case_id }}</td>
        <td class="{{ 'pass' if case.passed else 'fail' }}">{{ 'PASS' if case.passed else 'FAIL' }}</td>
        <td class="{{ 'pass' if case.invariant_passed else 'fail' }}">{{ 'OK' if case.invariant_passed else 'FAIL' }}</td>
        <td>${{ "%.4f"|format(case.cost_usd) }}</td>
        <td>{{ "%.0f"|format(case.latency_ms) }}ms</td>
        <td>
          {% for ar in case.assertion_results if not ar.passed %}
          <div class="{{ 'warn' if ar.tier == 'judge' else 'fail' }}">{{ ar.name }}: {{ ar.detail }}</div>
          {% endfor %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <h2>Derived Provenance</h2>
  {% for case in run.cases %}
  <h3>{{ case.case_id }}</h3>
  <table class="trace">
    <thead><tr><th>Field</th><th>Value</th><th>Provenance</th><th>Model-originated</th><th>Policy</th></tr></thead>
    <tbody>
      {% for field, ft in case.trace.items() %}
      <tr>
        <td>{{ field }}</td>
        <td>{{ ft['value'] }}</td>
        <td>{{ ft['provenance'] }}</td>
        <td>{{ ft['model_originated'] }}</td>
        <td>{{ ft['policy'] }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% endfor %}
</body>
</html>
""")


def render_report(run: Run, output_path: Path) -> None:
    html = REPORT_TEMPLATE.render(run=run)
    output_path.write_text(html, encoding="utf-8")


def format_github_summary(run: Run) -> str:
    lines = ["## InvariantEval Gate Summary", ""]
    if not run.summary:
        return "\n".join(lines)

    m = run.summary.metrics
    lines.extend(
        [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Cases passed | {m.passed_cases}/{m.total_cases} |",
            f"| Invariant pass rate | {m.invariant_pass_rate:.1%} |",
            f"| Invariant failures | {m.invariant_failures} |",
            f"| Deterministic pass rate | {m.deterministic_pass_rate:.1%} |",
            f"| Cost per task | ${m.cost_per_task_usd:.4f} |",
            f"| Latency p95 | {m.latency_p95_ms:.0f}ms |",
        ]
    )
    if m.judge_score_mean is not None:
        lines.append(f"| Judge score (warn only) | {m.judge_score_mean:.2f} |")

    failed = [
        (c.case_id, r.name, r.detail)
        for c in run.cases
        for r in c.assertion_results
        if not r.passed and r.tier == "invariant"
    ]
    if failed:
        lines.extend(["", "### Invariant Failures", ""])
        for case_id, name, detail in failed:
            lines.append(f"- **{case_id}** `{name}`: {detail}")

    if run.summary.baseline_warnings:
        lines.extend(["", "### Warnings", ""])
        for w in run.summary.baseline_warnings:
            lines.append(f"- {w}")

    return "\n".join(lines)


format_summary = format_github_summary
