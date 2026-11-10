import { expect, test } from "@playwright/test";

type Candidate = {
  document_id: string;
  publication_no: string;
  fusion_rank: number;
  rerank_rank: number | null;
};

test("local model reranks the same official candidates @versions", async ({ page }) => {
  test.setTimeout(240_000);
  await page.goto("/");
  await page.getByLabel("構想描述（最多 160 字）").fill("動態導通電阻");
  await page.getByLabel("IPC 篩選（選填）").fill("G01R27/02");
  await page.getByLabel("申請人（中英文名稱）").fill("陽明交通");
  const search = page.getByRole("button", { name: "搜尋臺灣專利", exact: true });

  async function submit(rerank: boolean) {
    const pending = page.waitForResponse((response) =>
      new URL(response.url()).pathname === "/api/v1/patents/search/hybrid" &&
      response.request().method() === "POST",
      { timeout: 185_000 },
    );
    await search.click();
    const response = await pending;
    expect(response.request().postDataJSON()).toMatchObject({ rerank });
    expect(response.ok(), `Search status ${response.status()}`).toBe(true);
    return response.json();
  }

  const baseline = await submit(false);
  expect(baseline.reranker).toBeNull();
  const original: Candidate[] = baseline.items;
  expect(original.map((item) => item.publication_no).sort()).toEqual(["202640162", "I941082"]);
  const rerank = page.getByRole("checkbox", { name: "使用本機模型重排序" });
  await rerank.check();
  const result = await submit(true);
  expect(result.reranker).toMatchObject({
    candidate_count: original.length,
    model_name: expect.any(String),
    model_digest: expect.stringMatching(/^[a-f0-9]{64}$/),
    version: "ollama-listwise-v2",
  });
  const ranked: Candidate[] = result.items;
  expect(ranked.map((item) => item.document_id).sort()).toEqual(original.map((item) => item.document_id).sort());
  await expect(rerank).toBeChecked();
  const rows = page.getByRole("listitem").filter({ hasText: /^第 \d+ 筆 ·/ });
  await expect(rows).toHaveCount(ranked.length);
  for (const [index, candidate] of ranked.entries()) {
    expect(candidate.rerank_rank).toBe(index + 1);
    expect(candidate.fusion_rank).toBe(original.find((item) => item.document_id === candidate.document_id)?.fusion_rank);
    await expect(rows.nth(index)).toContainText(candidate.publication_no);
    await expect(rows.nth(index)).toContainText(`重排 ${index + 1}`);
  }
});
