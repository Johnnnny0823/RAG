import { expect, test } from "@playwright/test";

test("utility model and design expose their actual official content @grant-types", async ({ page }) => {
  await page.goto("/");
  const lookup = page.getByRole("region", { name: "專利號碼查詢" });
  await lookup.getByLabel("號碼類型").selectOption("grant");

  const cases = [
    { number: "M687984", label: "請求項", claims: 16, sections: 0 },
    { number: "D246917", label: "書目與摘要", claims: 0, sections: 0 },
  ];
  if (process.env.PATENTSCOPE_E2E_GRANT_FULLTEXT === "1") {
    cases.push(
      { number: "M688679", label: "全文", claims: 10, sections: 208 },
      { number: "D247328", label: "全文", claims: 0, sections: 7 },
    );
  }
  for (const { number, label, claims, sections } of cases) {
    await lookup.getByLabel("專利號碼").fill(number);
    await lookup.getByRole("button", { name: "查詢專利號碼" }).click();
    const match = lookup.getByRole("listitem").filter({ hasText: new RegExp(`公告 ${number}.*${label}`) });
    await expect(match.first()).toBeVisible();
    await match.first().getByRole("button").click();
    await expect(page.getByText(`請求項（${claims}）`, { exact: true })).toBeVisible();
    await expect(page.getByText(`說明書段落（${sections}）`, { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: `在智慧財產局查詢公告號 ${number}` })).toBeVisible();
    if (number === "M688679") {
      await expect(page.getByRole("heading", { name: "中文摘要" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "英文摘要" })).toBeVisible();
    }
  }
});

