import { RefreshCw, UploadCloud } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type DocumentRecord } from "../lib/api";

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setStatus("Uploading and indexing...");
    const response = await api.post<DocumentRecord>("/documents/upload", formData);
    setStatus(`${response.data.filename} is ${response.data.status}.`);
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Document Upload</h1>
          <p>Upload PDF, TXT, or CSV assets for extraction, chunking, embedding, and retrieval.</p>
        </div>
      </header>
      <form className="upload-zone" onSubmit={upload}>
        <UploadCloud size={42} />
        <input type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <button className="primary-button">Upload and index</button>
        {status ? <span>{status}</span> : null}
      </form>
    </section>
  );
}

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);

  async function load() {
    const response = await api.get<DocumentRecord[]>("/documents");
    setDocuments(response.data);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Document Management</h1>
          <p>Review ingestion status and indexed knowledge sources.</p>
        </div>
        <button className="secondary-button" onClick={load}>
          <RefreshCw size={16} /> Refresh
        </button>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>{document.filename}</td>
                <td>{document.content_type}</td>
                <td><span className={`pill ${document.status}`}>{document.status}</span></td>
                <td>{new Date(document.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
