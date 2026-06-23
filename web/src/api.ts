const API = import.meta.env.VITE_API_URL || "/api";

let token: string | null = localStorage.getItem("invarianteval_token");

export function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem("invarianteval_token", t);
  else localStorage.removeItem("invarianteval_token");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...init, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const data = await api<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}
