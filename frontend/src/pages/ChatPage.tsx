import { Send, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { api, type ChatResult } from "../lib/api";

type Message = { role: "user" | "assistant"; content: string; result?: ChatResult };

export function ChatPage() {
  const [question, setQuestion] = useState("What is ContextOps AI required to do?");
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    const currentQuestion = question.trim();
    setMessages((items) => [...items, { role: "user", content: currentQuestion }]);
    setQuestion("");
    setLoading(true);
    const response = await api.post<ChatResult>("/chat", { question: currentQuestion, conversation_id: conversationId });
    setConversationId(response.data.conversation_id);
    setMessages((items) => [...items, { role: "assistant", content: response.data.answer, result: response.data }]);
    setLoading(false);
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>AI Chat</h1>
          <p>Grounded answers with chunk-level citations and hallucination risk scoring.</p>
        </div>
      </header>
      <div className="chat-layout">
        <div className="chat-stream">
          {messages.length === 0 ? <div className="empty-state">Upload a document, then ask a question about approved knowledge.</div> : null}
          {messages.map((message, index) => (
            <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <p>{message.content}</p>
              {message.result ? (
                <div className="citation-strip">
                  <span>Confidence {Math.round(message.result.confidence_score * 100)}%</span>
                  <span>Risk {Math.round(message.result.hallucination_risk * 100)}%</span>
                  <span>{message.result.latency_ms} ms</span>
                </div>
              ) : null}
              {message.result?.sources.map((source) => (
                <blockquote key={source.chunk_id}>
                  {source.filename} chunk {source.chunk_index + 1}: {source.excerpt}
                </blockquote>
              ))}
            </article>
          ))}
          {loading ? <div className="message assistant">Thinking with retrieved context...</div> : null}
        </div>
        <form className="composer" onSubmit={ask}>
          <ShieldAlert size={18} />
          <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a grounded enterprise question" />
          <button className="icon-button primary" title="Send">
            <Send size={18} />
          </button>
        </form>
      </div>
    </section>
  );
}
