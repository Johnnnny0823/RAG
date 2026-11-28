import { useEffect, useRef, useState } from "react";
import { ComparisonMatrix, EvidenceLocator, verdicts } from "./comparison-matrix";
import { ResearchSessions } from "./research-sessions";
import { MAX_INVENTION_LENGTH } from "./invention";

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
type Party = { zh: string | null; en: string | null };
type Hit = PatentVersion & {
  lexical_rank: number | null;
  semantic_rank: number | null;
  fusion_rank: number;
  rerank_rank: number | null;
  abstract_excerpt?: string | null;
  applicants?: Party[];
  ipc_codes?: string[];
  loc_codes?: string[];
  official_source_url?: string | null;
  lexical_match_fields?: string[];
};
type SourceLocation = { xpath: string; artifact_sha256: string };
type Evidence = SourceLocation & { quote: string; char_start: number; char_end: number };
type SearchSort = "relevance" | "date_desc" | "date_asc";
const searchSortLabels: Record<SearchSort, string> = {
  relevance: "相關性",
  date_desc: "文件日期（新至舊）",
  date_asc: "文件日期（舊至新）",
};
type Detail = {
  abstract_zh: string | null;
  abstract_en: string | null;
  applicants: Party[];
  inventors: Party[];
  classifications: { scheme: string; code: string }[];
  priorities: { country: string; priority_no: string; priority_date: string; source_url: string | null; dataset_url: string | null; source: SourceLocation }[];
  sections: { ordinal: number; section_type: string; original_text: string; source: SourceLocation }[];
  sources: { dataset_name: string; publisher: string; dataset_url: string | null; source_url: string | null; batch_key: string; ingested_at: string; artifact_sha256: string; record_locator: string }[];
  legal_events: {
    kind: "extinguishment" | "gazette_correction";
    certificate_no: string;
    effective_on: string | null;
    detail: string | null;
    source_url: string | null;
    dataset_url: string | null;
    batch_key: string;
    ingested_at: string;
    artifact_sha256: string;
    record_locator: string;
  }[];
};
type Claim = { claim_number: number; text: string; referenced_claim_numbers: number[]; source: SourceLocation };
type SearchFilters = {
  loc: string;
  published_from: string;
  published_to: string;
  document_stage: string;
  content_scope: string;
  applicant: string;
};
type Search = { query: string; ipc: string | null; features: Feature[]; rerank: boolean; offset: number; sort_by?: SearchSort } &
  { [Key in keyof SearchFilters]?: string | null };
const emptyFilters: SearchFilters = { loc: "", published_from: "", published_to: "", document_stage: "", content_scope: "", applicant: "" };
type CorpusCoverage = {
  observed_at: string;
  lexical_versions: number;
  semantic_versions: number;
  latest_document_date: string | null;
};
type PatentPage<T> = { items: T[]; has_more: boolean; limit: number; offset: number };
type Results = PatentPage<Hit> & { corpus_coverage?: CorpusCoverage | null };
type NumberLookup = { number: string; numberType: string; page: PatentPage<PatentVersion> };
type RunSummary = { id: string; created_at: string; project_id: string | null };
type HistoryRun = RunSummary & { query_preview: string | null };
type Project = { id: string; name: string; description: string };
type SavedRun = RunSummary & {
  request: Search & { limit: number };
  settings: { corpus_coverage?: CorpusCoverage | null };
  items: Hit[];
  comparisons: Comparison[];
};
export type Comparison = {
  document_id: string;
  passages_checked: number;
  items: {
    feature_id: string;
    verdict: keyof typeof verdicts;
    basis: string;
    evidence: Evidence | null;
  }[];
};
type ComparedDocument = { document: PatentVersion; comparison: Comparison };

const stage: Record<string, string> = { publication: "公開", grant: "公告" };
const tipoLookupUrl = "https://tiponet.tipo.gov.tw/S092_OUT/2022/out";
const scope: Record<string, string> = {
  fulltext: "全文",
  metadata_and_abstract: "書目與摘要",
  claims_only: "請求項",
};
const splitTerms = (value: string) => value.split(/[,，、\n]/).map((word) => word.trim()).filter(Boolean);
const names = (parties: Party[]) => parties.map((party) => party.zh || party.en).filter(Boolean).join("、") || "未提供";
const title = (hit: PatentVersion) => hit.title_zh || hit.title_en || hit.publication_no;

function retrievalReason(hit: Hit): string {
  const fields = hit.lexical_match_fields ?? [];
  const areas = [
    fields.some((field) => field.startsWith("title_")) && "標題",
    fields.some((field) => field.startsWith("abstract_") || field.startsWith("section:abstract-")) && "摘要",
    fields.includes("claim") && "請求項",
    fields.some((field) => field.startsWith("section:") && !field.startsWith("section:abstract-")) && "說明書",
  ].filter(Boolean);
  return [
    hit.lexical_rank !== null && (areas.length ? `詞彙命中${areas.join("、")}` : "詞彙檢索候選"),
    hit.semantic_rank !== null && "列入語意檢索候選",
    hit.rerank_rank !== null && "模型依標題與摘要重排",
  ].filter(Boolean).join(" · ");
}

function evidenceBounds(text: string, source: SourceLocation, evidence: Evidence | null) {
  if (!source || !evidence || evidence.xpath !== source.xpath || evidence.artifact_sha256 !== source.artifact_sha256) return null;
  const chars = Array.from(text);
  const { char_start: start, char_end: end } = evidence;
  if (start < 0 || end <= start || end > chars.length || chars.slice(start, end).join("") !== evidence.quote) return null;
  return { prefix: chars.slice(0, start).join(""), quote: evidence.quote, suffix: chars.slice(end).join("") };
}

function highlighted(text: string, source: SourceLocation, evidence: Evidence | null) {
  const bounds = evidenceBounds(text, source, evidence);
  return bounds ? <>{bounds.prefix}<mark>{bounds.quote}</mark>{bounds.suffix}</> : text;
}

class SessionExpired extends Error {}

async function fetchWithDeadline(url: string, options: RequestInit): Promise<Response> {
  const signal = AbortSignal.timeout(180_000);
  try {
    return await fetch(url, { ...options, signal });
  } catch (error) {
    if (signal.aborted) throw signal.reason;
    throw error;
  }
}

