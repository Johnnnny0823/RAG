import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import "./style.css";

type Status = "loading" | "ready" | "database" | "api";

const statusText: Record<Status, string> = {
  loading: "正在檢查服務狀態…",
  ready: "API、資料庫與向量擴充功能已就緒。",
  database: "資料庫或向量擴充功能目前無法使用。",
  api: "目前無法取得 API 狀態。",
};

async function readStatus(signal: AbortSignal): Promise<Status> {
  const response = await fetch("/api/v1/ready", {
    signal: AbortSignal.any([signal, AbortSignal.timeout(6000)]),
    cache: "no-store",
  });
  const body = await response.json();
  if (response.ok && body?.status === "ready") return "ready";
  if (response.status === 503 && body?.error?.code === "DATABASE_UNAVAILABLE") {
    return "database";
  }
  return "api";
}

function App() {
  const [status, setStatus] = useState<Status>("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    readStatus(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setStatus(result);
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("api");
      });
    return () => controller.abort();
  }, [attempt]);

  return (
    <main className="mx-auto max-w-2xl px-6 py-16 text-slate-900">
      <h1 className="text-3xl font-semibold">PatentScope AI</h1>
      <p className="mt-3 text-slate-700">台灣專利研究平台 · 本機開發環境</p>
      <section className="mt-8 rounded-lg border border-slate-300 p-5">
        <h2 className="text-lg font-semibold">服務狀態</h2>
        <p className="mt-2" role="status">{statusText[status]}</p>
        <button
          className="mt-4 rounded bg-slate-900 px-4 py-2 text-white focus-visible:outline-2 focus-visible:outline-offset-4 disabled:opacity-70"
          disabled={status === "loading"}
          onClick={() => {
            setStatus("loading");
            setAttempt(attempt + 1);
          }}
        >
          重新檢查
        </button>
      </section>
      <p className="mt-5 text-sm text-slate-700">目前語料庫尚未建立，專利搜尋將於後續里程碑提供。</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
