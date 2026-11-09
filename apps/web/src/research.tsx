import { useState } from "react";
import { ResearchSessions } from "./research-sessions";

export type Feature = {
  feature_id: string;
  description_zh: string;
  keywords_zh: string[];
  keywords_en: string[];
  must_have: boolean;
  confidence: "low" | "medium" | "high";
  ipc_candidates: string[];
};
type Draft = Omit<Feature, "keywords_zh" | "keywords_en"> & {
  keywords_zh: string;
  keywords_en: string;
};
type PatentVersion = {
  document_id: string;
  publication_no: string;
  application_no: string;
  document_stage: string;
  kind_code: string | null;
  publication_date: string | null;
  filing_date: string | null;
  title_zh: string | null;
  title_en: string | null;
  content_scope: string;
};
type Bookmark = PatentVersion & { note: string };
type Hit = PatentVersion & {
  lexical_rank: number | null;
  semantic_rank: number | null;
  fusion_rank: number;
  rerank_rank: number | null;
};
type Party = { zh: string | null; en: string | null };
type Detail = {
  abstract_zh: string | null;
  abstract_en: string | null;
  applicants: Party[];
  inventors: Party[];
  classifications: { scheme: string; code: string }[];
  sections: { ordinal: number; section_type: string; original_text: string }[];
  sources: { dataset_name: string; publisher: string; dataset_url: string | null; source_url: string | null; batch_key: string; ingested_at: string }[];
};
type Claim = { claim_number: number; text: string };
type Search = { query: string; ipc: string | null; features: Feature[]; rerank: boolean; offset: number };
type Results = { items: Hit[]; has_more: boolean; limit: number; offset: number };
type RunSummary = { id: string; created_at: string; project_id: string | null };
type Project = { id: string; name: string; description: string };
type SavedRun = RunSummary & {
  request: Search & { limit: number };
  items: Hit[];
  comparisons: Comparison[];
};
const verdicts = {
  supported: "有明確證據",
  partially_supported: "部分符合",
  uncertain: "不確定",
  not_found_in_checked_content: "未找到證據",
};
type Comparison = {
  document_id: string;
  passages_checked: number;
  items: {
    feature_id: string;
    verdict: keyof typeof verdicts;
    basis: string;
    evidence: { quote: string; xpath: string; artifact_sha256: string; char_start: number; char_end: number } | null;
  }[];
};

const stage: Record<string, string> = { publication: "公開", grant: "公告" };
const scope: Record<string, string> = {
  fulltext: "全文",
  metadata_and_abstract: "書目與摘要",
  claims_only: "請求項",
};
const splitTerms = (value: string) => value.split(/[,，、\n]/).map((word) => word.trim()).filter(Boolean);
const names = (parties: Party[]) => parties.map((party) => party.zh || party.en).filter(Boolean).join("、") || "未提供";
const title = (hit: PatentVersion) => hit.title_zh || hit.title_en || hit.publication_no;

class SessionExpired extends Error {}