async function request<T>(path: string, payload?: object, token?: string, method = payload ? "POST" : "GET"): Promise<T> {
  const headers = new Headers();
  if (payload) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", "Bearer " + token);
  const response = await fetchWithDeadline("/api/v1" + path, {
    cache: "no-store",
    headers,
    method,
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

type GazettePdfPage = { page_number: number; extracted_text: string };
type GazettePdfHit = PatentVersion & { artifact_sha256: string; page_number: number; source_url: string };
type GazettePdfResults = { items: GazettePdfHit[]; has_more: boolean; limit: number; offset: number };
type GazettePdfFilters = { query: string; document_stage: "publication" | "grant" | null };

function GazettePdfSearch({ busy, open }: { busy: boolean; open: (hit: GazettePdfHit) => void }) {
  const [query, setQuery] = useState("");
  const [documentStage, setDocumentStage] = useState<"publication" | "grant" | "">("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState<{ filters: GazettePdfFilters; page: GazettePdfResults } | null>(null);
  const [error, setError] = useState("");
  const results = submitted?.page;

  async function search(filters: GazettePdfFilters, offset: number) {
    setLoading(true);
    setError("");
    try {
      const page = await request<GazettePdfResults>("/patents/gazette-pdfs/search", { ...filters, offset });
      setSubmitted({ filters, page });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "公報檢索失敗。");
    } finally {
      setLoading(false);
    }
  }

  return <section className="research-panel mt-6" aria-labelledby="gazette-search-heading">
    <h2 id="gazette-search-heading">公報 PDF 檢索</h2>
    <p className="my-2 text-sm">搜尋已匯入的公報文字層。掃描圖像請查閱官方 PDF。</p>
    <form onSubmit={(event) => {
      event.preventDefault();
      if (!loading && query.trim()) void search({ query: query.trim(), document_stage: documentStage || null }, 0);
    }}>
      <label className="research-field">公報檢索詞
        <input value={query} onChange={(event) => setQuery(event.target.value)} maxLength={120} />
      </label>
      <label className="research-field">公報階段
        <select value={documentStage} onChange={(event) => setDocumentStage(event.target.value as typeof documentStage)}>
          <option value="">全部</option>
          <option value="publication">公開</option>
          <option value="grant">公告</option>
        </select>
      </label>
      <button type="submit" disabled={loading || !query.trim()}>{loading ? "正在搜尋公報…" : "搜尋公報 PDF"}</button>
    </form>
    {error && <p role="alert">{error}</p>}
    {results && (results.items.length ? <ul className="my-3 divide-y divide-slate-200">
      {results.items.map((hit) => <li key={`${hit.document_id}-${hit.artifact_sha256}-${hit.page_number}`} className="py-2">
        <p>{stage[hit.document_stage]} {hit.publication_no} · 第 {hit.page_number} 頁</p>
        <button type="button" disabled={busy} onClick={() => open(hit)}>{title(hit)}</button>
        <a className="ml-2 text-sm" href={`${hit.source_url}#page=${hit.page_number}`} target="_blank" rel="noreferrer">開啟官方 PDF 第 {hit.page_number} 頁</a>
      </li>)}
    </ul> : <p role="status">已匯入的公報文字中沒有符合的頁面。</p>)}
    {submitted && results && (results.has_more || results.offset > 0) && <nav className="mt-2 flex gap-3" aria-label="公報搜尋分頁">
      <button type="button" disabled={loading || !results.offset} onClick={() => void search(submitted.filters, Math.max(0, results.offset - results.limit))}>上一頁</button>
      <button type="button" disabled={loading || !results.has_more} onClick={() => void search(submitted.filters, results.offset + results.limit)}>下一頁</button>
    </nav>}
  </section>;
}

function GazettePdfReader({ documentId, checksum }: { documentId: string; checksum: string }) {
  const [pages, setPages] = useState<GazettePdfPage[] | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadPages() {
    setLoading(true);
    setError("");
    try {
      const result = await request<{ pages: GazettePdfPage[] }>(`/patents/${documentId}/gazette-pdfs/${checksum}/pages`);
      setPages(result.pages);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "公報文字載入失敗。");
    } finally {
      setLoading(false);
    }
  }

  if (!pages) {
    return <div className="mt-2">
      <button type="button" disabled={loading} onClick={() => void loadPages()}>{loading ? "載入公報文字…" : "讀取公報文字"}</button>
      {error && <p role="alert">{error}</p>}
    </div>;
  }
  if (!pages.length) return <p role="status">這份公報的頁面文字目前不可用。</p>;

  const normalize = (text: string) => text.normalize("NFKC").toLowerCase().replace(/\s+/g, "");
  const term = normalize(query);
  const matches = term ? pages.filter((page) => normalize(page.extracted_text).includes(term)) : pages;
  return <div className="my-2">
    <label className="research-field">在公報文字中查找
      <input value={query} maxLength={120} onChange={(event) => setQuery(event.target.value)} />
    </label>
    <p className="text-sm" role="status">顯示 {matches.length}／{pages.length} 頁。掃描圖像的內容請查閱官方 PDF。</p>
    {matches.map((page) => <details className="my-2" key={page.page_number}>
      <summary>PDF 第 {page.page_number} 頁</summary>
      <p className="whitespace-pre-wrap break-words text-sm">{page.extracted_text.trim() ? page.extracted_text : "這一頁沒有可讀取的文字層。"}</p>
    </details>)}
  </div>;
}

async function downloadPrivate(path: string, filename: string, token: string, failure: string) {
  const response = await fetchWithDeadline(`/api/v1${path}`, {
    headers: { Authorization: "Bearer " + token },
    cache: "no-store",
  });
  if (response.status === 401) throw new SessionExpired("登入已失效，請重新登入。");
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || failure);
  }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

type SearchJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  run_id: string | null;
  error_code: string | null;
};

type IngestionJob = {
  id: string;
  batch_key: string;
  status: "running" | "succeeded" | "partial" | "failed" | "interrupted";
  stage: "import" | "lexical" | "semantic";
  counts: {
    import?: { fulltext?: number; metadata?: number; grants_with_claims?: number; quarantined_specs?: number; download_failures?: number };
    lexical?: { versions: number };
    semantic?: { versions: number; vectors: number };
  };
  updated_at: string;
};
const ingestionStages = { import: "匯入", lexical: "詞彙索引", semantic: "向量索引" };
const ingestionStatuses = { running: "執行中", succeeded: "完成", partial: "部分完成", failed: "失敗", interrupted: "已中斷" };

