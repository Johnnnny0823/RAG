import { useState } from "react";

type Feature = {
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
type Hit = {
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
const verdicts = {
  supported: "有明確證據",
  partially_supported: "部分符合",
  uncertain: "不確定",
  not_found_in_checked_content: "未找到證據",
};
type Comparison = {
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
const title = (hit: Hit) => hit.title_zh || hit.title_en || hit.publication_no;

async function request<T>(path: string, payload?: object): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    cache: "no-store",
    signal: AbortSignal.timeout(180_000),
    ...(payload && {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || `服務回應錯誤（HTTP ${response.status}）`);
  }
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
  const [selected, setSelected] = useState<{ hit: Hit; detail: Detail; claims: Claim[] } | null>(null);
  const [comparison, setComparison] = useState<Comparison | null>(null);

  async function run(label: string, operation: () => Promise<void>) {
    setBusy(label);
    setError("");
    try {
      await operation();
    } catch (failure) {
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
    setResults(data);
    setSelected(null);
    setComparison(null);
  }

  async function submitSearch() {
    const features = drafts.map((draft) => ({
      ...draft, keywords_zh: splitTerms(draft.keywords_zh), keywords_en: splitTerms(draft.keywords_en),
    }));
    if (features.some((feature) => !feature.description_zh.trim() ||
      [feature.keywords_zh, feature.keywords_en].some((terms) => terms.length > 4 || terms.some((term) => term.length > 48)))) {
      throw new Error("每項特徵須填寫描述。每種語言最多四個檢索詞，每詞最多 48 字。");
    }
    await loadResults({ query: query.trim(), ipc: ipc.trim() || null, features, rerank, offset: 0 });
  }

  async function openPatent(hit: Hit) {
    const path = "/patents/" + hit.document_id;
    const [detail, claims] = await Promise.all([request<Detail>(path), request<{ claims: Claim[] }>(path + "/claims")]);
    setSelected({ hit, detail, claims: claims.claims });
    setComparison(null);
  }

  return (
    <>
      <p className="mb-6 max-w-3xl text-slate-700">描述你的構想，從已索引的 TIPO 公開資料找出相關技術。涵蓋範圍以本機已匯入的批次為限。比對僅供研究參考。</p>
      <p className="mb-4 font-medium text-teal-900" role="status">{busy}</p>
      {error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-red-900" role="alert">{error}</p>}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <section className="research-panel">
          <h2>發明構想</h2>
          <form onSubmit={(event) => { event.preventDefault(); if (!busy && query.trim()) void run("正在檢索專利…", submitSearch); }}>
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
            </fieldset>
          </form>
        </section>
        <section className="research-panel" aria-busy={busy === "正在檢索專利…"}>
          <h2>檢索結果</h2>
          {!results && <p className="mt-3 text-slate-700">完成搜尋後，這裡會顯示候選文件與排序資訊。</p>}
          {search && results && <>
            <p className="my-3 break-words text-slate-700">本次查詢 · {search.query}{search.ipc && ` · IPC ${search.ipc}`}</p>
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
              <button disabled={!!busy || results.offset === 0} onClick={() => void run("正在檢索專利…", () => loadResults({ ...search, offset: Math.max(0, results.offset - results.limit) }))}>上一頁</button>
              <button disabled={!!busy || !results.has_more} onClick={() => void run("正在檢索專利…", () => loadResults({ ...search, offset: results.offset + results.limit }))}>下一頁</button>
            </div>
          </>}
        </section>
      </div>
      {selected && search && (
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
          <button disabled={!!busy || !search.features.length} onClick={() => void run("正在核對技術特徵…", async () => {
            setComparison(await request<Comparison>(`/patents/${selected.hit.document_id}/compare`, { features: search.features }));
          })}>比對本次搜尋特徵</button>
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
        </section>
      )}
    </>
  );
}
