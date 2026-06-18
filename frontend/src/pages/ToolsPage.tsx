import { Check, Hammer, Play, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Tool = { name: string; description: string; sensitive: boolean };
type Approval = {
  id: number;
  tool_name: string;
  payload: Record<string, unknown>;
  status: string;
  reason: string;
  created_at: string;
};

export function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selected, setSelected] = useState("calculator");
  const [payload, setPayload] = useState('{"expression":"12 * 7"}');
  const [result, setResult] = useState("");

  useEffect(() => {
    api.get<Tool[]>("/tools").then((response) => {
      setTools(response.data);
      setSelected(response.data[0]?.name ?? "calculator");
    });
  }, []);

  async function run(event: React.FormEvent) {
    event.preventDefault();
    const response = await api.post("/tools/run", { tool_name: selected, payload: JSON.parse(payload || "{}") });
    setResult(JSON.stringify(response.data, null, 2));
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Controlled Tools</h1>
          <p>Run approved tools with human approval gates for sensitive actions.</p>
        </div>
      </header>
      <div className="grid-list">
        {tools.map((tool) => (
          <article className="panel-card" key={tool.name}>
            <Hammer size={18} />
            <h2>{tool.name}</h2>
            <p>{tool.description}</p>
            <span>{tool.sensitive ? "Approval required" : "Direct execution"}</span>
          </article>
        ))}
      </div>
      <form className="analytics-form" onSubmit={run}>
        <label>
          Tool
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {tools.map((tool) => <option key={tool.name}>{tool.name}</option>)}
          </select>
        </label>
        <label>
          Payload JSON
          <textarea value={payload} onChange={(event) => setPayload(event.target.value)} />
        </label>
        <button className="primary-button"><Play size={16} /> Run tool</button>
      </form>
      {result ? <pre>{result}</pre> : null}
    </section>
  );
}

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);

  async function load() {
    const response = await api.get<Approval[]>("/approvals");
    setApprovals(response.data);
  }

  async function decide(id: number, status: "approved" | "rejected") {
    await api.post(`/approvals/${id}/decision`, { status, decision_note: `${status} from dashboard` });
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Human Approvals</h1>
          <p>Review sensitive tool requests before execution.</p>
        </div>
      </header>
      <div className="timeline">
        {approvals.map((approval) => (
          <article key={approval.id}>
            <Hammer size={16} />
            <div>
              <strong>{approval.tool_name}</strong>
              <span>{approval.status} - {new Date(approval.created_at).toLocaleString()}</span>
              <code>{JSON.stringify(approval.payload)}</code>
            </div>
            {approval.status === "pending" ? (
              <div className="row-actions">
                <button className="icon-button primary" title="Approve" onClick={() => decide(approval.id, "approved")}><Check size={16} /></button>
                <button className="icon-button danger" title="Reject" onClick={() => decide(approval.id, "rejected")}><X size={16} /></button>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