const searchJobErrors: Record<string, string> = {
  MODEL_BUSY: "本機模型忙碌中，請稍後重試。",
  EMBEDDING_UNAVAILABLE: "目前無法使用本機嵌入模型。",
  ANALYSIS_UNAVAILABLE: "本機模型目前無法重排專利候選。",
  SEMANTIC_INDEX_UNAVAILABLE: "目前沒有可用的語意索引。",
  SEARCH_JOB_EXPIRED: "搜尋工作已逾時，請重新送出。",
};

export function Research() {
  const [query, setQuery] = useState("");
  const [ipc, setIpc] = useState("");
  const [filters, setFilters] = useState(emptyFilters);
  const [rerank, setRerank] = useState(false);
  const [sortBy, setSortBy] = useState<SearchSort>("relevance");
  const [highlight, setHighlight] = useState<{ documentId: string; evidence: Evidence } | null>(null);
  const [relatedVersions, setRelatedVersions] = useState<PatentVersion[] | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [busy, setBusy] = useState("");
  const [searchJob, setSearchJob] = useState<SearchJob | null>(null);
  const [searchJobMessage, setSearchJobMessage] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState<Search | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [numberLookup, setNumberLookup] = useState<NumberLookup | null>(null);
  const [selected, setSelected] = useState<{ hit: PatentVersion; detail: Detail; claims: Claim[]; fromResults: boolean } | null>(null);
  const [previewComparisons, setPreviewComparisons] = useState<ComparedDocument[]>([]);
  const [session, setSession] = useState<{ token: string; email: string; canMonitorIngestion: boolean } | null>(null);
  const workspaceHeading = useRef<HTMLHeadingElement>(null);
  const editorHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (session) workspaceHeading.current?.focus();
  }, [session]);
  const [ingestionJobs, setIngestionJobs] = useState<IngestionJob[] | null>(null);
  const [accountDeleted, setAccountDeleted] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [history, setHistory] = useState<HistoryRun[] | null>(null);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [saved, setSaved] = useState<SavedRun | null>(null);
  const [confirmSearchRemoval, setConfirmSearchRemoval] = useState(false);
  const [searchRemoved, setSearchRemoved] = useState(false);
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
  const compared = saved ? saved.items.flatMap((document) => {
    const comparison = saved.comparisons.find((item) => item.document_id === document.document_id);
    return comparison ? [{ document, comparison }] : [];
  }) : previewComparisons;
  const comparison = selected?.fromResults
    ? compared.find((item) => item.document.document_id === selected.hit.document_id)?.comparison
    : undefined;

  function leaveAccount() {
    setSession(null);
    setIngestionJobs(null);
    setSearchJobMessage("");
    setAccountDeleted(false);
    setHistory(null);
    setHistoryOffset(0);
    setSaved(null);
    setConfirmSearchRemoval(false);
    setSearchRemoved(false);
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
    setPreviewComparisons([]);
    setQuery("");
    setIpc("");
    setFilters(emptyFilters);
    setRerank(false);
    setSortBy("relevance");
    setDrafts([]);
    setError("");
  }

  async function signIn(credentials: { email: string; password: string }) {
    if (registering) {
      await request("/auth/register", credentials);
      setRegistering(false);
    }
    const { access_token } = await request<{ access_token: string }>("/auth/login", credentials);
    const account = await request<{ email: string; can_monitor_ingestion: boolean }>("/me", undefined, access_token);
    const accountProjects = await request<Project[]>("/projects?limit=100", undefined, access_token);
    leaveAccount();
    setSession({ token: access_token, email: account.email, canMonitorIngestion: account.can_monitor_ingestion });
    setProjects(accountProjects);
  }

  async function loadHistory(token: string, offset = 0) {
    const filter = projectFilter ? "&project_id=" + encodeURIComponent(projectFilter) : "";
    const rows = await request<HistoryRun[]>(`/search-runs?limit=21&offset=${offset}${filter}`, undefined, token);
    setHistory(rows);
    setHistoryOffset(offset);
  }

  function showSavedPage(record: SavedRun, offset = 0) {
    const limit = record.request.limit;
    setSearch(record.request);
    setResults({ items: record.items.slice(offset, offset + limit), offset, limit, has_more: offset + limit < record.items.length, corpus_coverage: record.settings?.corpus_coverage });
    setSelected(null);
  }

  async function openRun(id: string, token: string) {
    const record = await request<SavedRun>("/search-runs/" + id, undefined, token);
    setSaved(record);
    setConfirmSearchRemoval(false);
    setSearchRemoved(false);
    setAssignment(record.project_id ?? "");
    showSavedPage(record);
  }

  async function downloadReport(runId: string, token: string) {
    type ReportJob = { id: string; status: "queued" | "running" | "succeeded" | "failed" };
    const reports = `/search-runs/${runId}/reports`;
    let report = await request<ReportJob>(reports, {}, token);
    const path = `${reports}/${report.id}`;
    const deadline = Date.now() + 10 * 60_000;
    while (report.status === "queued" || report.status === "running") {
      setBusy(report.status === "queued" ? "PDF 等待產生…" : "正在產生私人 PDF…");
      if (Date.now() >= deadline) throw new Error("報告仍在等待或處理，請稍後重新開啟匯出。");
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
      report = await request<ReportJob>(path, undefined, token);
    }
    if (report.status !== "succeeded") throw new Error("目前無法產生 PDF，請稍後重試。");
    await downloadPrivate(`${path}/pdf`, `patentscope-${runId}.pdf`, token, "目前無法匯出 PDF。");
  }

  async function deleteSearch(runId: string, token: string) {
    await request<void>(`/search-runs/${runId}`, undefined, token, "DELETE");
    setSaved(null);
    setSearch(null);
    setResults(null);
    setSelected(null);
    setPreviewComparisons([]);
    setAssignment("");
    setHistory(null);
    setHistoryOffset(0);
    setConfirmSearchRemoval(false);
    setSearchRemoved(true);
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
    loadFeatureDrafts(data.features);
  }

  function loadFeatureDrafts(features: Feature[]) {
    setDrafts(features.map((feature) => ({
      ...feature, keywords_zh: feature.keywords_zh.join("，"), keywords_en: feature.keywords_en.join(", "),
    })));
  }

  function reuseSearch(strategy: Search) {
    setQuery(strategy.query);
    loadFeatureDrafts(strategy.features);
    setIpc(strategy.ipc ?? "");
    setFilters({
      loc: strategy.loc ?? "",
      published_from: strategy.published_from ?? "",
      published_to: strategy.published_to ?? "",
      document_stage: strategy.document_stage ?? "",
      content_scope: strategy.content_scope ?? "",
      applicant: strategy.applicant ?? "",
    });
    setRerank(strategy.rerank);
    setSortBy(strategy.sort_by ?? "relevance");
    editorHeading.current?.focus();
  }

  async function loadResults(next: Search, newSearch = false) {
    const data = await request<Results>("/patents/search/hybrid", next);
    setSearch(next);
    setSaved(null);
    setConfirmSearchRemoval(false);
    setSearchRemoved(false);
    setResults(data);
    setSelected(null);
    if (newSearch) setPreviewComparisons([]);
  }

  async function submitSearch(save: boolean) {
    const features = drafts.map((draft) => ({
      ...draft, keywords_zh: splitTerms(draft.keywords_zh), keywords_en: splitTerms(draft.keywords_en),
    }));
    if (features.some((feature) => !feature.description_zh.trim() ||
      [feature.keywords_zh, feature.keywords_en].some((terms) => terms.length > 4 || terms.some((term) => term.length > 48)))) {
      throw new Error("每項特徵須填寫描述。每種語言最多四個檢索詞，每詞最多 48 字。");
    }
    const payload = {
      query: query.trim(), ipc: ipc.trim() || null, features, rerank, offset: 0, sort_by: sortBy,
      loc: filters.loc.trim() || null,
      published_from: filters.published_from || null,
      published_to: filters.published_to || null,
      document_stage: filters.document_stage || null,
      content_scope: filters.content_scope || null,
      applicant: filters.applicant.trim() || null,
    };
    if (save && session) {
      setSearchJobMessage("");
      const active = await request<SearchJob | null>("/search-jobs/active", undefined, session.token);
      await followSearchJob(
        active ?? await request<SearchJob>("/search-jobs", payload, session.token),
        session.token,
        active !== null,
      );
      return;
    }
    await loadResults(payload, true);
  }

  async function resumeSearch(token: string) {
    setSearchJobMessage("");
    const active = await request<SearchJob | null>("/search-jobs/active", undefined, token);
    if (!active) {
      setSearchJobMessage("目前沒有背景搜尋。");
      return;
    }
    await followSearchJob(active, token, true);
  }

  async function followSearchJob(initial: SearchJob, token: string, resumed: boolean) {
    const deadline = Date.now() + 10 * 60_000;
    let job = initial;
    try {
      while (job.status === "queued" || job.status === "running") {
        setSearchJob(job);
        const label = resumed ? "先前的背景搜尋" : "背景搜尋";
        setBusy(job.status === "queued" ? `${label}等待中…` : `${label}處理中…`);
        if (Date.now() >= deadline) throw new Error("目前無法取得最終結果。可重新查看背景搜尋或從歷史載入成果。");
        await new Promise((resolve) => window.setTimeout(resolve, 1000));
        job = await request<SearchJob>(`/search-jobs/${job.id}`, undefined, token);
      }
      if (job.status === "cancelled") {
        setError("已取消背景搜尋。");
        return;
      }
      if (job.status === "failed" || !job.run_id) {
        throw new Error(searchJobErrors[job.error_code ?? ""] ?? "背景搜尋失敗，請重新送出。");
      }
      setHistory(null);
      await openRun(job.run_id, token);
    } finally {
      setSearchJob(null);
    }
  }

  async function cancelSearchJob() {
    if (!session || !searchJob) return;
    try {
      await request<SearchJob>(`/search-jobs/${searchJob.id}/cancel`, {}, session.token);
    } catch (error) {
      setError(error instanceof Error ? error.message : "目前無法取消搜尋。");
    }
  }

  async function openPatent(hit: PatentVersion, fromResults = true) {
    const path = "/patents/" + hit.document_id;
    const [detail, claims] = await Promise.all([request<Detail>(path), request<{ claims: Claim[] }>(path + "/claims")]);
    setSelected({ hit, detail, claims: claims.claims, fromResults });
    setRelatedVersions(null);
    setBookmarkProject(fromResults ? saved?.project_id ?? projectFilter : projectFilter);
    setBookmarkMessage("");
  }

  async function lookupPatentNumber(number: string, numberType: string, offset: number) {
    const params = new URLSearchParams({ number, number_type: numberType, limit: "20", offset: String(offset) });
    const page = await request<PatentPage<PatentVersion>>("/patents?" + params);
    setNumberLookup({ number, numberType, page });
    setSelected(null);
  }

  async function comparePatent(document: PatentVersion, features: Feature[]) {
    const documentId = document.document_id;
    if (saved && session) {
      const result = await request<Comparison>(`/search-runs/${saved.id}/comparisons/${documentId}`, {}, session.token);
      setSaved({ ...saved, comparisons: [...saved.comparisons.filter((item) => item.document_id !== documentId), result] });
      return;
    }
    const result = await request<Comparison>(`/patents/${documentId}/compare`, { features });
    setPreviewComparisons((current) => {
      if (current.some((item) => item.document.document_id === documentId)) {
        return current.map((item) => item.document.document_id === documentId ? { document, comparison: result } : item);
      }
      return [...current, { document, comparison: result }];
    });
  }

  function navigateResults(offset: number) {
    if (saved) showSavedPage(saved, offset);
    else if (search) void run("正在檢索專利…", () => loadResults({ ...search, offset }));
  }

  const abstractSections = selected?.detail.sections.filter((section) => section.section_type.startsWith("abstract-")) ?? [];
  const descriptionSections = selected?.detail.sections.filter((section) => !section.section_type.startsWith("abstract-")) ?? [];
  const drawings = selected?.detail.sources.filter((source) => source.record_locator.startsWith("/specification/drawings/figure[")) ?? [];

  return (
    <>
      <p className="mb-6 max-w-3xl text-slate-700">描述你的構想，從已索引的 TIPO 公開資料找出相關技術。涵蓋範圍以本機已匯入的批次為限。比對僅供研究參考。</p>
      <p className="mb-4 font-medium text-teal-900" role="status">{busy}</p>
      {searchJob && <button type="button" onClick={() => void cancelSearchJob()}>取消背景搜尋</button>}
      {error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-red-900" role="alert">{error}</p>}
      <section className="research-panel mb-6">
        <h2 ref={workspaceHeading} tabIndex={-1}>私人搜尋歷史</h2>
        {accountDeleted && <p role="status" className="my-2 text-sm text-teal-900">帳號與伺服器上的私人研究資料已刪除。</p>}
        {session ? <>
          <p className="my-2 break-all text-sm">目前帳號 · {session.email}</p>
          {session.canMonitorIngestion && (
            <details className="my-3">
              <summary>官方匯入與索引狀態</summary>
              <button className="my-2" disabled={!!busy} onClick={() => void run("正在查詢匯入工作…", async () => {
                setIngestionJobs(await request<IngestionJob[]>("/admin/ingestion/jobs", undefined, session.token));
              })}>更新最近 20 筆工作</button>
              {ingestionJobs?.length === 0 && <p>目前沒有已記錄的匯入工作。</p>}
              <ul className="space-y-2">
                {ingestionJobs?.map((job) => (
                  <li key={job.id} className="rounded border border-slate-300 p-2">
                    <p>期別 {job.batch_key} · {ingestionStages[job.stage]} · {ingestionStatuses[job.status]}</p>
                    <p className="text-sm">最後更新 <time dateTime={job.updated_at}>{new Date(job.updated_at).toLocaleString("zh-TW")}</time></p>
                    {job.counts.import && <p className="text-sm">
                      全文 {job.counts.import.fulltext ?? 0} · 書目 {job.counts.import.metadata ?? 0}
                      {job.counts.import.grants_with_claims !== undefined && ` · 公告請求項文件 ${job.counts.import.grants_with_claims}`}
                      {" · "}隔離 {job.counts.import.quarantined_specs ?? 0} · 下載失敗 {job.counts.import.download_failures ?? 0}
                    </p>}
                    {job.counts.lexical && <p className="text-sm">新增詞彙索引版本 {job.counts.lexical.versions}</p>}
                    {job.counts.semantic && <p className="text-sm">新增向量 {job.counts.semantic.vectors}</p>}
                  </li>
                ))}
              </ul>
            </details>
          )}
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
              loadFeatureDrafts(features);
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
            <button disabled={!!busy} onClick={() => void run("正在查看背景搜尋…", () => resumeSearch(session.token))}>查看背景搜尋</button>
            <button disabled={!!busy} onClick={() => void run("正在讀取歷史…", () => loadHistory(session.token))}>載入搜尋歷史</button>
            <button disabled={!!busy} onClick={() => void run("正在匯出私人研究資料…",
              () => downloadPrivate("/me/export", "patentscope-research.json", session.token, "目前無法匯出研究資料。"),
            )}>匯出我的研究資料（JSON）</button>
            <button disabled={!!busy} onClick={() => void run("正在登出…", async () => {
              await request<void>("/auth/logout", {}, session.token);
              leaveAccount();
            })}>登出此頁</button>
          </div>
          {searchJobMessage && <p className="my-2 text-sm" role="status">{searchJobMessage}</p>}
          <details className="my-3">
            <summary>刪除帳號與私人資料</summary>
            <p className="my-2 text-sm">此操作會永久刪除帳號、研究專案、搜尋、收藏與 AI Session，並撤銷所有登入。已下載的 PDF 和部署者備份須在各自位置管理。</p>
            <form onSubmit={(event) => {
              event.preventDefault();
              const form = event.currentTarget;
              const password = String(new FormData(form).get("password"));
              form.reset();
              void run("正在刪除帳號…", async () => {
                await request<void>("/me", { password }, session.token, "DELETE");
                leaveAccount();
                setAccountDeleted(true);
              });
            }}>
              <fieldset disabled={!!busy}>
                <label className="research-field">確認帳號密碼
                  <input name="password" type="password" autoComplete="current-password" minLength={12} maxLength={128} required />
                </label>
                <button type="submit">永久刪除我的帳號</button>
              </fieldset>
            </form>
          </details>
          {history?.length === 0 && <p className="mt-3">{projectFilter ? "此專案還沒有搜尋紀錄。" : "此帳號還沒有保存的搜尋。"}</p>}
          {!!history?.length && <>
            <ul className="my-3 space-y-2">
              {history.slice(0, 20).map((item) => <li key={item.id}>
                <button className="max-w-full break-words text-left" disabled={!!busy} onClick={() => void run("正在開啟搜尋紀錄…", () => openRun(item.id, session.token))}>
                  <strong className="block">{item.query_preview || "已保存的搜尋"}</strong>{" "}
                  <time className="text-sm" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString("zh-TW")}</time> · {item.id.slice(0, 8)}
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
          <h2 ref={editorHeading} tabIndex={-1}>發明構想</h2>
          <form onSubmit={(event) => { event.preventDefault(); if (!busy && query.trim()) void run("正在檢索專利…", () => submitSearch(false)); }}>
            <fieldset disabled={!!busy}>
              <label className="research-field">構想描述（最多 {MAX_INVENTION_LENGTH} 字）
                <textarea rows={5} value={query} maxLength={MAX_INVENTION_LENGTH} required onChange={(event) => setQuery(event.target.value)} />
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
              <label className="research-field">LOC 設計分類（選填）
                <input value={filters.loc} maxLength={12} onChange={(event) => setFilters({ ...filters, loc: event.target.value })} />
              </label>
              <div className="grid grid-cols-1 gap-x-3 sm:grid-cols-2">
                <label className="research-field">公開／公告起日
                  <input type="date" value={filters.published_from} onChange={(event) => setFilters({ ...filters, published_from: event.target.value })} />
                </label>
                <label className="research-field">公開／公告迄日
                  <input type="date" value={filters.published_to} onChange={(event) => setFilters({ ...filters, published_to: event.target.value })} />
                </label>
              </div>
              <label className="research-field">文件種類
                <select value={filters.document_stage} onChange={(event) => setFilters({ ...filters, document_stage: event.target.value })}>
                  <option value="">所有文件</option>
                  <option value="publication">公開</option>
                  <option value="grant">公告</option>
                </select>
              </label>
              <label className="research-field">文件內容
                <select value={filters.content_scope} onChange={(event) => setFilters({ ...filters, content_scope: event.target.value })}>
                  <option value="">不限</option>
                  <option value="fulltext">全文</option>
                  <option value="claims_only">書目與請求項</option>
                  <option value="metadata_and_abstract">書目與摘要</option>
                </select>
              </label>
              <label className="research-field">申請人（中英文名稱）
                <input value={filters.applicant} maxLength={120} onChange={(event) => setFilters({ ...filters, applicant: event.target.value })} />
              </label>
              <label className="my-3 block"><input type="checkbox" checked={rerank} onChange={(event) => setRerank(event.target.checked)} /> 使用本機模型重排序</label>
              <label className="research-field">候選排序
                <select value={sortBy} onChange={(event) => setSortBy(event.target.value as SearchSort)}>
                  {Object.entries(searchSortLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </label>
              <button className="research-primary" disabled={!query.trim()} type="submit">搜尋臺灣專利</button>
              {session && <button className="ml-2" type="button" disabled={!query.trim()} onClick={() => void run("正在檢索並保存…", () => submitSearch(true))}>搜尋並保存</button>}
            </fieldset>
          </form>
        </section>
        <section className="research-panel" aria-busy={busy === "正在檢索專利…"}>
          <h2>檢索結果</h2>
          {searchRemoved && <p role="status" className="my-2 text-sm text-teal-900">已刪除保存的搜尋紀錄與比對。</p>}
          {!results && <p className="mt-3 text-slate-700">完成搜尋後，這裡會顯示候選文件與排序資訊。</p>}
          {search && results && <>
            <p className="my-3 break-words text-slate-700">{saved ? "已保存的查詢" : "本次查詢"} · {search.query}{search.ipc && ` · IPC ${search.ipc}`}{search.loc && ` · LOC ${search.loc}`}</p>
            {results.corpus_coverage ? <p className="mb-3 text-sm text-slate-700">
              搜尋涵蓋範圍（依篩選） · 詞彙索引 {results.corpus_coverage.lexical_versions} 個文件版本 · 向量索引 {results.corpus_coverage.semantic_versions} 個文件版本 · 最新文件日期 {results.corpus_coverage.latest_document_date ?? "未提供"} · <time dateTime={results.corpus_coverage.observed_at}>{new Date(results.corpus_coverage.observed_at).toLocaleString("zh-TW")}</time>
            </p> : saved && <p className="mb-3 text-sm text-slate-700">這筆搜尋未記錄當時的索引涵蓋範圍。</p>}
            {(search.published_from || search.published_to || search.document_stage || search.applicant || search.content_scope) && <p className="mb-3 break-words text-sm text-slate-700">
              {[
                search.published_from && `起日 ${search.published_from}`,
                search.published_to && `迄日 ${search.published_to}`,
                search.document_stage && `文件 ${stage[search.document_stage]}`,
                search.content_scope && `內容 ${scope[search.content_scope]}`,
                search.applicant && `申請人 ${search.applicant}`,
              ].filter(Boolean).join(" · ")}
            </p>}
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
              <button className="ml-2" disabled={!!busy} onClick={() => void run("正在匯出私人 PDF…", () => downloadReport(saved.id, session.token))}>匯出 PDF 報告</button>
              {confirmSearchRemoval ? <div className="mt-3">
                <p className="mb-2 text-sm">這會永久刪除保存的查詢、候選與比對。收藏、AI Session 及已下載的 PDF 由各自位置管理。</p>
                <div className="flex flex-wrap gap-2">
                  <button disabled={!!busy} onClick={() => void run("正在刪除搜尋紀錄…", () => deleteSearch(saved.id, session.token))}>確認刪除搜尋紀錄</button>
                  <button disabled={!!busy} onClick={() => setConfirmSearchRemoval(false)}>取消刪除搜尋紀錄</button>
                </div>
              </div> : <button className="ml-2" disabled={!!busy} onClick={() => setConfirmSearchRemoval(true)}>刪除搜尋紀錄</button>}
            </div>}
            {saved && <details className="mb-3">
              <summary>已保存的檢索策略</summary>
              <p className="my-2 text-sm">本機重排序 · {search.rerank ? "啟用" : "停用"} · 候選排序 {searchSortLabels[search.sort_by ?? "relevance"]}</p>
              <button className="mb-2" type="button" disabled={!!busy} onClick={() => reuseSearch(saved.request)}>帶入搜尋表單</button>
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
                  <p className="mt-1 break-words text-sm text-slate-700">申請人 {names(hit.applicants ?? [])} · 文件日期 {hit.publication_date ?? "未提供"}{hit.ipc_codes?.length ? ` · IPC ${hit.ipc_codes.join("、")}` : ""}{hit.loc_codes?.length ? ` · LOC ${hit.loc_codes.join("、")}` : ""}</p>
                  {hit.abstract_excerpt && <p className="mt-1 line-clamp-3 break-words text-sm text-slate-700">{hit.abstract_excerpt}</p>}
                  <p className="mt-1 text-sm text-slate-700">相關原因 · {retrievalReason(hit)}</p>
                  <p className="mt-1 text-sm text-slate-700">詞彙 {hit.lexical_rank ?? "—"} · 語意 {hit.semantic_rank ?? "—"} · 融合 {hit.fusion_rank}{hit.rerank_rank && ` · 重排 ${hit.rerank_rank}`}</p>
                  {hit.official_source_url && <a className="mt-1 inline-block text-sm" href={hit.official_source_url} target="_blank" rel="noreferrer">官方資料集</a>}
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
      <GazettePdfSearch busy={!!busy} open={(hit) => void run("正在載入專利詳情…", () => openPatent(hit, false))} />
      <section className="research-panel mt-6" aria-labelledby="patent-number-heading">
        <h2 id="patent-number-heading">專利號碼查詢</h2>
        <form onSubmit={(event) => {
          event.preventDefault();
          if (busy) return;
          const data = new FormData(event.currentTarget);
          const number = String(data.get("number") ?? "").trim();
          if (!number) return;
          setNumberLookup(null);
          setSelected(null);
          void run("正在查詢專利號碼…", () => lookupPatentNumber(number, String(data.get("number_type")), 0));
        }}>
          <fieldset className="grid gap-x-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto] sm:items-end" disabled={!!busy}>
            <label className="research-field">號碼類型
              <select name="number_type" defaultValue="application">
                <option value="application">申請號</option>
                <option value="publication">公開號</option>
                <option value="grant">公告號</option>
              </select>
            </label>
            <label className="research-field">專利號碼
              <input name="number" required maxLength={32} />
            </label>
            <button className="mb-2" type="submit">查詢專利號碼</button>
          </fieldset>
        </form>
        {numberLookup && <>
          {numberLookup.page.items.length === 0 && <p role="status">已索引的資料中沒有符合這個號碼的文件。</p>}
          <ul className="divide-y divide-slate-200">
            {numberLookup.page.items.map((hit) => <li key={hit.document_id} className="py-3">
              <p className="text-sm font-medium text-teal-800">{stage[hit.document_stage]} {hit.publication_no} {hit.kind_code} · {scope[hit.content_scope]}</p>
              <button className="mt-1 text-left" type="button" disabled={!!busy} onClick={() => void run("正在載入專利詳情…", () => openPatent(hit, false))}>{title(hit)}</button>
            </li>)}
          </ul>
          {(numberLookup.page.offset > 0 || numberLookup.page.has_more) && <div className="mt-4 flex gap-2">
            <button disabled={!!busy || numberLookup.page.offset === 0} onClick={() => void run("正在查詢專利號碼…", () => lookupPatentNumber(numberLookup.number, numberLookup.numberType, numberLookup.page.offset - numberLookup.page.limit))}>上一頁</button>
            <button disabled={!!busy || !numberLookup.page.has_more} onClick={() => void run("正在查詢專利號碼…", () => lookupPatentNumber(numberLookup.number, numberLookup.numberType, numberLookup.page.offset + numberLookup.page.limit))}>下一頁</button>
          </div>}
        </>}
      </section>
      {search && !!compared.length && <ComparisonMatrix features={search.features} columns={compared.map(({ document, comparison }) => ({
        label: `${stage[document.document_stage]} ${document.publication_no} ${document.kind_code ?? ""} · ${scope[document.content_scope]}`,
        title: title(document),
        comparison,
      }))} />}
      {selected && (
        <section className="research-panel mt-6">
          <h2>專利詳情</h2>
          <div className={`grid gap-6 ${comparison ? "lg:grid-cols-2" : ""}`}>
          <div className="min-w-0">
          <h3 className="mt-2 text-xl">{title(selected.hit)}</h3>
          <p>{stage[selected.hit.document_stage]} {selected.hit.publication_no} {selected.hit.kind_code} · {scope[selected.hit.content_scope]}</p>
          <button type="button" disabled={!!busy} onClick={() => void run("正在查詢同案版本…", async () => {
            const query = new URLSearchParams({ number: selected.hit.application_no, number_type: "application", limit: "100" });
            const page = await request<PatentPage<PatentVersion>>("/patents?" + query);
            setRelatedVersions(page.items.filter((item) => item.document_id !== selected.hit.document_id));
          })}>查詢同案其他版本</button>
          {relatedVersions && (relatedVersions.length ? <ul>
            {relatedVersions.map((version) => <li key={version.document_id}>
              <button type="button" disabled={!!busy} onClick={() => void run("正在載入專利詳情…", () => openPatent(version, !!(saved?.items ?? results?.items)?.some((item) => item.document_id === version.document_id)))}>
                {stage[version.document_stage]} {version.publication_no} · {scope[version.content_scope]}
              </button>
            </li>)}
          </ul> : <p role="status">目前索引沒有同案的其他文件版本。</p>)}
          <dl className="my-4 grid gap-2 text-sm sm:grid-cols-2">
            <div><dt>申請號</dt><dd>{selected.hit.application_no}</dd></div>
            <div><dt>申請日期</dt><dd>{selected.hit.filing_date || "未提供"}</dd></div>
            <div><dt>文件日期</dt><dd>{selected.hit.publication_date || "未提供"}</dd></div>
            <div><dt>申請人</dt><dd>{names(selected.detail.applicants)}</dd></div>
            <div><dt>發明人</dt><dd>{names(selected.detail.inventors)}</dd></div>
            <div><dt>分類</dt><dd>{selected.detail.classifications.map((item) => `${item.scheme} ${item.code}`).join("、") || "未提供"}</dd></div>
          </dl>
          {selected.detail.priorities.length > 0 && (
            <details className="my-3">
              <summary>優先權（{selected.detail.priorities.length}）</summary>
              <ul className="my-2 space-y-2 text-sm">
                {selected.detail.priorities.map((item) => (
                  <li key={item.source.xpath} className="break-words">
                    <p>{item.country} · {item.priority_no} · <time dateTime={item.priority_date}>{item.priority_date}</time></p>
                    {(item.dataset_url || item.source_url) && <a className="underline" href={item.dataset_url || item.source_url || undefined} target="_blank" rel="noreferrer">優先權官方來源</a>}
                    <p>{item.source.xpath} · SHA-256 {item.source.artifact_sha256}</p>
                  </li>
                ))}
              </ul>
            </details>
          )}
          <h3>摘要</h3>
          {abstractSections.length ? abstractSections.map((section) => (
            <div className="mb-4" key={section.section_type}>
              <h4>{section.section_type === "abstract-zh" ? "中文摘要" : "英文摘要"}</h4>
              <p id={`section-${section.section_type}-${section.ordinal}`} tabIndex={-1} className="scroll-mt-4 whitespace-pre-wrap">
                {highlighted(section.original_text, section.source, highlight?.documentId === selected.hit.document_id ? highlight.evidence : null)}
              </p>
            </div>
          )) : <p className="mb-4 whitespace-pre-wrap">{selected.detail.abstract_zh || selected.detail.abstract_en || "此版本未提供摘要。"}</p>}
          <details className="my-3"><summary>請求項（{selected.claims.length}）</summary>
            {selected.claims.map((claim) => (
              <div key={claim.claim_number} id={`claim-${claim.claim_number}`} tabIndex={-1} className="my-2 scroll-mt-4">
                <p className="whitespace-pre-wrap">第 {claim.claim_number} 項 · {highlighted(claim.text, claim.source, highlight?.documentId === selected.hit.document_id ? highlight.evidence : null)}</p>
                {claim.referenced_claim_numbers.length > 0 && (
                  <p className="text-sm">原文援引：
                    {claim.referenced_claim_numbers.map((number) => (
                      <a key={number} href={`#claim-${number}`} className="ml-2 underline">第 {number} 項</a>
                    ))}
                  </p>
                )}
              </div>
            ))}
          </details>
          <details className="my-3"><summary>說明書段落（{descriptionSections.length}）</summary>
            {descriptionSections.map((section) => <p id={`section-${section.section_type}-${section.ordinal}`} tabIndex={-1} key={`${section.section_type}-${section.ordinal}`} className="my-2 whitespace-pre-wrap">第 {section.ordinal} 段 · {highlighted(section.original_text, section.source, highlight?.documentId === selected.hit.document_id ? highlight.evidence : null)}</p>)}
          </details>
          {drawings.length > 0 && <details className="my-3">
            <summary>官方圖式（{drawings.length}）</summary>
            {drawings.map((drawing) => {
              const position = drawing.record_locator.match(/figure\[(\d+)\]/)?.[1];
              return <figure key={drawing.artifact_sha256 + drawing.record_locator} className="my-4">
                <img className="max-w-full" loading="lazy" src={`/api/v1/patents/${selected.hit.document_id}/drawings/${drawing.artifact_sha256}`} alt={`官方圖式 ${position ?? ""}`} />
                <figcaption className="break-all text-sm">{drawing.record_locator} · SHA-256 {drawing.artifact_sha256}</figcaption>
              </figure>;
            })}
          </details>}
          <h3>權利異動公報</h3>
          <p className="mb-2 text-sm text-slate-700">涵蓋已匯入的公報卷期。查詢目前權利狀態時，請以智慧財產局最新資料為準。</p>
          {selected.detail.legal_events.length ? <ul className="mb-4">
            {selected.detail.legal_events.map((event) => <li key={event.artifact_sha256 + event.record_locator} className="my-2">
              <span>{event.kind === "extinguishment" ? "專利權消滅公告" : "公報更正"} · 證書號 {event.certificate_no} · 卷期 {event.batch_key}</span>
              {event.effective_on && <span> · 公報記載消滅日 {event.effective_on}</span>}
              {event.detail && <span> · {event.detail}</span>}
              {event.dataset_url && <a className="ml-2" href={event.dataset_url} target="_blank" rel="noreferrer">異動公報資料集</a>}
              {event.source_url && <a className="ml-2" href={event.source_url} target="_blank" rel="noreferrer">異動公報原始檔</a>}
              <details className="text-sm"><summary>異動公報來源定位</summary>
                <p className="break-all">{event.record_locator}</p>
                <p className="break-all">原始檔 SHA-256 · {event.artifact_sha256}</p>
                <p>匯入 {event.ingested_at.slice(0, 10)}（UTC）</p>
              </details>
            </li>)}
          </ul> : <p className="mb-4 text-sm text-slate-700">目前索引沒有這筆申請案的異動公報紀錄。</p>}
          <h3>來源批次</h3>
          <p className="my-2 text-sm">
            <a href={tipoLookupUrl} target="_blank" rel="noreferrer">在智慧財產局查詢{stage[selected.hit.document_stage]}號 {selected.hit.publication_no}</a>
            <span> · 到官方頁面輸入此號碼。</span>
          </p>
          <ul className="mb-4" key={selected.hit.document_id}>
            {selected.detail.sources.map((source, index) => <li key={index} className="my-2">
              {source.publisher} · {source.dataset_name} · {source.batch_key} · 匯入 {source.ingested_at.slice(0, 10)}（UTC）
              {source.source_url && <a className="ml-2" href={source.source_url} target="_blank" rel="noreferrer">{source.source_url.endsWith(".pdf") ? "官方公報 PDF" : "官方原始檔"}</a>}
              {source.dataset_url && source.dataset_url !== source.source_url && <a className="ml-2" href={source.dataset_url} target="_blank" rel="noreferrer">官方資料集</a>}
              <details className="mt-1 text-sm">
                <summary>原檔雜湊與定位</summary>
                <dl className="my-2 grid gap-2">
                  <div><dt>SHA-256</dt><dd className="break-all">{source.artifact_sha256}</dd></div>
                  <div><dt>原文位置</dt><dd className="break-all">{source.record_locator}</dd></div>
                </dl>
                {source.source_url?.startsWith("ftps://") && <label className="research-field">
                  FTPS 位址（可複製到 FTPS 用戶端）
                  <input type="text" readOnly value={source.source_url} onFocus={(event) => event.currentTarget.select()} />
                </label>}
                {source.source_url?.endsWith(".pdf") && (
                  <GazettePdfReader documentId={selected.hit.document_id} checksum={source.artifact_sha256} />
                )}
              </details>
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
          </div>
          {search && selected.fromResults && <>
          <div className="min-w-0">
          <button disabled={!!busy || !search.features.length || (!!saved && !!comparison)} onClick={() => void run("正在核對技術特徵…", () => comparePatent(selected.hit, search.features))}>
            {saved ? comparison ? "已保存技術比對" : "比對並保存證據" : "比對本次搜尋特徵"}
          </button>
          {!search.features.length && <p className="mt-2 text-sm">新增技術特徵並重新搜尋後，即可比對。</p>}
          {comparison && <div className="mt-5">
            <h3>技術特徵比對</h3>
            <p className="text-sm">檢查 {comparison.passages_checked} 個原文片段。判定限於此次檢查範圍。</p>
            {comparison.items.map((item) => {
              const evidence = item.evidence;
              const claim = selected.claims.find((entry) => evidenceBounds(entry.text, entry.source, evidence));
              const section = selected.detail.sections.find((entry) => evidenceBounds(entry.original_text, entry.source, evidence));
              const target = claim ? `claim-${claim.claim_number}` : section ? `section-${section.section_type}-${section.ordinal}` : null;
              return <article className="my-3 rounded-lg border border-slate-300 p-3" key={item.feature_id}>
              <h4 className="font-semibold">{search.features.find((feature) => feature.feature_id === item.feature_id)?.description_zh} · {verdicts[item.verdict]}</h4>
              <p>{item.basis}</p>
              {item.evidence ? <>
                <blockquote className="my-2 border-l-2 border-teal-700 pl-3 whitespace-pre-wrap">{item.evidence.quote}</blockquote>
                {target && evidence && <button onClick={() => {
                  setHighlight({ documentId: selected.hit.document_id, evidence });
                  const passage = document.getElementById(target);
                  const reader = passage?.closest("details");
                  if (reader) reader.open = true;
                  passage?.focus();
                  passage?.scrollIntoView({ block: "nearest" });
                }}>定位並標記原文</button>}
                <details><summary>原文定位</summary>
                  <EvidenceLocator evidence={item.evidence} />
                </details>
              </> : <p>此項判定沒有可引用的原文證據。</p>}
            </article>})}
          </div>}
          </div>
          </>}
          </div>
        </section>
      )}
    </>
  );
}