async function request<T>(path: string, payload?: object, token?: string, method = payload ? "POST" : "GET"): Promise<T> {
  const headers = new Headers();
  if (payload) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", "Bearer " + token);
  const response = await fetch("/api/v1" + path, {
    cache: "no-store",
    headers,
    method,
    signal: AbortSignal.timeout(180_000),
    ...(payload && {
      body: JSON.stringify(payload),
    }),
  });
  if (!response.ok) {
    if (token && response.status === 401) throw new SessionExpired("登入已失效，請重新登入。");
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || `服務回應錯誤（HTTP ${response.status}）`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export function Research() {
  const [query, setQuery] = useState("");
  const [ipc, setIpc] = useState("");
  const [rerank, setRerank] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState<Search | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [selected, setSelected] = useState<{ hit: PatentVersion; detail: Detail; claims: Claim[]; fromResults: boolean } | null>(null);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [session, setSession] = useState<{ token: string; email: string } | null>(null);
  const [registering, setRegistering] = useState(false);
  const [history, setHistory] = useState<RunSummary[] | null>(null);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [saved, setSaved] = useState<SavedRun | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectFilter, setProjectFilter] = useState("");
  const [confirmProjectRemoval, setConfirmProjectRemoval] = useState(false);
  const [projectMessage, setProjectMessage] = useState("");
  const activeProject = projects.find((project) => project.id === projectFilter);
  const [assignment, setAssignment] = useState("");
  const [bookmarks, setBookmarks] = useState<Bookmark[] | null>(null);
  const [bookmarkOffset, setBookmarkOffset] = useState(0);
  const [bookmarkProject, setBookmarkProject] = useState("");
  const [bookmarkMessage, setBookmarkMessage] = useState("");
  const [pendingRemoval, setPendingRemoval] = useState<string | null>(null);

  function leaveAccount() {
    setSession(null);
    setHistory(null);
    setHistoryOffset(0);
    setSaved(null);
    setProjects([]);
    setProjectFilter("");
    setConfirmProjectRemoval(false);
    setProjectMessage("");
    setAssignment("");
    setBookmarks(null);
    setBookmarkOffset(0);
    setBookmarkProject("");
    setBookmarkMessage("");
    setPendingRemoval(null);
    setSearch(null);
    setResults(null);
    setSelected(null);
    setComparison(null);
    setQuery("");
    setIpc("");
    setRerank(false);
    setDrafts([]);
    setError("");
  }

  async function signIn(credentials: { email: string; password: string }) {
    if (registering) {
      await request("/auth/register", credentials);
      setRegistering(false);
    }
    const { access_token } = await request<{ access_token: string }>("/auth/login", credentials);
    const account = await request<{ email: string }>("/me", undefined, access_token);
    const accountProjects = await request<Project[]>("/projects?limit=100", undefined, access_token);
    leaveAccount();
    setSession({ token: access_token, email: account.email });
    setProjects(accountProjects);
  }

  async function loadHistory(token: string, offset = 0) {
    const filter = projectFilter ? "&project_id=" + encodeURIComponent(projectFilter) : "";
    const rows = await request<RunSummary[]>(`/search-runs?limit=21&offset=${offset}${filter}`, undefined, token);
    setHistory(rows);
    setHistoryOffset(offset);
  }

  function showSavedPage(record: SavedRun, offset = 0) {
    const limit = record.request.limit;
    setSearch(record.request);
    setResults({ items: record.items.slice(offset, offset + limit), offset, limit, has_more: offset + limit < record.items.length });
    setSelected(null);
    setComparison(null);
  }

  async function openRun(id: string, token: string) {
    const record = await request<SavedRun>("/search-runs/" + id, undefined, token);
    setSaved(record);
    setAssignment(record.project_id ?? "");
    showSavedPage(record);
  }

  async function createProject(payload: { name: string; description: string }, token: string) {
    const project = await request<Project>("/projects", payload, token);
    setProjects([project, ...projects].slice(0, 100));
  }

  function selectProject(projectId: string) {
    setProjectFilter(projectId);
    setConfirmProjectRemoval(false);
    setProjectMessage("");
    setHistory(null);
    setHistoryOffset(0);
    setBookmarks(null);
    setBookmarkOffset(0);
    setBookmarkMessage("");
    setPendingRemoval(null);
  }

  async function editProject(projectId: string, payload: { name: string; description: string }, token: string) {
    const updated = await request<Project>(`/projects/${projectId}`, payload, token, "PATCH");
    setProjects((current) => current.map((project) => project.id === updated.id ? updated : project));
    setProjectMessage("專案資料已更新。");
  }

  async function deleteProject(projectId: string, token: string) {
    await request<void>(`/projects/${projectId}`, undefined, token, "DELETE");
    setProjects((current) => current.filter((project) => project.id !== projectId));
    if (bookmarkProject === projectId) setBookmarkProject("");
    if (assignment === projectId) setAssignment("");
    selectProject("");
    setProjectMessage("空白專案已刪除。");
  }

  async function assignProject(record: SavedRun, token: string) {
    const updated = await request<RunSummary>(`/search-runs/${record.id}/project`, {
      project_id: assignment || null,
    }, token, "PATCH");
    setSaved({ ...record, project_id: updated.project_id });
    setHistory(null);
    setHistoryOffset(0);
  }

  async function loadBookmarks(projectId: string, token: string, offset = 0) {
    const rows = await request<Bookmark[]>(`/projects/${projectId}/patents?limit=21&offset=${offset}`, undefined, token);
    setBookmarks(rows);
    setBookmarkOffset(offset);
  }

  async function addBookmark(documentId: string, token: string) {
    await request(`/projects/${bookmarkProject}/patents/${documentId}`, {}, token, "PUT");
    setBookmarkMessage("已收藏此文件版本。");
  }

  async function updateBookmark(documentId: string, token: string, note: string) {
    const updated = await request<{ note: string }>(`/projects/${projectFilter}/patents/${documentId}`, { note }, token, "PATCH");
    setBookmarks((current) => current?.map((item) => item.document_id === documentId ? { ...item, note: updated.note } : item) ?? null);
    setBookmarkMessage("筆記已保存。");
  }

  async function removeBookmark(documentId: string, token: string) {
    await request(`/projects/${projectFilter}/patents/${documentId}`, undefined, token, "DELETE");
    setPendingRemoval(null);
    setBookmarkMessage("已移除收藏及其筆記。");
    setBookmarks(null);
    await loadBookmarks(projectFilter, token);
  }

  async function run(label: string, operation: () => Promise<void>) {
    setBusy(label);
    setError("");
    try {
      await operation();
    } catch (failure) {
      if (failure instanceof SessionExpired) leaveAccount();
      setError(failure instanceof TypeError ? "無法連線至服務，請重試。"
        : failure instanceof DOMException && failure.name === "TimeoutError" ? "服務回應逾時，請重試。"
        : failure instanceof Error ? failure.message : "操作失敗，請重試。");
    } finally {
      setBusy("");
    }
  }

  function changeDraft(id: string, change: Partial<Draft>) {
    setDrafts(drafts.map((draft) => draft.feature_id === id ? { ...draft, ...change } : draft));
  }

  function addDraft() {
    const feature_id = ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9"]
      .find((id) => !drafts.some((draft) => draft.feature_id === id));
    if (!feature_id || drafts.length >= 5) return;
    setDrafts([...drafts, {
      feature_id, description_zh: "", keywords_zh: "", keywords_en: "",
      must_have: false, confidence: "low", ipc_candidates: [],
    }]);
  }

  async function analyze() {
    const data = await request<{ features: Feature[] }>("/queries/analyze", { query: query.trim() });
    setDrafts(data.features.map((feature) => ({
      ...feature, keywords_zh: feature.keywords_zh.join("，"), keywords_en: feature.keywords_en.join(", "),
    })));
  }

  async function loadResults(next: Search) {
    const data = await request<Results>("/patents/search/hybrid", next);
    setSearch(next);
    setSaved(null);
    setResults(data);
    setSelected(null);
    setComparison(null);
  }

  async function submitSearch(save: boolean) {
    const features = drafts.map((draft) => ({
      ...draft, keywords_zh: splitTerms(draft.keywords_zh), keywords_en: splitTerms(draft.keywords_en),
    }));
    if (features.some((feature) => !feature.description_zh.trim() ||
      [feature.keywords_zh, feature.keywords_en].some((terms) => terms.length > 4 || terms.some((term) => term.length > 48)))) {
      throw new Error("每項特徵須填寫描述。每種語言最多四個檢索詞，每詞最多 48 字。");
    }
    const payload = { query: query.trim(), ipc: ipc.trim() || null, features, rerank, offset: 0 };
    if (save && session) {
      const { id } = await request<RunSummary>("/search-runs", payload, session.token);
      setHistory(null);
      await openRun(id, session.token);
      return;
    }
    await loadResults(payload);
  }

  async function openPatent(hit: PatentVersion, fromResults = true) {
    const path = "/patents/" + hit.document_id;
    const [detail, claims] = await Promise.all([request<Detail>(path), request<{ claims: Claim[] }>(path + "/claims")]);
    setSelected({ hit, detail, claims: claims.claims, fromResults });
    setBookmarkProject(fromResults ? saved?.project_id ?? projectFilter : projectFilter);
    setBookmarkMessage("");
    setComparison(fromResults ? saved?.comparisons.find((item) => item.document_id === hit.document_id) ?? null : null);
  }

  async function comparePatent(documentId: string, features: Feature[]) {
    if (saved && session) {
      const result = await request<Comparison>(`/search-runs/${saved.id}/comparisons/${documentId}`, {}, session.token);
      setSaved({ ...saved, comparisons: [...saved.comparisons.filter((item) => item.document_id !== documentId), result] });
      setComparison(result);
      return;
    }
    setComparison(await request<Comparison>(`/patents/${documentId}/compare`, { features }));
  }

  function navigateResults(offset: number) {
    if (saved) showSavedPage(saved, offset);
    else if (search) void run("正在檢索專利…", () => loadResults({ ...search, offset }));
  }

  return (
    <>
      <p className="mb-6 max-w-3xl text-slate-700">描述你的構想，從已索引的 TIPO 公開資料找出相關技術。涵蓋範圍以本機已匯入的批次為限。比對僅供研究參考。</p>
      <p className="mb-4 font-medium text-teal-900" role="status">{busy}</p>
      {error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-red-900" role="alert">{error}</p>}
      <section className="research-panel mb-6">
        <h2>私人搜尋歷史</h2>
        {session ? <>
          <p className="my-2 break-all text-sm">目前帳號 · {session.email}</p>
          <details className="my-3">
            <summary>建立研究專案</summary>
            <form className="my-3" onSubmit={(event) => {
              event.preventDefault();
              const form = event.currentTarget;
              const data = new FormData(form);
              void run("正在建立專案…", async () => {
                await createProject({ name: String(data.get("name")), description: String(data.get("description")) }, session.token);
                form.reset();
              });
            }}>
              <fieldset disabled={!!busy}>
                <label className="research-field">專案名稱<input name="name" required maxLength={120} /></label>
                <label className="research-field">專案說明<textarea name="description" rows={2} maxLength={2000} /></label>
                <button type="submit">新增研究專案</button>
              </fieldset>
            </form>
          </details>
          <label className="research-field">依研究專案篩選
            <select value={projectFilter} disabled={!!busy} onChange={(event) => selectProject(event.target.value)}>
              <option value="">所有搜尋紀錄</option>
              {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
            </select>
          </label>
          {projectMessage && <p role="status" className="my-2 text-sm text-teal-900">{projectMessage}</p>}
          {activeProject && <>
            <p className="my-2 whitespace-pre-wrap break-words text-sm">{activeProject.description}</p>
            <details className="my-3" key={activeProject.id}>
              <summary>管理研究專案</summary>
              <form className="my-3" onSubmit={(event) => {
                event.preventDefault();
                const data = new FormData(event.currentTarget);
                void run("正在更新研究專案…", () => editProject(activeProject.id, {
                  name: String(data.get("name")), description: String(data.get("description")),
                }, session.token));
              }}>
                <fieldset disabled={!!busy}>
                  <label className="research-field">修改專案名稱<input name="name" defaultValue={activeProject.name} maxLength={120} required /></label>
                  <label className="research-field">修改專案說明<textarea name="description" defaultValue={activeProject.description} rows={2} maxLength={2000} /></label>
                  <button type="submit">保存專案資料</button>
                </fieldset>
              </form>
              <p className="mb-2 text-sm">僅可刪除沒有搜尋紀錄、收藏或 AI Session 的專案。</p>
              {confirmProjectRemoval ? <div className="flex flex-wrap gap-2">
                <button disabled={!!busy} onClick={() => void run("正在刪除研究專案…", () => deleteProject(activeProject.id, session.token))}>確認刪除空白專案</button>
                <button disabled={!!busy} onClick={() => setConfirmProjectRemoval(false)}>取消刪除專案</button>
              </div> : <button disabled={!!busy} onClick={() => setConfirmProjectRemoval(true)}>刪除空白專案</button>}
            </details>
          </>}
          {projectFilter && <ResearchSessions key={projectFilter} projectId={projectFilter} token={session.token}
            request={request} run={run} busy={!!busy} onUse={(idea, features) => {
              setQuery(idea);
              setDrafts(features.map((feature) => ({
                ...feature, keywords_zh: feature.keywords_zh.join("，"), keywords_en: feature.keywords_en.join(", "),
              })));
            }} />}
          {projectFilter && <section className="my-4 rounded-lg border border-slate-200 p-3">
            <h3>專案收藏</h3>
            <button className="my-2" disabled={!!busy} onClick={() => void run("正在載入收藏…", () => loadBookmarks(projectFilter, session.token))}>載入專案收藏</button>
            {bookmarkMessage && <p role="status" className="text-sm text-teal-900">{bookmarkMessage}</p>}
            {bookmarks?.length === 0 && <p>此專案還沒有收藏。</p>}
            {bookmarks?.slice(0, 20).map((item) => <article className="my-3 border-t border-slate-200 pt-3" key={item.document_id}>
              <p className="text-sm">{stage[item.document_stage]} {item.publication_no} {item.kind_code} · {scope[item.content_scope]}</p>
              <button className="my-2" disabled={!!busy} onClick={() => void run("正在載入收藏詳情…", () => openPatent(item, false))}>{title(item)}</button>
              <form onSubmit={(event) => {
                event.preventDefault();
                const note = String(new FormData(event.currentTarget).get("note"));
                void run("正在保存筆記…", () => updateBookmark(item.document_id, session.token, note));
              }}>
                <label className="research-field">私人筆記 · {item.publication_no}
                  <textarea key={item.note} name="note" defaultValue={item.note} maxLength={4000} rows={2} disabled={!!busy} />
                </label>
                <div className="flex flex-wrap gap-2">
                  <button disabled={!!busy} type="submit">保存筆記</button>
                  {pendingRemoval === item.document_id ? <>
                    <button disabled={!!busy} type="button" onClick={() => void run("正在移除收藏…", () => removeBookmark(item.document_id, session.token))}>確認移除收藏及筆記</button>
                    <button disabled={!!busy} type="button" onClick={() => setPendingRemoval(null)}>取消移除</button>
                  </> : <button disabled={!!busy} type="button" onClick={() => setPendingRemoval(item.document_id)}>移除收藏</button>}
                </div>
              </form>
            </article>)}
            {!!bookmarks?.length && <div className="flex gap-2">
              <button disabled={!!busy || bookmarkOffset === 0} onClick={() => void run("正在載入收藏…", () => loadBookmarks(projectFilter, session.token, bookmarkOffset - 20))}>上一頁收藏</button>
              <button disabled={!!busy || bookmarks.length < 21} onClick={() => void run("正在載入收藏…", () => loadBookmarks(projectFilter, session.token, bookmarkOffset + 20))}>下一頁收藏</button>
            </div>}
          </section>}
          <div className="flex flex-wrap gap-2">
            <button disabled={!!busy} onClick={() => void run("正在讀取歷史…", () => loadHistory(session.token))}>載入搜尋歷史</button>
            <button disabled={!!busy} onClick={leaveAccount}>登出此頁</button>
          </div>
          {history?.length === 0 && <p className="mt-3">{projectFilter ? "此專案還沒有搜尋紀錄。" : "此帳號還沒有保存的搜尋。"}</p>}
          {!!history?.length && <>
            <ul className="my-3 space-y-2">
              {history.slice(0, 20).map((item) => <li key={item.id}>
                <button disabled={!!busy} onClick={() => void run("正在開啟搜尋紀錄…", () => openRun(item.id, session.token))}>
                  {new Date(item.created_at).toLocaleString("zh-TW")} · {item.id.slice(0, 8)}
                </button>
              </li>)}
            </ul>
            <div className="flex gap-2">
              <button disabled={!!busy || historyOffset === 0} onClick={() => void run("正在讀取歷史…", () => loadHistory(session.token, historyOffset - 20))}>較新紀錄</button>
              <button disabled={!!busy || history.length < 21} onClick={() => void run("正在讀取歷史…", () => loadHistory(session.token, historyOffset + 20))}>較舊紀錄</button>
            </div>
          </>}
        </> : <>
          <p className="my-2 text-sm">登入可主動保存查詢與比對。重新整理頁面後需重新登入。</p>
          <form onSubmit={(event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const data = new FormData(form);
            const credentials = { email: String(data.get("email")), password: String(data.get("password")) };
            form.reset();
            void run(registering ? "正在註冊…" : "正在登入…", () => signIn(credentials));
          }}>
            <fieldset disabled={!!busy}>
              <div className="grid gap-x-4 sm:grid-cols-2">
                <label className="research-field">電子郵件
                  <input name="email" type="email" required maxLength={254} autoComplete="username" />
                </label>
                <label className="research-field">密碼（至少 12 字元）
                  <input name="password" type="password" required minLength={12} maxLength={128} autoComplete={registering ? "new-password" : "current-password"} />
                </label>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="submit">{registering ? "註冊並登入" : "登入"}</button>
                <button type="button" onClick={() => { setRegistering(!registering); setError(""); }}>{registering ? "返回登入" : "建立帳號"}</button>
              </div>
            </fieldset>
          </form>
        </>}
      </section>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <section className="research-panel">
          <h2>發明構想</h2>
          <form onSubmit={(event) => { event.preventDefault(); if (!busy && query.trim()) void run("正在檢索專利…", () => submitSearch(false)); }}>
            <fieldset disabled={!!busy}>
              <label className="research-field">構想描述（最多 160 字）
                <textarea rows={4} value={query} maxLength={160} required onChange={(event) => setQuery(event.target.value)} />
              </label>
              <button type="button" disabled={!query.trim()} onClick={() => void run("正在拆解技術特徵…", analyze)}>AI 拆解技術特徵</button>
              <h3 className="mt-5">技術特徵</h3>
              {drafts.length === 0 && <p className="my-2 text-sm text-slate-700">可先讓 AI 草擬，也可自行新增。</p>}
              {drafts.map((draft, index) => (
                <fieldset key={draft.feature_id} className="my-3 min-w-0 rounded-lg border border-slate-300 p-3">
                  <legend className="px-1 font-medium">特徵 {index + 1}</legend>
                  <label className="research-field">特徵描述
                    <input value={draft.description_zh} maxLength={160} onChange={(event) => changeDraft(draft.feature_id, { description_zh: event.target.value })} />
                  </label>
                  <label className="research-field">繁中檢索詞（逗號分隔）
                    <input value={draft.keywords_zh} onChange={(event) => changeDraft(draft.feature_id, { keywords_zh: event.target.value })} />
                  </label>
                  <label className="research-field">英文檢索詞（逗號分隔）
                    <input value={draft.keywords_en} onChange={(event) => changeDraft(draft.feature_id, { keywords_en: event.target.value })} />
                  </label>
                  {!!draft.ipc_candidates.length && <p className="mb-2 text-sm">IPC 候選 · {draft.ipc_candidates.join("、")}</p>}
                  <div className="flex flex-wrap items-center gap-3">
                    <label><input type="checkbox" checked={draft.must_have} onChange={(event) => changeDraft(draft.feature_id, { must_have: event.target.checked })} /> 必要特徵</label>
                    <button type="button" aria-label={`刪除特徵 ${index + 1}`} onClick={() => setDrafts(drafts.filter((item) => item.feature_id !== draft.feature_id))}>刪除</button>
                  </div>
                </fieldset>
              ))}
              <button type="button" disabled={drafts.length >= 5} onClick={addDraft}>新增特徵</button>
              <label className="research-field mt-5">IPC 篩選（選填）
                <input value={ipc} maxLength={24} onChange={(event) => setIpc(event.target.value)} />
              </label>
              <label className="my-3 block"><input type="checkbox" checked={rerank} onChange={(event) => setRerank(event.target.checked)} /> 使用本機模型重排序</label>
              <button className="research-primary" disabled={!query.trim()} type="submit">搜尋臺灣專利</button>
              {session && <button className="ml-2" type="button" disabled={!query.trim()} onClick={() => void run("正在檢索並保存…", () => submitSearch(true))}>搜尋並保存</button>}
            </fieldset>
          </form>
        </section>
        <section className="research-panel" aria-busy={busy === "正在檢索專利…"}>
          <h2>檢索結果</h2>
          {!results && <p className="mt-3 text-slate-700">完成搜尋後，這裡會顯示候選文件與排序資訊。</p>}
          {search && results && <>
            <p className="my-3 break-words text-slate-700">{saved ? "已保存的查詢" : "本次查詢"} · {search.query}{search.ipc && ` · IPC ${search.ipc}`}</p>
            {saved && session && <div className="mb-3">
              <p className="mb-2 break-words text-sm">目前歸檔 · {projects.find((project) => project.id === saved.project_id)?.name ?? saved.project_id ?? "未歸檔"}</p>
              <label className="research-field">歸檔至研究專案
                <select disabled={!!busy} value={assignment} onChange={(event) => setAssignment(event.target.value)}>
                  <option value="">未歸檔</option>
                  {saved.project_id && !projects.some((project) => project.id === saved.project_id) &&
                    <option value={saved.project_id}>{saved.project_id}</option>}
                  {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
                </select>
              </label>
              <button disabled={!!busy || assignment === (saved.project_id ?? "")} onClick={() => void run("正在更新歸檔…", () => assignProject(saved, session.token))}>更新歸檔</button>
            </div>}
            {saved && <details className="mb-3">
              <summary>已保存的檢索策略</summary>
              <p className="my-2 text-sm">本機重排序 · {search.rerank ? "啟用" : "停用"}</p>
              {search.features.length ? <ul className="space-y-2 text-sm">
                {search.features.map((feature) => <li key={feature.feature_id} className="break-words">
                  <strong>{feature.description_zh}</strong> · {feature.must_have ? "必要" : "選用"}
                  <p>{[...feature.keywords_zh, ...feature.keywords_en].join("、") || "未提供檢索詞"}</p>
                </li>)}
              </ul> : <p className="text-sm">此查詢未包含技術特徵。</p>}
            </details>}
            {results.items.length === 0 && <p>已索引的資料中沒有符合這次條件的結果。</p>}
            <ol className="divide-y divide-slate-200" start={results.offset + 1}>
              {results.items.map((hit, index) => (
                <li key={hit.document_id} className="py-3">
                  <p className="text-sm font-medium text-teal-800">第 {results.offset + index + 1} 筆 · {stage[hit.document_stage] ?? hit.document_stage} {hit.publication_no} {hit.kind_code} · {scope[hit.content_scope]}</p>
                  <button className="mt-1 text-left" type="button" disabled={!!busy} onClick={() => void run("正在載入專利詳情…", () => openPatent(hit))}>{title(hit)}</button>
                  <p className="mt-1 text-sm text-slate-700">詞彙 {hit.lexical_rank ?? "—"} · 語意 {hit.semantic_rank ?? "—"} · 融合 {hit.fusion_rank}{hit.rerank_rank && ` · 重排 ${hit.rerank_rank}`}</p>
                </li>
              ))}
            </ol>
            <div className="mt-4 flex gap-2">
              <button disabled={!!busy || results.offset === 0} onClick={() => navigateResults(Math.max(0, results.offset - results.limit))}>上一頁</button>
              <button disabled={!!busy || !results.has_more} onClick={() => navigateResults(results.offset + results.limit)}>下一頁</button>
            </div>
          </>}
        </section>
      </div>
      {selected && (
        <section className="research-panel mt-6">
          <h2>專利詳情</h2>
          <h3 className="mt-2 text-xl">{title(selected.hit)}</h3>
          <p>{stage[selected.hit.document_stage]} {selected.hit.publication_no} {selected.hit.kind_code} · {scope[selected.hit.content_scope]}</p>
          <dl className="my-4 grid gap-2 text-sm sm:grid-cols-2">
            <div><dt>申請號</dt><dd>{selected.hit.application_no}</dd></div>
            <div><dt>申請日期</dt><dd>{selected.hit.filing_date || "未提供"}</dd></div>
            <div><dt>文件日期</dt><dd>{selected.hit.publication_date || "未提供"}</dd></div>
            <div><dt>申請人</dt><dd>{names(selected.detail.applicants)}</dd></div>
            <div><dt>發明人</dt><dd>{names(selected.detail.inventors)}</dd></div>
            <div><dt>分類</dt><dd>{selected.detail.classifications.map((item) => `${item.scheme} ${item.code}`).join("、") || "未提供"}</dd></div>
          </dl>
          <h3>摘要</h3>
          <p className="mb-4 whitespace-pre-wrap">{selected.detail.abstract_zh || selected.detail.abstract_en || "此版本未提供摘要。"}</p>
          <details className="my-3"><summary>請求項（{selected.claims.length}）</summary>
            {selected.claims.map((claim) => <p key={claim.claim_number} className="my-2 whitespace-pre-wrap">第 {claim.claim_number} 項 · {claim.text}</p>)}
          </details>
          <details className="my-3"><summary>說明書段落（{selected.detail.sections.length}）</summary>
            {selected.detail.sections.map((section) => <p key={`${section.section_type}-${section.ordinal}`} className="my-2 whitespace-pre-wrap">第 {section.ordinal} 段 · {section.original_text}</p>)}
          </details>
          <h3>來源批次</h3>
          <ul className="mb-4">
            {selected.detail.sources.map((source, index) => <li key={index} className="my-2">
              {source.publisher} · {source.dataset_name} · {source.batch_key} · 匯入 {source.ingested_at.slice(0, 10)}（UTC）
              {source.source_url ? <a className="ml-2" href={source.source_url} target="_blank" rel="noreferrer">官方原始檔</a>
                : source.dataset_url ? <a className="ml-2" href={source.dataset_url} target="_blank" rel="noreferrer">官方資料集</a> : null}
            </li>)}
          </ul>
          {session && projects.length > 0 && <div className="mb-4">
            <label className="research-field">收藏至研究專案
              <select disabled={!!busy} value={bookmarkProject} onChange={(event) => { setBookmarkProject(event.target.value); setBookmarkMessage(""); }}>
                <option value="">選擇研究專案</option>
                {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
              </select>
            </label>
            <button disabled={!!busy || !bookmarkProject} onClick={() => void run("正在收藏文件…", () => addBookmark(selected.hit.document_id, session.token))}>收藏此版本</button>
            {bookmarkMessage && <p role="status" className="mt-2 text-sm text-teal-900">{bookmarkMessage}</p>}
          </div>}
          {search && selected.fromResults && <>
          <button disabled={!!busy || !search.features.length || (!!saved && !!comparison)} onClick={() => void run("正在核對技術特徵…", () => comparePatent(selected.hit.document_id, search.features))}>
            {saved ? comparison ? "已保存技術比對" : "比對並保存證據" : "比對本次搜尋特徵"}
          </button>
          {!search.features.length && <p className="mt-2 text-sm">新增技術特徵並重新搜尋後，即可比對。</p>}
          {comparison && <div className="mt-5">
            <h3>技術特徵比對</h3>
            <p className="text-sm">檢查 {comparison.passages_checked} 個原文片段。判定限於此次檢查範圍。</p>
            {comparison.items.map((item) => <article className="my-3 rounded-lg border border-slate-300 p-3" key={item.feature_id}>
              <h4 className="font-semibold">{search.features.find((feature) => feature.feature_id === item.feature_id)?.description_zh} · {verdicts[item.verdict]}</h4>
              <p>{item.basis}</p>
              {item.evidence ? <>
                <blockquote className="my-2 border-l-2 border-teal-700 pl-3 whitespace-pre-wrap">{item.evidence.quote}</blockquote>
                <details><summary>原文定位</summary>
                  <p className="break-all">{item.evidence.xpath}</p>
                  <p>字元區間 [{item.evidence.char_start}, {item.evidence.char_end})</p>
                  <p className="break-all">原始檔 SHA-256 · {item.evidence.artifact_sha256}</p>
                </details>
              </> : <p>此項判定沒有可引用的原文證據。</p>}
            </article>)}
          </div>}
          </>}
        </section>
      )}
    </>
  );
}
