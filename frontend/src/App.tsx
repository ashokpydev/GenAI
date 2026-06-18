import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import { Shell, type View } from "./components/Shell";
import { api, type User } from "./lib/api";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { AuditPage, EvaluationPage, PromptPage, SettingsPage, UsagePage } from "./pages/AdminPages";
import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage, UploadPage } from "./pages/DocumentsPage";
import { LoginPage } from "./pages/LoginPage";

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<View>("chat");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<User>("/auth/me").then((response) => setUser(response.data)).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  function logout() {
    localStorage.removeItem("contextops_token");
    setUser(null);
  }

  if (loading) return <main className="loading-screen">Loading ContextOps AI...</main>;
  if (!user) return <LoginPage onAuthenticated={(_, nextUser) => setUser(nextUser)} />;

  const pages: Record<View, ReactElement> = {
    chat: <ChatPage />,
    upload: <UploadPage />,
    documents: <DocumentsPage />,
    analytics: <AnalyticsPage />,
    prompts: <PromptPage />,
    evaluation: <EvaluationPage />,
    audit: <AuditPage />,
    usage: <UsagePage />,
    settings: <SettingsPage />
  };

  return (
    <Shell user={user} view={view} onViewChange={setView} onLogout={logout}>
      {pages[view]}
    </Shell>
  );
}
