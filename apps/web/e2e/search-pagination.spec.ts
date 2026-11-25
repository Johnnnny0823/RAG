import { expect, test } from "@playwright/test";

type SearchPage = {
  offset: number;
  limit: number;
  has_more: boolean;
  items: { document_id: string; publication_no: string; fusion_rank: number }[];
};

test("official results keep fusion order across pages @versions", async ({ page }) => {
  test.setTimeout(180_000);
  await page.goto("/");
  await page.getByLabel(/^構想描述（最多 /).fill("動態導通電阻");

  const button = (name: string) => page.getByRole("button", { name, exact: true });
  const previous = button("上一頁");
  const next = button("下一頁");
  const results = page.getByRole("listitem").filter({ hasText: /^第 \d+ 筆 ·/ });

  async function readPage(action: typeof next, offset: number) {
    const pending = page.waitForResponse((response) =>
      new URL(response.url()).pathname === "/api/v1/patents/search/hybrid" &&
      response.request().method() === "POST",
      { timeout: 60_000 },
    );
    await action.click();
    const response = await pending;
    expect(response.ok()).toBe(true);
    expect(response.request().postDataJSON()).toMatchObject({ offset, rerank: false });
    const data: SearchPage = await response.json();
    expect(data.offset).toBe(offset);
    expect(data.items.length).toBeGreaterThan(0);
    expect(data.items.length).toBeLessThanOrEqual(data.limit);
    await expect(results).toHaveCount(data.items.length);
    for (const [index, item] of data.items.entries()) {
      const rank = offset + index + 1;
      expect(item.fusion_rank).toBe(rank);
      await expect(results.nth(index)).toContainText(`第 ${rank} 筆 ·`);
      await expect(results.nth(index)).toContainText(item.publication_no);
    }
    return data;
  }

  const first = await readPage(button("搜尋臺灣專利"), 0);
  expect(first.has_more).toBe(true);
  expect(first.items).toHaveLength(first.limit);
  await expect(previous).toBeDisabled();
  const second = await readPage(next, first.limit);
  const ids = [...first.items, ...second.items].map((item) => item.document_id);
  expect(new Set(ids).size).toBe(ids.length);
  const returned = await readPage(previous, 0);
  expect(returned.items).toEqual(first.items);
  await expect(previous).toBeDisabled();
});

test("saved search restores its ranked snapshot and paginates it @versions", async ({ page }) => {
  test.setTimeout(180_000);
  const email = `pagination-${crypto.randomUUID()}@example.invalid`;
  const password = crypto.randomUUID();
  const button = (name: string) => page.getByRole("button", { name, exact: true });
  const previous = button("上一頁");
  const next = button("下一頁");
  const results = page.getByRole("listitem").filter({ hasText: /^第 \d+ 筆 ·/ });
  const account = page.getByText(`目前帳號 · ${email}`, { exact: true });
  await page.goto("/");

  async function signIn(submit: string) {
    await page.getByLabel("電子郵件").fill(email);
    await page.getByLabel("密碼（至少 12 字元）").fill(password);
    await button(submit).click();
    await expect(account).toBeVisible();
  }

  await button("建立帳號").click();
  await signIn("註冊並登入");
  try {
    await page.getByLabel(/^構想描述（最多 /).fill("動態導通電阻");
    const savedResponse = page.waitForResponse((response) =>
      new URL(response.url()).pathname === "/api/v1/search-runs" &&
      response.request().method() === "POST", { timeout: 90_000 },
    );
    const initialSnapshotResponse = page.waitForResponse((response) =>
      /^\/api\/v1\/search-runs\/[^/]+$/.test(new URL(response.url()).pathname) &&
      response.request().method() === "GET", { timeout: 90_000 },
    );
    await button("搜尋並保存").click();
    const saved = await savedResponse;
    expect(saved.status()).toBe(201);
    const { id } = await saved.json();
    const initialSnapshot = await initialSnapshotResponse;
    expect(initialSnapshot.ok()).toBe(true);
    expect(new URL(initialSnapshot.url()).pathname).toBe(`/api/v1/search-runs/${id}`);
    const initial = await initialSnapshot.json();
    await expect(results.first()).toBeVisible();

    await button("登出此頁").click();
    await expect(results).toHaveCount(0);
    await page.reload();
    await signIn("登入");
    await button("載入搜尋歷史").click();

    const restoredResponse = page.waitForResponse((response) =>
      new URL(response.url()).pathname === `/api/v1/search-runs/${id}` &&
      response.request().method() === "GET",
    );
    await page.getByRole("button", { name: new RegExp(`${id.slice(0, 8)}$`) }).click();
    const restored = await restoredResponse;
    expect(restored.ok()).toBe(true);
    const snapshot: { request: { limit: number }; items: SearchPage["items"] } = await restored.json();
    expect(snapshot.items).toEqual(initial.items);
    expect(snapshot.request).toEqual(initial.request);
    expect(snapshot.items.length).toBeGreaterThan(snapshot.request.limit);
    const ids = snapshot.items.map((item) => item.document_id);
    expect(new Set(ids).size).toBe(ids.length);

    const { limit } = snapshot.request;
    async function expectSavedPage(offset: number) {
      const items = snapshot.items.slice(offset, offset + limit);
      await expect(results).toHaveCount(items.length);
      for (const [index, item] of items.entries()) {
        const rank = offset + index + 1;
        expect(item.fusion_rank).toBe(rank);
        await expect(results.nth(index)).toContainText(`第 ${rank} 筆 ·`);
        await expect(results.nth(index)).toContainText(item.publication_no);
      }
    }

    await expectSavedPage(0);
    const searchCalls: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname === "/api/v1/patents/search/hybrid") {
        searchCalls.push(request.url());
      }
    });
    for (let offset = limit; offset < snapshot.items.length; offset += limit) {
      await next.click();
      await expectSavedPage(offset);
    }
    await expect(next).toBeDisabled();
    await previous.click();
    const lastOffset = Math.floor((snapshot.items.length - 1) / limit) * limit;
    await expectSavedPage(lastOffset - limit);
    expect(searchCalls).toEqual([]);
  } finally {
    await page.getByText("刪除帳號與私人資料", { exact: true }).click();
    await page.getByLabel("確認帳號密碼").fill(password);
    await button("永久刪除我的帳號").click();
    await expect(page.getByText("帳號與伺服器上的私人研究資料已刪除。")).toBeVisible();
  }
});
