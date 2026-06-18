import axios from "axios";

export const api = axios.create({ baseURL: "/" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("contextops_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: "admin" | "analyst" | "business_user" | "compliance_user";
  is_active: boolean;
};

export type DocumentRecord = {
  id: number;
  filename: string;
  content_type: string;
  status: "uploaded" | "processing" | "indexed" | "failed";
  error_message?: string | null;
  created_at: string;
};

export type ChatSource = {
  document_id: number;
  filename: string;
  chunk_id: number;
  chunk_index: number;
  score: number;
  excerpt: string;
};

export type ChatResult = {
  conversation_id: number;
  answer: string;
  sources: ChatSource[];
  confidence_score: number;
  hallucination_risk: number;
  latency_ms: number;
};
