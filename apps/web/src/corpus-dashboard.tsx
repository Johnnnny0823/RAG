export type IngestionBatchSummary = {
  dataset_key: string;
  batch_key: string;
  parser_version: string;
  status: string;
  counts: Record<string, unknown>;
  finished_at: string | null;
};

export type CorpusStatus = {
  datasets_count: number;
  documents_total: number;
  publications_count: number;
  grants_count: number;
  lexical_indexed_documents: number;
  semantic_indexed_documents: number;
  latest_ingested_at: string | null;
  recent_batches: IngestionBatchSummary[];
};

const batchStatusLabel: Record<string, string> = {
  complete: "完成",
  partial: "部分完成",
  processing: "處理中",
  failed: "失敗",
};

const batchStatusTone: Record<string, string> = {
  complete: "bg-emerald-100 text-emerald-900",
  partial: "bg-amber-100 text-amber-900",
  processing: "bg-sky-100 text-sky-900",
  failed: "bg-rose-100 text-rose-900",
};

export function CorpusDashboard({ corpus }: { corpus: CorpusStatus }) {
  const lexicalPct = corpus.documents_total
    ? Math.round((corpus.lexical_indexed_documents / corpus.documents_total) * 100)
    : 0;
  const semanticPct = corpus.documents_total
    ? Math.round((corpus.semantic_indexed_documents / corpus.documents_total) * 100)
    : 0;

  return (
    <section id="admin-corpus" className="mt-8 rounded-xl border border-slate-300 bg-white p-5 sm:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">語料涵蓋與匯入監控</h2>
          <p className="mt-1 text-sm text-slate-600">
            呈現目前資料庫中已查核之 TIPO 官方語料覆蓋範圍與最近匯入批次（僅含公開官方資料，不含私人研究紀錄）。
          </p>
        </div>
        <p className="text-xs text-slate-600">
          最新匯入：{corpus.latest_ingested_at ? `${corpus.latest_ingested_at.slice(0, 16).replace("T", " ")} UTC` : "尚未匯入"}
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-600">官方資料集</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{corpus.datasets_count}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-600">已匯入文件版本</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{corpus.documents_total}</p>
          <p className="mt-0.5 text-xs text-slate-600">
            公開 {corpus.publications_count} · 公告 {corpus.grants_count}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-600">詞彙索引覆蓋</p>
          <p className="mt-1 text-2xl font-semibold text-teal-800">{lexicalPct}%</p>
          <p className="mt-0.5 text-xs text-slate-600">
            {corpus.lexical_indexed_documents} / {corpus.documents_total} 份版本
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-600">向量索引覆蓋（所有已索引模型）</p>
          <p className="mt-1 text-2xl font-semibold text-teal-800">{semanticPct}%</p>
          <p className="mt-0.5 text-xs text-slate-600">
            {corpus.semantic_indexed_documents} / {corpus.documents_total} 份版本
          </p>
        </div>
      </div>

      {corpus.recent_batches.length > 0 ? (
        <div className="mt-5 overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-100 text-xs text-slate-700">
              <tr>
                <th className="px-3 py-2">資料集</th>
                <th className="px-3 py-2">批次鍵</th>
                <th className="px-3 py-2">解析器版本</th>
                <th className="px-3 py-2">狀態</th>
                <th className="px-3 py-2">完成時間（UTC）</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {corpus.recent_batches.map((batch, index) => (
                <tr key={`${batch.dataset_key}-${batch.batch_key}-${batch.parser_version}-${index}`}>
                  <td className="px-3 py-2 font-medium">{batch.dataset_key}</td>
                  <td className="px-3 py-2">{batch.batch_key}</td>
                  <td className="px-3 py-2 font-mono text-xs">{batch.parser_version}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${batchStatusTone[batch.status] ?? "bg-slate-200 text-slate-800"}`}>
                      {batchStatusLabel[batch.status] ?? batch.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    {batch.finished_at ? batch.finished_at.slice(0, 16).replace("T", " ") : "進行中"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-600">尚未有已完成的官方專利匯入批次。</p>
      )}
    </section>
  );
}
