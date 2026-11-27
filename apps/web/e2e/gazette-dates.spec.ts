import { expect, test } from "@playwright/test";

test("official gazette dates filter a publication and link its source @gazette", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("API、資料庫與向量擴充功能已就緒。")).toBeVisible();
  await page.getByLabel(/^構想描述（最多 /).fill("photocurable resin composition");
  await page.getByLabel("IPC 篩選（選填）").fill("C08F2/48");
  const start = page.getByLabel("公開／公告起日");
  const end = page.getByLabel("公開／公告迄日");
  const search = page.getByRole("button", { name: "搜尋臺灣專利", exact: true });
  await start.fill("2026-10-01");
  await end.fill("2026-10-01");
  const pending = page.waitForResponse((response) =>
    new URL(response.url()).pathname === "/api/v1/patents/search/hybrid",
  );
  await search.click();
  const response = await pending;
  expect(response.ok()).toBe(true);
  const { items } = await response.json();
  const candidate = items.find((item: { publication_no: string; content_scope: string }) =>
    item.publication_no === "202639611" && item.content_scope === "fulltext",
  );
  expect(candidate?.abstract_excerpt).toBeTruthy();
  expect(candidate.lexical_match_fields).toContain("title_en");
  const publication = page.getByRole("listitem").filter({ hasText: "公開 202639611 · 全文" });
  await expect(publication).toBeVisible({ timeout: 40_000 });
  await expect(publication.getByText(/申請人 .*九州大學.*文件日期 2026-10-01.*IPC .*C08F/)).toBeVisible();
  await expect(publication.getByText(candidate.abstract_excerpt, { exact: true })).toBeVisible();
  await expect(publication.getByText(/相關原因 · 詞彙命中標題.*列入語意檢索候選/)).toBeVisible();
  await expect(publication.getByRole("link", { name: "官方資料集" })).toHaveAttribute("href", "https://data.gov.tw/dataset/9683");
  await expect(page.getByText(/搜尋涵蓋範圍.*最新文件日期 2026-10-01/)).toBeVisible();
  await publication.getByRole("button").click();
  await expect(page.getByText("2024-09-06", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "在智慧財產局查詢公開號 202639611" })).toHaveAttribute("href", "https://tiponet.tipo.gov.tw/S092_OUT/2022/out");
  const source = page.getByRole("listitem").filter({ hasText: "發明公開公報書目" });
  await expect(source.getByRole("link", { name: "官方資料集" })).toHaveAttribute("href", "https://data.gov.tw/dataset/9683");
  await expect(source.getByRole("link", { name: "官方原始檔" })).toHaveAttribute("href", /\/PatentPubRegXMLB_024019\/pubinvention\.xml$/);
  await source.getByText("原檔雜湊與定位", { exact: true }).click();
  await expect(source.getByText("5eb3c531a3795e685f802289195da4f1779b8ca9eefef3e2f13ea8a85e634558")).toBeVisible();
  await expect(source.getByText("/tw-patent-applications/tw-patent-application[1]/tw-bibliographic-data-application", { exact: true })).toBeVisible();
  await expect(source.getByLabel(/FTPS 位址/)).toHaveValue("ftps://ftp.tipo.gov.tw/PatentPubRegXMLB/115/PatentPubRegXMLB_024019/pubinvention.xml");
  await start.fill("2026-10-02");
  await end.fill("2026-10-02");
  await search.click();
  await expect(page.getByText("已索引的資料中沒有符合這次條件的結果。")).toBeVisible({ timeout: 40_000 });
  await expect(publication).toHaveCount(0);
});
