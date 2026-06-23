import { useState } from "react";

export function Settings() {
  const [members, setMembers] = useState<Array<{ user_id: number; role: string }>>([]);
  const [apiKey, setApiKey] = useState("");

  async function loadMembers() {
    const { api } = await import("../api");
    setMembers(await api("/members"));
  }

  async function createKey() {
    const { api } = await import("../api");
    const res = await api<{ api_key: string }>("/api-keys", {
      method: "POST",
      body: JSON.stringify({ name: "dashboard" }),
    });
    setApiKey(res.api_key);
  }

  return (
    <div>
      <h1>Settings</h1>
      <div className="card">
        <h3>Organization</h3>
        <button type="button" onClick={loadMembers}>
          Load members
        </button>
        <ul>
          {members.map((m) => (
            <li key={m.user_id}>
              user {m.user_id}: {m.role}
            </li>
          ))}
        </ul>
      </div>
      <div className="card">
        <h3>API keys</h3>
        <button type="button" onClick={createKey}>
          Create API key
        </button>
        {apiKey && <p>Copy now: {apiKey}</p>}
      </div>
    </div>
  );
}
