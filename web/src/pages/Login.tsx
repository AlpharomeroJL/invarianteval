import { useState } from "react";
import { login } from "../api";

export function Login() {
  const [email, setEmail] = useState("admin@demo.local");
  const [password, setPassword] = useState("admin");
  const [msg, setMsg] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await login(email, password);
      setMsg("Logged in");
    } catch (err) {
      setMsg(String(err));
    }
  }

  return (
    <div>
      <h1>Login</h1>
      <form className="card" onSubmit={submit}>
        <p>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
        </p>
        <p>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
          />
        </p>
        <button type="submit">Sign in</button>
        <p>{msg}</p>
      </form>
    </div>
  );
}
