import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Research } from "./research";
import { CorpusDashboard, type CorpusStatus } from "./corpus-dashboard";

import "./style.css";

type Status = "loading" | "ready" | "database" | "api";
type InstallPrompt = Event & { prompt(): Promise<unknown> };

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
  const [corpus, setCorpus] = useState<CorpusStatus | null>(null);
  const [online, setOnline] = useState(navigator.onLine);
  const [installPrompt, setInstallPrompt] = useState<InstallPrompt | null>(null);

  useEffect(() => {
    const updateNetwork = () => setOnline(navigator.onLine);
    const offerInstall = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as InstallPrompt);
    };
    window.addEventListener("online", updateNetwork);
    window.addEventListener("offline", updateNetwork);
    window.addEventListener("beforeinstallprompt", offerInstall);
    return () => {
      window.removeEventListener("online", updateNetwork);
      window.removeEventListener("offline", updateNetwork);
      window.removeEventListener("beforeinstallprompt", offerInstall);
    };
  }, []);

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

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v1/corpus/status", { signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then((body: CorpusStatus | null) => { if (!controller.signal.aborted) setCorpus(body); })
      .catch(() => { if (!controller.signal.aborted) setCorpus(null); });
    return () => controller.abort();
  }, [attempt]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 text-slate-900 sm:px-8">
      <header className="mb-8 border-b border-slate-200 pb-6">
        <p className="mb-2 text-sm font-semibold text-teal-800">臺灣專利研究平台</p>
        <h1 className="text-3xl font-semibold sm:text-4xl">PatentScope AI</h1>
        {installPrompt && <button className="mt-3" type="button" onClick={() => {
          setInstallPrompt(null);
          void installPrompt.prompt().catch(() => undefined);
        }}>安裝 PatentScope AI</button>}
        {!online && <p className="mt-3 text-sm" role="status">目前離線。搜尋及存取研究紀錄需要連線。</p>}
      </header>
      <Research />
      {corpus && <CorpusDashboard corpus={corpus} />}
      <section className="mt-8 rounded-lg border border-slate-300 bg-white p-5">
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
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  void navigator.serviceWorker.register("/sw.js").catch(() => undefined);
}
