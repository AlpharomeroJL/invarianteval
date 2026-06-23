import { useEffect, useState } from "react";
import { api } from "../api";

type Alerts = {
  alert: boolean;
  failure_count: number;
  threshold: number;
  recent: Array<{ id: number; detail: string; at: string }>;
};

export function OnlineEval() {
  const [data, setData] = useState<Alerts | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Alerts>("/online/alerts")
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1>Online Eval</h1>
      <p>Production sampling runs invariants in warn-only mode.</p>
      {error && <p className="fail">{error}</p>}
      {data && (
        <div className="card">
          <p className={data.alert ? "fail" : "pass"}>
            Alert: {data.alert ? "ACTIVE" : "ok"} — {data.failure_count} failures (threshold{" "}
            {data.threshold})
          </p>
          <h3>Recent violations</h3>
          <ul>
            {data.recent.map((r) => (
              <li key={r.id}>
                #{r.id} {r.at}: {r.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
