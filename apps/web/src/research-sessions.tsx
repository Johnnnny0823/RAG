import { useState } from "react";
import { MAX_INVENTION_LENGTH } from "./invention";
import type { Feature } from "./research";

type Session = { id: string; title: string };
type Analysis = { features: Feature[]; model_name: string; analysis_version: string };
type Message = { id: string } & (
  { role: "user"; content: string } | { role: "assistant"; content: Analysis }
);
type Props = {
  projectId: string;
  token: string;
  request: <T>(path: string, payload?: object, token?: string, method?: string) => Promise<T>;
  run: (label: string, operation: () => Promise<void>) => Promise<void>;
  busy: boolean;
  onUse: (query: string, features: Feature[]) => void;
};
const messageLimit = 40;

export function ResearchSessions({ projectId, token, request, run, busy, onUse }: Props) {
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [active, setActive] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [hasOlder, setHasOlder] = useState(false);
  const [idea, setIdea] = useState("");
  const [applied, setApplied] = useState("");
  const [confirmRemoval, setConfirmRemoval] = useState(false);
  const [removed, setRemoved] = useState(false);

  async function loadSessions() {
    setSessions(await request<Session[]>(`/sessions?project_id=${projectId}&limit=100`, undefined, token));
  }

  async function openSession(session: Session) {
    const rows = await request<Message[]>(`/sessions/${session.id}/messages?limit=${messageLimit}`, undefined, token);
    setActive(session);
    setMessages(rows);
    setHasOlder(rows.length === messageLimit);
    setIdea("");
    setApplied("");
    setConfirmRemoval(false);
    setRemoved(false);
  }

  async function createSession(title: string) {
    const session = await request<Session>("/sessions", { project_id: projectId, title }, token);
    await openSession(session);
    await loadSessions();
  }

  async function loadOlder(session: Session) {
    const rows = await request<Message[]>(`/sessions/${session.id}/messages?limit=${messageLimit}&before=${messages[0].id}`, undefined, token);
    setMessages([...rows, ...messages]);
    setHasOlder(rows.length === messageLimit);
  }

  async function analyzeIdea(session: Session) {
    const turn = await request<Message[]>(`/sessions/${session.id}/messages`, { query: idea.trim() }, token);
    setMessages([...messages, ...turn]);
    setIdea("");
    setApplied("");
  }

  async function deleteSession(session: Session) {
    await request<void>(`/sessions/${session.id}`, undefined, token, "DELETE");
    setSessions((current) => current?.filter((item) => item.id !== session.id) ?? null);
    setActive(null);
    setMessages([]);
    setHasOlder(false);
    setIdea("");
    setApplied("");
    setConfirmRemoval(false);
    setRemoved(true);
  }

  return <section className="my-4 rounded-lg border border-slate-200 p-3">
    <h3>AI Session</h3>
    <p className="my-2 text-sm">提交後會在此專案保存構想及本機 AI 拆解。每次拆解只分析該次輸入。</p>
    <button disabled={busy} onClick={() => void run("正在載入 AI Session…", loadSessions)}>載入 AI Session</button>
    {removed && <p role="status" className="my-2 text-sm text-teal-900">已刪除 AI Session 與訊息。</p>}
    {sessions?.length === 0 && <p className="my-2">此專案還沒有 AI Session。</p>}
    {!!sessions?.length && <ul className="my-2 flex flex-wrap gap-2">
      {sessions.map((session) => <li key={session.id}>
        <button disabled={busy} onClick={() => void run("正在讀取 AI Session…", () => openSession(session))}>{session.title}</button>
      </li>)}
    </ul>}
    <form className="my-3" onSubmit={(event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const title = String(new FormData(form).get("title")).trim();
      if (title) void run("正在建立 AI Session…", async () => { await createSession(title); form.reset(); });
    }}>
      <fieldset disabled={busy}>
        <label className="research-field">Session 名稱<input name="title" maxLength={120} required /></label>
        <button type="submit">建立 AI Session</button>
      </fieldset>
    </form>
    {active && <div className="border-t border-slate-200 pt-3">
      <h4 className="font-semibold break-words">目前 Session · {active.title}</h4>
      {confirmRemoval ? <div className="my-2">
        <p className="mb-2 text-sm">這會永久刪除此 Session 的構想和技術草稿。另行保存的搜尋及報告副本由各自位置管理。</p>
        <div className="flex flex-wrap gap-2">
          <button disabled={busy} onClick={() => void run("正在刪除 AI Session…", () => deleteSession(active))}>確認刪除 AI Session</button>
          <button disabled={busy} onClick={() => setConfirmRemoval(false)}>取消刪除 AI Session</button>
        </div>
      </div> : <button className="my-2" disabled={busy} onClick={() => setConfirmRemoval(true)}>刪除 AI Session</button>}
      {!messages.length && <p className="my-2 text-sm">尚無分析紀錄。</p>}
      {hasOlder && <button className="my-2" disabled={busy} onClick={() => void run("正在讀取較早的紀錄…", () => loadOlder(active))}>較早的分析紀錄</button>}
      <ol className="my-3 space-y-2">
        {messages.map((message, index) => {
          if (message.role === "user") return <li key={message.id} className="break-words"><strong>構想 · </strong>{message.content}</li>;
          const previous = messages[index - 1];
          const { features, model_name, analysis_version } = message.content;
          return <li key={message.id} className="rounded-lg bg-slate-50 p-3">
            <p className="mb-2 text-sm font-medium">AI 技術草稿 · {model_name} · {analysis_version}</p>
            <ul className="space-y-2 text-sm">
              {features.map((feature) => <li className="break-words" key={feature.feature_id}>
                {feature.description_zh} · {[...feature.keywords_zh, ...feature.keywords_en].join("、")}
              </li>)}
            </ul>
            {previous?.role === "user" && <button className="mt-2" disabled={busy} onClick={() => {
              onUse(previous.content, features);
              setApplied(message.id);
            }}>帶入檢索表單</button>}
            {applied === message.id && <p role="status" className="mt-2 text-sm">已帶入構想及技術草稿，可在檢索前編輯。</p>}
          </li>;
        })}
      </ol>
      <form onSubmit={(event) => {
        event.preventDefault();
        if (idea.trim() && !busy) void run("正在拆解並保存至 AI Session…", () => analyzeIdea(active));
      }}>
        <label className="research-field">Session 構想（最多 {MAX_INVENTION_LENGTH} 字）
          <textarea value={idea} onChange={(event) => setIdea(event.target.value)} disabled={busy} maxLength={MAX_INVENTION_LENGTH} rows={4} required />
        </label>
        <button type="submit" disabled={busy || !idea.trim()}>拆解並保存至 Session</button>
      </form>
    </div>}
  </section>;
}
