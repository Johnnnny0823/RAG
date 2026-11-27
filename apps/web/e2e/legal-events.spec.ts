import { expect, test } from "@playwright/test";

test("utility model and design display their same-certificate official corrections @grant-events", async ({ page }) => {
  await page.goto("/");
  const lookup = page.getByRole("region", { name: "專利號碼查詢" });
  await lookup.getByLabel("號碼類型").selectOption("grant");
  for (const [number, field] of [["M681479", "代理人"], ["D246955", "設計人"]]) {
    await lookup.getByLabel("專利號碼").fill(number);
    await lookup.getByRole("button", { name: "查詢專利號碼" }).click();
    await lookup.getByRole("listitem").filter({ hasText: `公告 ${number}` }).getByRole("button").click();
    const correction = page.getByRole("listitem").filter({ hasText: `公報更正 · 證書號 ${number} · 卷期 053033` });
    await expect(correction.getByText(new RegExp(field))).toBeVisible();
    await expect(correction.getByRole("link", { name: "異動公報原始檔" })).toHaveAttribute("href", /PatentIsuModXML_053033\/sud24\.xml$/);
    await correction.getByText("異動公報來源定位", { exact: true }).click();
    await expect(correction.getByText(/97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3/)).toBeVisible();
  }
});

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

test("an official grant links its dated extinguishment to the matching certificate @legal-events", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("API、資料庫與向量擴充功能已就緒。")).toBeVisible();
  await page.getByLabel(/^構想描述（最多 /).fill("具深度學習演算法之咖啡豆檢測系統");
  await page.getByLabel("文件種類").selectOption("grant");
  await page.getByRole("button", { name: "搜尋臺灣專利", exact: true }).click();
  const grant = page.getByRole("listitem").filter({ hasText: "公告 I874215" });
  await expect(grant).toBeVisible({ timeout: 40_000 });
  await grant.getByRole("button").click();

  const event = page.getByRole("listitem").filter({ hasText: "專利權消滅公告 · 證書號 I874215" });
  await expect(event).toContainText("卷期 053033");
  await expect(event).toContainText("公報記載消滅日 2026-02-21");
  await expect(event).toContainText("未依限繳費");
  await expect(event.getByRole("link", { name: "異動公報原始檔" })).toHaveAttribute("href", "ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud08.xml");
  await event.getByText("異動公報來源定位").click();
  await expect(event).toContainText("213b98e7337a0f99b74b9eff59ce0d92f0f27ccecf665892f8ee48b8423bd964");
  await expect(event).toContainText("sud08'][1447]");
});

test("official identifier lookup opens synchronized gazette events @legal-events", async ({ page }) => {
  await page.goto("/");
  const lookup = page.getByRole("region", { name: "專利號碼查詢" });
  const cases = [
    {
      type: "grant",
      number: "I874215",
      label: "專利權消滅公告 · 證書號 I874215",
      detail: "公報記載消滅日 2026-02-21",
      file: "sud08.xml",
      hash: "213b98e7337a0f99b74b9eff59ce0d92f0f27ccecf665892f8ee48b8423bd964",
    },
    {
      type: "publication",
      number: "202639186",
      label: "公報更正 · 證書號 I927657",
      detail: "代理人",
      file: "sud24.xml",
      hash: "97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3",
    },
  ];
  for (const sample of cases) {
    await lookup.getByLabel("號碼類型").selectOption(sample.type);
    await lookup.getByLabel("專利號碼").fill(sample.number);
    await lookup.getByRole("button", { name: "查詢專利號碼" }).click();
    await lookup.getByRole("listitem").filter({ hasText: sample.number }).first().getByRole("button").click();
    const event = page.getByRole("listitem").filter({ hasText: sample.label });
    await expect(event).toContainText(sample.detail);
    await expect(event).toContainText("卷期 053033");
    await expect(event.getByRole("link", { name: "異動公報原始檔" })).toHaveAttribute("href", `ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/${sample.file}`);
    await event.getByText("異動公報來源定位").click();
    await expect(event).toContainText(sample.hash);
  }
});
