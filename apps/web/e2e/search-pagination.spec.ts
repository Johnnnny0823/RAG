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
  await page.getByLabel("構想描述（最多 160 字）").fill("動態導通電阻");

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
