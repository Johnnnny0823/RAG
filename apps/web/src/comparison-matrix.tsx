import type { Comparison, Feature } from "./research";

export const verdicts = {
  supported: "有明確證據",
  partially_supported: "部分符合",
  uncertain: "不確定",
  not_found_in_checked_content: "未找到證據",
};

export function EvidenceLocator({ evidence }: {
  evidence: NonNullable<Comparison["items"][number]["evidence"]>;
}) {
  return <>
    <p className="break-all">{evidence.xpath}</p>
    <p>字元區間 [{evidence.char_start}, {evidence.char_end})</p>
    <p className="break-all">原始檔 SHA-256 · {evidence.artifact_sha256}</p>
  </>;
}

type Column = { label: string; title: string; comparison: Comparison };

export function ComparisonMatrix({ features, columns }: { features: Feature[]; columns: Column[] }) {
  return <section className="research-panel mt-6" aria-labelledby="comparison-matrix-heading">
    <h2 id="comparison-matrix-heading">跨文件比對矩陣</h2>
    <p className="my-3 text-sm text-slate-700">開啟其他候選的專利詳情並執行比對，即可新增欄位。各判定限於該文件版本已檢查的片段。</p>
    <div className="overflow-x-auto rounded-md border border-slate-300 focus-visible:outline-2" tabIndex={0} role="region" aria-label="技術特徵比對表格，可橫向捲動">
      <table className="w-full border-collapse text-left text-sm" aria-labelledby="comparison-matrix-heading">
        <thead className="bg-slate-100">
          <tr>
            <th className="min-w-40 p-3" scope="col">技術特徵</th>
            {columns.map(({ label, title, comparison }) => (
              <th key={comparison.document_id} scope="col" className="min-w-60 border-l border-slate-300 p-3 align-top">
                <p>{label}</p>
                <p className="mt-1 font-normal">{title}</p>
                <p className="mt-1 font-normal">檢查 {comparison.passages_checked} 個原文片段</p>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {features.map((feature) => (
            <tr key={feature.feature_id} className="border-t border-slate-300">
              <th scope="row" className="p-3 align-top font-semibold break-words">{feature.description_zh}</th>
              {columns.map(({ comparison }) => {
                const item = comparison.items.find((entry) => entry.feature_id === feature.feature_id);
                return <td key={comparison.document_id} className="border-l border-slate-300 p-3 align-top">
                  {item ? <>
                    <p className="font-semibold">{verdicts[item.verdict]}</p>
                    <p className="my-1">{item.basis}</p>
                    {item.evidence ? <details>
                      <summary>原文證據與定位</summary>
                      <p className="my-2 whitespace-pre-wrap">{item.evidence.quote}</p>
                      <EvidenceLocator evidence={item.evidence} />
                    </details> : <p>無可引用原文。</p>}
                  </> : "尚未比對"}
                </td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>;
}
