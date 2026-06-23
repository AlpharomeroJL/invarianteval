import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

type RunRow = {
  run_id: string;
  suite_name: string;
  passed_cases: number;
  total_cases: number;
  invariant_failures: number;
  created_at: string;
};

export function Runs() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<RunRow[]>("/runs")
      .then(setRuns)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1>Runs</h1>
      {error && <p className="fail">{error}</p>}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Suite</th>
              <th>Pass</th>
              <th>Invariant failures</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.run_id}>
                <td>
                  <Link to={`/runs/${r.run_id}/cases/panel-001`}>{r.run_id}</Link>
                </td>
                <td>{r.suite_name}</td>
                <td>
                  {r.passed_cases}/{r.total_cases}
                </td>
                <td className={r.invariant_failures ? "fail" : "pass"}>
                  {r.invariant_failures}
                </td>
                <td>{r.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
