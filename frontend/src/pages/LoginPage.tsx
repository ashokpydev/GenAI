import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { api, type User } from "../lib/api";

type Props = {
  onAuthenticated: (token: string, user: User) => void;
};

export function LoginPage({ onAuthenticated }: Props) {
  const [email, setEmail] = useState("admin@contextops.ai");
  const [password, setPassword] = useState("Admin@12345");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const login = await api.post("/auth/login", { email, password });
      localStorage.setItem("contextops_token", login.data.access_token);
      const me = await api.get<User>("/auth/me");
      onAuthenticated(login.data.access_token, me.data);
    } catch {
      setError("Sign-in failed. Check credentials or backend status.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-panel" onSubmit={submit}>
        <ShieldCheck size={34} />
        <h1>ContextOps AI</h1>
        <p>Sign in to the enterprise knowledge, analytics, and action copilot.</p>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
        </label>
        <label>
          Password
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
        </label>
        {error ? <div className="error">{error}</div> : null}
        <button className="primary-button" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}
