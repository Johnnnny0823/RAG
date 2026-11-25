import { execFile } from "node:child_process";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { expect, test } from "@playwright/test";

type Citation = {
  kind: string;
  ordinal: number;
  char_start: number;
  char_end: number;
  quote: string;
  xpath: string;
  artifact_sha256: string;
};

test("official publication supports saved evidence and PDF export @tipo", async ({ page }, testInfo) => {
  test.setTimeout(180_000);
  const email = `tipo-e2e-${randomUUID()}@example.invalid`;
  const password = randomUUID();
  const button = (name: string) => page.getByRole("button", { name, exact: true });
  const publication = page.getByRole("listitem").filter({ hasText: "公開 202639611 · 全文" });

  await page.goto("/");
  await expect(page.getByText("API、資料庫與向量擴充功能已就緒。")).toBeVisible();
  await button("建立帳號").click();
  await page.getByLabel("電子郵件").fill(email);
  await page.getByLabel("密碼（至少 12 字元）").fill(password);
  await button("註冊並登入").click();
  await expect(page.getByText(`目前帳號 · ${email}`)).toBeVisible();

  try {
    const longIdea = [
      "光硬化性樹脂組成物。",
      "我想研發一種用於半導體元件組裝的光硬化接著劑。製程先在基材上塗布薄層樹脂，再以波長高於五百奈米的可見光照射，使接著劑在零件之間完成硬化。",
      "我希望配方能在較低溫度下施工，以避免細小零件因受熱而變形，並利用顆粒分散的方式控制塗層厚度。研究時需要區分光源波長、感光成分與粒子尺寸等條件。",
      "若先前技術也使用長波光源，還需要檢查其是否揭露相同的樹脂成分與使用方法，以及原文是否限制了封裝用途。",
    ].join("\n");
    const ideaField = page.getByLabel(/^構想描述（最多 /);
    await ideaField.fill(longIdea);
    await expect(ideaField).toHaveValue(longIdea);
    const analysisResponse = page.waitForResponse((response) =>
      response.url().endsWith("/api/v1/queries/analyze"), { timeout: 120_000 },
    );
    await button("AI 拆解技術特徵").click();
    const analysis = await analysisResponse;
    expect(analysis.ok()).toBe(true);
    expect(analysis.request().postDataJSON().query).toBe(longIdea);
    const { features } = await analysis.json();
    expect(features.length).toBeGreaterThan(0);
    for (let index = features.length; index > 0; index--) {
      await button(`刪除特徵 ${index}`).click();
    }
    await button("新增特徵").click();
    await page.getByLabel("特徵描述", { exact: true }).fill("光硬化性樹脂組成物");
    await page.getByLabel("繁中檢索詞（逗號分隔）").fill("光硬化性樹脂組成物");
    const ipc = page.getByLabel("IPC 篩選（選填）");
    await ipc.fill("A01B");
    const emptyResponse = page.waitForResponse((response) =>
      response.url().endsWith("/api/v1/patents/search/hybrid"), { timeout: 90_000 },
    );
    await button("搜尋臺灣專利").click();
    const empty = await emptyResponse;
    expect(empty.ok()).toBe(true);
    expect((await empty.json()).items).toEqual([]);
    await expect(page.getByText("已索引的資料中沒有符合這次條件的結果。")).toBeVisible();
    await expect(page.getByRole("alert")).toHaveCount(0);
    await ipc.fill("C08F");
    await page.getByLabel("文件種類").selectOption("publication");
    await page.getByLabel("申請人（中英文名稱）").fill("九州大學");

    const savedResponse = page.waitForResponse((response) =>
      response.url().endsWith("/api/v1/search-runs") && response.request().method() === "POST",
      { timeout: 90_000 },
    );
    await button("搜尋並保存").click();
    const saved = await savedResponse;
    expect(saved.status()).toBe(201);
    const { id } = await saved.json();
    await expect(publication).toBeVisible();
    await expect(page.getByRole("listitem").filter({ hasText: "公告 " })).toHaveCount(0);

    const claimsResponse = page.waitForResponse((response) => /\/api\/v1\/patents\/[^/]+\/claims$/.test(response.url()));
    await publication.getByRole("button").click();
    const claims = await claimsResponse;
    expect(claims.ok()).toBe(true);
    const { document_id: detailId, claims: originalClaims } = await claims.json();
    await expect(page.getByRole("heading", { name: "專利詳情" })).toBeVisible();
    await expect(page.getByRole("link", { name: "官方資料集" }).first()).toHaveAttribute("href", "https://data.gov.tw/dataset/15996");
    await page.getByText(/^請求項（\d+）$/).click();
    const secondClaim = page.locator("#claim-2");
    const reference = secondClaim.getByRole("link", { name: "第 1 項", exact: true });
    await expect(reference).toHaveAttribute("href", "#claim-1");
    await reference.click();
    await expect(page).toHaveURL(/#claim-1$/);
    await expect(page.getByText(/^第 1 項 ·/).first()).toBeVisible();

    const comparePath = `/api/v1/patents/${detailId}/compare`;
    const paraphrase = [{
      feature_id: "f1",
      description_zh: "Polymer composition curable by light above 500 nanometers",
      keywords_zh: [],
      keywords_en: [],
      must_have: true,
      confidence: "high",
      ipc_candidates: [],
    }];
    const literal = await page.request.post(comparePath, { data: { features: paraphrase, semantic_evidence: false } });
    expect(literal.ok()).toBe(true);
    expect((await literal.json()).items[0]).toMatchObject({
      verdict: "not_found_in_checked_content",
      evidence: null,
    });
    const semantic = await page.request.post(comparePath, { data: { features: paraphrase }, timeout: 90_000 });
    expect(semantic.ok()).toBe(true);
    const semanticResult = await semantic.json();
    expect(semanticResult.document_id).toBe(detailId);
    expect(semanticResult.items[0].evidence_method).toBe("semantic");
    const semanticQuote: Citation = semanticResult.items[0].evidence;
    const detail = await page.request.get(`/api/v1/patents/${detailId}`);
    expect(detail.ok()).toBe(true);
    const semanticSource = semanticQuote.kind === "claim"
      ? originalClaims.find((item: { claim_number: number }) => item.claim_number === semanticQuote.ordinal)
      : (await detail.json()).sections.find((item: { section_type: string; ordinal: number }) =>
        item.section_type === semanticQuote.kind && item.ordinal === semanticQuote.ordinal);
    expect(semanticSource?.source).toEqual({ xpath: semanticQuote.xpath, artifact_sha256: semanticQuote.artifact_sha256 });
    const semanticText: string = semanticSource.text ?? semanticSource.original_text;
    expect(Array.from(semanticText).slice(semanticQuote.char_start, semanticQuote.char_end).join("")).toBe(semanticQuote.quote);

    const comparisonResponse = page.waitForResponse((response) =>
      response.url().includes(`/api/v1/search-runs/${id}/comparisons/`) && response.request().method() === "POST",
      { timeout: 90_000 },
    );
    await button("比對並保存證據").click();
    const comparison = await comparisonResponse;
    expect(comparison.ok()).toBe(true);
    const { items, document_id: documentId } = await comparison.json();
    expect(new URL(claims.url()).pathname).toBe(`/api/v1/patents/${documentId}/claims`);
    const citation: Citation = items[0].evidence;
    expect(citation).toBeTruthy();
    expect(citation.kind).toBe("claim");
    expect(citation.artifact_sha256).toBe("0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a");
    const claim = originalClaims.find((item: { claim_number: number }) => item.claim_number === citation.ordinal);
    expect(claim).toBeTruthy();
    expect(claim.source).toEqual({ xpath: citation.xpath, artifact_sha256: citation.artifact_sha256 });
    expect(Array.from(claim.text as string).slice(citation.char_start, citation.char_end).join("")).toBe(citation.quote);
    const evidence = page.getByRole("article").filter({ has: page.locator("blockquote") });
    await expect(evidence.locator("blockquote").filter({ hasText: citation.quote })).toBeVisible();
    await evidence.getByText("原文定位", { exact: true }).click();
    await expect(evidence.getByText(citation.xpath, { exact: true })).toBeVisible();
    await expect(evidence.getByText(`原始檔 SHA-256 · ${citation.artifact_sha256}`)).toBeVisible();

    await button("登出此頁").click();
    await expect(publication).toHaveCount(0);
    await page.reload();
    await page.getByLabel("電子郵件").fill(email);
    await page.getByLabel("密碼（至少 12 字元）").fill(password);
    await button("登入").click();
    await expect(page.getByText(`目前帳號 · ${email}`)).toBeVisible();

    await button("載入搜尋歷史").click();
    const historyResponse = page.waitForResponse((response) =>
      new URL(response.url()).pathname === `/api/v1/search-runs/${id}` && response.request().method() === "GET",
    );
    await page.getByRole("button", { name: new RegExp(`${id.slice(0, 8)}$`) }).click();
    const reopened = await historyResponse;
    expect(reopened.ok()).toBe(true);
    const reopenedRun = await reopened.json();
    expect(reopenedRun.request.query).toBe(longIdea);
    expect(reopenedRun.settings.query_expansion_version).toBe("sentence-expansion-v2");
    expect(reopenedRun.comparisons).toEqual([
      expect.objectContaining({ document_id: documentId, items }),
    ]);
    await expect(page.getByText(`已保存的查詢 · ${longIdea} · IPC C08F`, { exact: true })).toBeVisible();
    const matrix = page.getByRole("table", { name: "跨文件比對矩陣" });
    await expect(matrix.getByRole("columnheader", { name: /公開 202639611/ })).toBeVisible();
    const savedEvidence = matrix.getByRole("cell").filter({ hasText: citation.quote });
    await savedEvidence.getByText("原文證據與定位", { exact: true }).click();
    await expect(savedEvidence.getByText(citation.xpath, { exact: true })).toBeVisible();

    const reportResponse = page.waitForResponse((response) => response.url().endsWith(`/api/v1/search-runs/${id}/report.pdf`));
    const downloaded = page.waitForEvent("download");
    await button("匯出 PDF 報告").click();
    const report = await reportResponse;
    expect(report.ok()).toBe(true);
    expect(report.headers()["content-type"]).toBe("application/pdf");
    expect(report.headers()["cache-control"]).toBe("private, no-store");
    const download = await downloaded;
    expect(download.suggestedFilename()).toBe(`patentscope-${id}.pdf`);
    expect(await download.failure()).toBeNull();
    const reportPath = testInfo.outputPath("official-patent-report.pdf");
    await download.saveAs(reportPath);
    const inspect = fileURLToPath(new URL("../../../scripts/inspect_test_report.py", import.meta.url));
    const { stdout } = await promisify(execFile)(
      process.env.PATENTSCOPE_TEST_PYTHON || "python",
      [inspect, reportPath],
      { timeout: 15_000 },
    );
    const { text, links } = JSON.parse(stdout) as { text: string; links: string[] };
    const normalizedText = text.replace(/\s+/gu, "");
    for (const expected of [
      "先前技術研究報告",
      "研究限制",
      "構想與檢索策略",
      "光硬化性樹脂組成物",
      ...longIdea.split("\n"),
      "公開 202639611",
      "經濟部智慧財產局",
      citation.quote,
      citation.xpath,
      citation.artifact_sha256,
    ]) {
      expect(normalizedText, `PDF text contains ${expected}`).toContain(expected.replace(/\s+/gu, ""));
    }
    expect(links).toContain("https://data.gov.tw/dataset/15996");
  } finally {
    await page.getByText("刪除帳號與私人資料", { exact: true }).click();
    await page.getByLabel("確認帳號密碼").fill(password);
    await button("永久刪除我的帳號").click();
    await expect(page.getByText("帳號與伺服器上的私人研究資料已刪除。")).toBeVisible();
  }
});
