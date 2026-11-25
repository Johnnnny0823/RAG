import { expect, test } from "@playwright/test";

const hybrid = "/api/v1/patents/search/hybrid";

test("search distinguishes invalid filters from a missing model", async ({ page }) => {
  await page.goto("/");
  const search = page.getByRole("button", { name: "搜尋臺灣專利", exact: true });
  const alert = page.getByRole("alert");
  await expect(search).toBeDisabled();
  await page.getByLabel(/^構想描述（最多 /).fill("光硬化性樹脂組成物");

  const from = page.getByLabel("公開／公告起日");
  const to = page.getByLabel("公開／公告迄日");
  await from.fill("2026-10-02");
  await to.fill("2026-10-01");
  const invalidResponse = page.waitForResponse((response) => response.url().endsWith(hybrid));
  await search.click();
  const invalid = await invalidResponse;
  expect(invalid.status()).toBe(422);
  expect((await invalid.json()).error.code).toBe("INVALID_REQUEST");
  await expect(alert).toContainText("起日不得晚於迄日");

  await from.fill("");
  await to.fill("");
  const unavailableResponse = page.waitForResponse((response) => response.url().endsWith(hybrid));
  await search.click();
  const unavailable = await unavailableResponse;
  expect(unavailable.status()).toBe(503);
  expect((await unavailable.json()).error.code).toBe("EMBEDDING_UNAVAILABLE");
  await expect(alert).toHaveText("目前無法使用本機嵌入模型。");
  await expect(page.getByText("已索引的資料中沒有符合這次條件的結果。")).toHaveCount(0);
  await expect(search).toBeEnabled();
});

test("a stalled search triggers the client deadline and can be retried", async ({ page }) => {
  await page.addInitScript(() => {
    const timeout = AbortSignal.timeout.bind(AbortSignal);
    AbortSignal.timeout = (ms) => {
      if (ms !== 180_000) return timeout(ms);
      AbortSignal.timeout = timeout;
      return timeout(800);
    };
  });
  // Hold the network request without returning a synthetic API response.
  await page.route(`**${hybrid}`, () => {});
  await page.goto("/");
  const idea = page.getByLabel(/^構想描述（最多 /);
  await idea.fill("光硬化性樹脂組成物");
  const search = page.getByRole("button", { name: "搜尋臺灣專利", exact: true });
  const request = page.waitForRequest((entry) => entry.url().endsWith(hybrid));
  await search.click();
  await request;
  await expect(page.getByRole("alert")).toHaveText("服務回應逾時，請重試。");
  await expect(idea).toHaveValue("光硬化性樹脂組成物");
  await expect(search).toBeEnabled();
  await page.unrouteAll({ behavior: "ignoreErrors" });

  const response = page.waitForResponse((entry) => entry.url().endsWith(hybrid));
  await search.click();
  expect((await response).status()).toBe(503);
  await expect(page.getByRole("alert")).toHaveText("目前無法使用本機嵌入模型。");
});
