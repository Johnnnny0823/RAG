import { expect, test } from "@playwright/test";

test("a public document shows the sourced gazette correction for its application @legal-events", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("API、資料庫與向量擴充功能已就緒。")).toBeVisible();
  await page.getByLabel(/^構想描述（最多 /).fill("用於消融細胞的脈衝刺激裝置");
  await page.getByRole("button", { name: "搜尋臺灣專利", exact: true }).click();
  const publication = page.getByRole("listitem").filter({ hasText: "公開 202639186" });
  await expect(publication).toBeVisible({ timeout: 40_000 });
  await publication.getByRole("button").click();

  const event = page.getByRole("listitem").filter({ hasText: "公報更正 · 證書號 I927657" });
  await expect(event).toContainText("卷期 053033");
  await expect(event).toContainText("代理人");
  await expect(event.getByRole("link", { name: "異動公報資料集" })).toHaveAttribute("href", "https://data.gov.tw/dataset/15974");
  await expect(event.getByRole("link", { name: "異動公報原始檔" })).toHaveAttribute("href", "ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud24.xml");
  await event.getByText("異動公報來源定位").click();
  await expect(event).toContainText("97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3");
  await expect(page.getByText(/目前權利狀態.*智慧財產局最新資料/)).toBeVisible();
});
