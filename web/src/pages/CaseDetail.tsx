import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

type CaseResult = {
  case_id: string;
  passed: boolean;
  invariant_passed: boolean;
  final_output: Record<string, unknown>;
  model_parsed: Record<string, unknown>;
  trace: Record<string, unknown>;
  assertion_results: Array<{
    name: string;
    passed: boolean;
    detail?: string;
    tier: string;
  }>;
};

type RunDetail = {
  run_id: string;
  suite_name: string;
  cases: CaseResult[];
};

export function CaseDetail() {
  const { runId, caseId } = useParams();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    api<RunDetail>(`/runs/${runId}`)
      .then(setRun)
      .catch((e) => setError(String(e)));
  }, [runId]);

  const c = run?.cases.find((x) => x.case_id === caseId) ?? run?.cases[0];

  return (
    <div>
      <h1>Case {caseId ?? c?.case_id}</h1>
      {error && <p className="fail">{error}</p>}
      {c && (
        <>
          <div className="card">
            <p className={c.invariant_passed ? "pass" : "fail"}>
              Invariant: {c.invariant_passed ? "PASS" : "FAIL"}
            </p>
            <h3>Assertions</h3>
            <ul>
              {c.assertion_results.map((a) => (
                <li key={a.name} className={a.passed ? "pass" : "fail"}>
                  {a.name} ({a.tier}) {a.detail ?? ""}
                </li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h3>Model parsed vs final</h3>
            <pre>{JSON.stringify({ model_parsed: c.model_parsed, final: c.final_output }, null, 2)}</pre>
          </div>
          <div className="card">
            <h3>Provenance trace</h3>
            <pre>{JSON.stringify(c.trace, null, 2)}</pre>
          </div>
        </>
      )}
    </div>
  );
}
