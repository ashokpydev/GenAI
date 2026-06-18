import {
  Activity,
  BarChart3,
  Bot,
  ClipboardCheck,
  Hammer,
  FileText,
  History,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  UploadCloud,
  Users
} from "lucide-react";
import type { ReactNode } from "react";
import type { User } from "../lib/api";

export type View =
  | "chat"
  | "upload"
  | "documents"
  | "analytics"
  | "tools"
  | "approvals"
  | "prompts"
  | "evaluation"
  | "audit"
  | "usage"
  | "users"
  | "settings";

const items: Array<{ id: View; label: string; icon: typeof Bot }> = [
  { id: "chat", label: "AI Chat", icon: Bot },
  { id: "upload", label: "Upload", icon: UploadCloud },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "tools", label: "Tools", icon: Hammer },
  { id: "approvals", label: "Approvals", icon: ShieldCheck },
  { id: "prompts", label: "Prompts", icon: SlidersHorizontal },
  { id: "evaluation", label: "Evaluation", icon: ClipboardCheck },
  { id: "audit", label: "Audit Logs", icon: History },
  { id: "usage", label: "Usage", icon: Activity },
  { id: "users", label: "Users", icon: Users },
  { id: "settings", label: "Settings", icon: Settings }
];

type Props = {
  user: User;
  view: View;
  onViewChange: (view: View) => void;
  onLogout: () => void;
  children: ReactNode;
};

export function Shell({ user, view, onViewChange, onLogout, children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <strong>ContextOps AI</strong>
            <span>Enterprise Copilot</span>
          </div>
        </div>
        <nav>
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <button className={view === item.id ? "nav-item active" : "nav-item"} key={item.id} onClick={() => onViewChange(item.id)}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="account">
          <div>
            <strong>{user.full_name}</strong>
            <span>{user.role.replace("_", " ")}</span>
          </div>
          <button className="icon-button" onClick={onLogout} title="Log out">
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
