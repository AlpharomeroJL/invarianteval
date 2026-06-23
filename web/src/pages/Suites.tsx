import { useEffect, useState } from "react";
import { api } from "../api";

type SuiteRow = { id: number; name: string; updated_at: string };

export function Suites() {
  const [suites, setSuites] = useState<SuiteRow[]>([]);
  const [yaml, setYaml] = useState("");
  const [name, setName] = useState("fire-inspection-extraction");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api<SuiteRow[]>("/suites").then(setSuites).catch(() => undefined);
  }, []);

  async function save() {
    await api("/suites", {
      method: "POST",
      body: JSON.stringify({ name, yaml_content: yaml }),
    });
    setMsg("Saved");
  }

  return (
    <div>
      <h1>Suites</h1>
      <div className="card">
        <label>
          Name{" "}
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <textarea
          value={yaml}
          onChange={(e) => setYaml(e.target.value)}
          placeholder="Paste suite YAML..."
        />
        <button type="button" onClick={save}>
          Save suite
        </button>
        {msg && <p className="pass">{msg}</p>}
      </div>
      <ul>
        {suites.map((s) => (
          <li key={s.id}>
            {s.name} — updated {s.updated_at}
          </li>
        ))}
      </ul>
    </div>
  );
}
