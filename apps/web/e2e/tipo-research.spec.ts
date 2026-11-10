import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
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

test("official publication supports saved evidence and PDF export @tipo", async ({ page }) => {
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
    await page.getByLabel("構想描述（最多 160 字）").fill("光硬化性樹脂組成物");
    await button("新增特徵").click();
    await page.getByLabel("特徵描述", { exact: true }).fill("光硬化性樹脂組成物");
    await page.getByLabel("繁中檢索詞（逗號分隔）").fill("光硬化性樹脂組成物");
    await page.getByLabel("IPC 篩選（選填）").fill("C08F");
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
    const { claims: originalClaims } = await claims.json();
    await expect(page.getByRole("heading", { name: "專利詳情" })).toBeVisible();
    await expect(page.getByRole("link", { name: "官方資料集" }).first()).toHaveAttribute("href", "https://data.gov.tw/dataset/15996");
    await page.getByText(/^請求項（\d+）$/).click();
    await expect(page.getByText(/^第 1 項 ·/).first()).toBeVisible();

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
    const pdf = (await readFile(await download.path())).toString("latin1");
    expect(pdf).toMatch(/^%PDF-\d\.\d/);
    expect(pdf).toMatch(/\/Type\s*\/Page\b/);
    expect(pdf).toMatch(/%%EOF\s*$/);
  } finally {
    await page.getByText("刪除帳號與私人資料", { exact: true }).click();
    await page.getByLabel("確認帳號密碼").fill(password);
    await button("永久刪除我的帳號").click();
    await expect(page.getByText("帳號與伺服器上的私人研究資料已刪除。")).toBeVisible();
  }
});