test("official identifier lookup opens the correct publication and grant versions @versions", async ({ page, browserName }) => {
  await page.goto("/");
  const lookup = page.getByRole("region", { name: "專利號碼查詢" });
  const kind = lookup.getByLabel("號碼類型");
  const number = lookup.getByLabel("專利號碼");
  const submit = lookup.getByRole("button", { name: "查詢專利號碼" });
  const application = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === "/api/v1/patents" && url.searchParams.get("number_type") === "application";
  });
  await number.fill("114106690");
  await submit.click();
  const response = await application;
  expect(response.ok()).toBe(true);
  await expect(lookup.getByRole("listitem")).toHaveCount(3);
  await expect(lookup.getByText(/公開 202640162.*全文/)).toBeVisible();
  await expect(lookup.getByText(/公開 202640162.*書目與摘要/)).toBeVisible();
  const grant = lookup.getByRole("listitem").filter({ hasText: "公告 I941082" });
  await grant.getByRole("button").click();
  await expect(page.getByRole("heading", { name: "專利詳情" })).toBeVisible();
  await expect(page.getByText("請求項（13）", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "在智慧財產局查詢公告號 I941082" })).toHaveAttribute("href", "https://tiponet.tipo.gov.tw/S092_OUT/2022/out");
  const checkPdfs = process.env.PATENTSCOPE_E2E_GAZETTE_PDFS === "1";
  const gazettePdf = page.getByRole("link", { name: "官方公報 PDF", exact: true });
  if (checkPdfs) {
    await expect(gazettePdf).toHaveAttribute("href", "https://cloud.tipo.gov.tw/S220/downloads/patent/isu053028/pdfdata/114106690.pdf");
  }
  const sourceDisclosures = page.locator("details").filter({ has: page.getByText("原檔雜湊與定位", { exact: true }) });
  await sourceDisclosures.first().getByText("原檔雜湊與定位", { exact: true }).click();
  await expect(sourceDisclosures.first()).toHaveAttribute("open", "");
  if (checkPdfs) {
    await page.getByRole("button", { name: "讀取公報文字" }).click();
    const search = page.getByLabel("在公報文字中查找");
    await search.fill("I941082");
    await expect(page.getByText("PDF 第 1 頁", { exact: true })).toBeVisible();
    await page.getByText("PDF 第 1 頁", { exact: true }).click();
    await expect(page.getByText(/證書號數：I941082/)).toBeVisible();
  }
  await page.getByRole("button", { name: "查詢同案其他版本" }).click();
  await page.getByRole("button", { name: "公開 202640162 · 全文", exact: true }).click();
  await expect(page.getByRole("link", { name: "在智慧財產局查詢公開號 202640162" })).toBeVisible();
  await expect(sourceDisclosures.first()).not.toHaveAttribute("open", "");
  if (checkPdfs) {
    await expect(gazettePdf).toHaveAttribute("href", "https://cloud.tipo.gov.tw/S220/downloads/invention/pub024019/pdfdata/114106690.pdf");
  }

  await kind.selectOption("publication");
  await number.fill("２０２６４０１６２");
  await submit.click();
  await expect(lookup.getByRole("listitem")).toHaveCount(2);
  await expect(lookup.getByText(/公告 I941082/)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "專利詳情" })).toHaveCount(0);

  await kind.selectOption("grant");
  await number.fill("i941082");
  await submit.click();
  await expect(lookup.getByRole("listitem")).toHaveCount(1);
  await expect(grant).toBeVisible();

  await kind.selectOption("publication");
  await number.fill("000000000");
  await submit.click();
  await expect(lookup.getByRole("status")).toHaveText("已索引的資料中沒有符合這個號碼的文件。");
  await expect(lookup.getByRole("listitem")).toHaveCount(0);

  await number.fill("invalid");
  await submit.click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(lookup.getByRole("status")).toHaveCount(0);

  if (checkPdfs) {
    const search = page.getByRole("region", { name: "公報 PDF 檢索" });
    await search.getByLabel("公報檢索詞").fill("動態導通電阻");
    await search.getByRole("button", { name: "搜尋公報 PDF" }).click();
    const publication = search.getByRole("listitem").filter({ hasText: "公開 202640162 · 第 1 頁" });
    const grant = search.getByRole("listitem").filter({ hasText: "公告 I941082 · 第 1 頁" });
    await expect(publication.getByRole("link")).toHaveAttribute("href", /\/invention\/pub024019\/pdfdata\/114106690\.pdf#page=1$/);
    await expect(grant.getByRole("link")).toHaveAttribute("href", /\/patent\/isu053028\/pdfdata\/114106690\.pdf#page=1$/);
    await publication.getByRole("button").click();
    await expect(page.getByRole("link", { name: "在智慧財產局查詢公開號 202640162" })).toBeVisible();

    await search.getByLabel("公報階段").selectOption("grant");
    await search.getByRole("button", { name: "搜尋公報 PDF" }).click();
    await expect(search.getByRole("listitem")).toHaveCount(2);
    await expect(search.getByText(/公開 202640162/)).toHaveCount(0);
    if (browserName !== "chromium") return;

    // Chromium supports overriding this request body to exercise the small corpus.
    await page.route("**/api/v1/patents/gazette-pdfs/search", (route) =>
      route.continue({ postData: JSON.stringify({ ...route.request().postDataJSON(), limit: 1 }) }),
    );
    await search.getByRole("button", { name: "搜尋公報 PDF" }).click();
    await expect(search.getByRole("listitem")).toHaveCount(1);
    await expect(search.getByRole("listitem")).toHaveText(/公告 I941082 · 第 2 頁/);
    await search.getByLabel("公報檢索詞").fill("另一個檢索詞");
    await search.getByRole("button", { name: "下一頁" }).click();
    await expect(search.getByRole("listitem")).toHaveText(/公告 I941082 · 第 1 頁/);
    await expect(search.getByRole("button", { name: "下一頁" })).toBeDisabled();
    await search.getByRole("button", { name: "上一頁" }).click();
    await expect(search.getByRole("listitem")).toHaveText(/公告 I941082 · 第 2 頁/);
  }
});
