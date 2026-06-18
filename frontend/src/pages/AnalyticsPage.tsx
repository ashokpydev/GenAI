import { Database, Play } from "lucide-react";
import { useState } from "react";
import { api } from "../lib/api";

type AnalyticsResult = { sql: string; rows: Record<string, unknown>[]; summary: string };

export function AnalyticsPage() {
  const [question, setQuestion] = useState("What were the top products by revenue?");
  const [sql, setSql] = useState("");
  const [result, setResult] = useState<AnalyticsResult | null>(null);
  const [error, setError] = useState("");

  async function run(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await api.post<AnalyticsResult>("/analytics/query", { question, sql: sql || null });
      setResult(response.data);
    } catch {
      setError("The SQL guardrail blocked the request or analytics service is unavailable.");
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Analytics Assistant</h1>
          <p>Ask business questions with SELECT-only SQL guardrails and masked sensitive columns.</p>
        </div>
      </header>
      <form className="analytics-form" onSubmit={run}>
        <label>
          Question
          <input value={question} onChange={(event) => setQuestion(event.target.value)} />
        </label>
        <label>
          Optional SQL
          <textarea value={sql} onChange={(event) => setSql(event.target.value)} placeholder="SELECT product, SUM(revenue) FROM sales GROUP BY product LIMIT 5" />
        </label>
        {error ? <div className="error">{error}</div> : null}
        <button className="primary-button"><Play size={16} /> Run analysis</button>
      </form>
      {result ? (
        <section className="result-panel">
          <h2><Database size={18} /> Result</h2>
          <code>{result.sql}</code>
          <p>{result.summary}</p>
          <pre>{JSON.stringify(result.rows, null, 2)}</pre>
        </section>
      ) : null}
    </section>
  );
}
