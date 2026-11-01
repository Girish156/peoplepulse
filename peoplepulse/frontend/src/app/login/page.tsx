"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { saveSession } from "@/lib/auth";

const DEMO_USERS = [
  { role: "Administrator", email: "admin@peoplepulse.demo" },
  { role: "HR Partner", email: "hr@peoplepulse.demo" },
  { role: "Manager", email: "manager@peoplepulse.demo" },
  { role: "Employee", email: "employee@peoplepulse.demo" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@peoplepulse.demo");
  const [password, setPassword] = useState("PeoplePulse2026!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await api.login(email, password);
      saveSession({
        access_token: user.access_token,
        token_type: user.token_type,
        role: user.role as never,
        name: user.name,
        email: user.email,
        employee_id: user.employee_id,
      });
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold text-slate-900">PeoplePulse</h1>
          <p className="mt-1 text-sm text-slate-500">Evidence-based performance reviews</p>
        </div>
        <form onSubmit={onSubmit} className="card space-y-4 p-6">
          <div>
            <label className="label">Email</label>
            <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <button className="btn btn-primary w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
          <p className="text-xs text-amber-700">
            Demo authentication only. These identities are not a production identity provider.
          </p>
        </form>
        <div className="mt-4 card p-4 text-sm">
          <p className="mb-2 font-medium text-slate-700">Demo users (password: PeoplePulse2026!)</p>
          <ul className="space-y-1 text-slate-600">
            {DEMO_USERS.map((u) => (
              <li key={u.email}>
                <button
                  type="button"
                  className="text-left hover:text-indigo-700"
                  onClick={() => setEmail(u.email)}
                >
                  {u.role}: {u.email}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
