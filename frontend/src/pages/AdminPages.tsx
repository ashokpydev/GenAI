import { Activity, ClipboardCheck, FileText, History, Settings, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { StatCard } from "../components/StatCard";

export function PromptPage() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    api.get("/prompts").then((response) => setItems(response.data)).catch(() => setItems([]));
  }, []);

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Prompt Management</h1>
          <p>Versioned prompt templates for RAG, SQL, summarization, validation, and guardrails.</p>
        </div>
      </header>
      <div className="grid-list">
        {items.map((item) => (
          <article className="panel-card" key={item.id}>
            <h2>{item.name}</h2>
            <span>Version {item.version}</span>
            <p>{item.description}</p>
            <code>{item.template}</code>
          </article>
        ))}
      </div>
    </section>
  );
}

export function EvaluationPage() {
  const [metrics, setMetrics] = useState<any[]>([]);
  useEffect(() => {
    api.get("/admin/evaluations").then((response) => setMetrics(response.data.metrics)).catch(() => setMetrics([]));
  }, []);
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Evaluation Dashboard</h1>
          <p>Quality metrics for groundedness, relevance, retrieval, latency, and risk.</p>
        </div>
      </header>
      <div className="chart-panel">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="score" fill="#2563eb" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  useEffect(() => {
    api.get("/admin/audit-logs").then((response) => setLogs(response.data)).catch(() => setLogs([]));
  }, []);
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Audit Logs</h1>
          <p>Trace user actions, AI answers, document events, and analytics execution.</p>
        </div>
      </header>
      <div className="timeline">
        {logs.map((log) => (
          <article key={log.id}>
            <History size={16} />
            <div>
              <strong>{log.action}</strong>
              <span>{new Date(log.created_at).toLocaleString()}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function UsagePage() {
  const [usage, setUsage] = useState<any>({});
  useEffect(() => {
    api.get("/admin/usage").then((response) => setUsage(response.data)).catch(() => setUsage({}));
  }, []);
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Usage Dashboard</h1>
          <p>Operational telemetry for documents, chat, latency, risk, and active users.</p>
        </div>
      </header>
      <div className="stats-grid">
        <StatCard label="Users" value={usage.users ?? 0} icon={<Activity size={18} />} />
        <StatCard label="Documents" value={usage.documents ?? 0} icon={<FileText size={18} />} />
        <StatCard label="Messages" value={usage.chat_messages ?? 0} icon={<ClipboardCheck size={18} />} />
        <StatCard label="Avg latency" value={`${Math.round(usage.average_latency_ms ?? 0)} ms`} icon={<History size={18} />} />
        <StatCard label="Prompt tokens" value={usage.prompt_tokens ?? 0} icon={<Activity size={18} />} />
        <StatCard label="Tool runs" value={usage.tool_executions ?? 0} icon={<ClipboardCheck size={18} />} />
        <StatCard label="Pending approvals" value={usage.pending_approvals ?? 0} icon={<History size={18} />} />
        <StatCard label="Cost" value={`$${Number(usage.cost_usd ?? 0).toFixed(2)}`} icon={<Activity size={18} />} />
      </div>
    </section>
  );
}

export function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  useEffect(() => {
    api.get("/admin/users").then((response) => setUsers(response.data)).catch(() => setUsers([]));
  }, []);
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>User Management</h1>
          <p>Review roles and active access state.</p>
        </div>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>User</th><th>Email</th><th>Role</th><th>Status</th></tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td><Users size={15} /> {user.full_name}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{user.is_active ? "active" : "disabled"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function SettingsPage() {
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Admin Settings</h1>
          <p>Security, approvals, model routing, observability, and deployment controls.</p>
        </div>
      </header>
      <div className="settings-grid">
        {["Human approval for sensitive tools", "PII masking", "Prompt injection detection", "OpenTelemetry ready", "OAuth2 ready", "Cost-aware model routing"].map((item) => (
          <article className="panel-card" key={item}>
            <Settings size={18} />
            <strong>{item}</strong>
            <span>Configured for MVP extension.</span>
          </article>
        ))}
      </div>
    </section>
  );
}
