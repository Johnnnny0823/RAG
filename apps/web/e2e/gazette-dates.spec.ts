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
  await search.click();
  const publication = page.getByRole("listitem").filter({ hasText: "公開 202639611 · 全文" });
  await expect(publication).toBeVisible({ timeout: 40_000 });
  await expect(page.getByText(/搜尋涵蓋範圍.*最新文件日期 2026-10-01/)).toBeVisible();
  await publication.getByRole("button").click();
  await expect(page.getByText("2024-09-06", { exact: true })).toBeVisible();
  const source = page.getByRole("listitem").filter({ hasText: "發明公開公報書目" });
  await expect(source.getByRole("link", { name: "官方資料集" })).toHaveAttribute("href", "https://data.gov.tw/dataset/9683");
  await expect(source.getByRole("link", { name: "官方原始檔" })).toHaveAttribute("href", /\/PatentPubRegXMLB_024019\/pubinvention\.xml$/);
  await start.fill("2026-10-02");
  await end.fill("2026-10-02");
  await search.click();
  await expect(page.getByText("已索引的資料中沒有符合這次條件的結果。")).toBeVisible({ timeout: 40_000 });
  await expect(publication).toHaveCount(0);
});
