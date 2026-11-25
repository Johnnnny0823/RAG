import { expect, test } from "@playwright/test";

const versions = [
  {
    label: "公開 202640162",
    scope: "全文",
    stage: "publication",
    hash: "838091d244ebaf021106f9efa390c33beb4140a92590b9fbe613c5ed5937d047",
  },
  {
    label: "公告 I941082",
    scope: "請求項",
    stage: "grant",
    // Archived FTPS index of grant issue 053028; the moving S01 copy has another hash.
    hash: "60936a7ab763fbb8bd79b8a3071aa89d43da3ffe4ef65928734a9ddc70827a4a",
  },
];

test("publication and grant keep separate claim citations @versions", async ({ page }) => {
  test.setTimeout(300_000);
  const button = (name: string) => page.getByRole("button", { name, exact: true });
  await page.goto("/");
  await page.getByLabel(/^構想描述（最多 /).fill("動態導通電阻");
  await button("新增特徵").click();
  await page.getByLabel("特徵描述", { exact: true }).fill("動態導通電阻量測電路");
  await page.getByLabel("繁中檢索詞（逗號分隔）").fill("動態導通電阻");
  await page.getByLabel("IPC 篩選（選填）").fill("G01R");
  await page.getByLabel("申請人（中英文名稱）").fill("陽明交通");
  await button("搜尋臺灣專利").click();

  const documentIds = new Set<string>();
  for (const version of versions) {
    const result = page.getByRole("listitem").filter({ hasText: `${version.label} · ${version.scope}` });
    await expect(result).toBeVisible({ timeout: 60_000 });
    const claimsResponse = page.waitForResponse((response) => /\/api\/v1\/patents\/[^/]+\/claims$/.test(response.url()));
    await result.getByRole("button").click();
    const claims = await claimsResponse;
    expect(claims.ok()).toBe(true);
    const { document_id: documentId, claims: originalClaims } = await claims.json();
    documentIds.add(documentId);
    const detail = await page.request.get(`/api/v1/patents/${documentId}`);
    expect(detail.ok()).toBe(true);
    const metadata = await detail.json();
    expect(metadata.application_no).toBe("114106690");
    expect(metadata.document_stage).toBe(version.stage);
    expect(originalClaims).toHaveLength(13);

    const comparisonResponse = page.waitForResponse((response) =>
      new URL(response.url()).pathname === `/api/v1/patents/${documentId}/compare` &&
      response.request().method() === "POST", { timeout: 110_000 },
    );
    await button("比對本次搜尋特徵").click();
    const comparison = await comparisonResponse;
    expect(comparison.ok()).toBe(true);
    const data = await comparison.json();
    expect(data.document_id).toBe(documentId);
    expect(data.document_sha256).toBe(metadata.document_sha256);
    const citation = data.items[0].evidence;
    expect(citation).toBeTruthy();
    expect(citation.kind).toBe("claim");
    expect(citation.artifact_sha256).toBe(version.hash);
    const claim = originalClaims.find((item: { claim_number: number }) => item.claim_number === citation.ordinal);
    expect(claim).toBeTruthy();
    expect(claim.source).toEqual({ xpath: citation.xpath, artifact_sha256: version.hash });
    expect(Array.from(claim.text as string).slice(citation.char_start, citation.char_end).join("")).toBe(citation.quote);
  }

  expect(documentIds.size).toBe(2);
  const matrix = page.getByRole("table", { name: "跨文件比對矩陣" });
  const cells = matrix.getByRole("row").filter({ has: page.getByRole("rowheader", { name: "動態導通電阻量測電路" }) }).getByRole("cell");
  await expect(cells).toHaveCount(2);
  for (const [index, version] of versions.entries()) {
    await expect(matrix.getByRole("columnheader").nth(index + 1)).toContainText(version.label);
    await cells.nth(index).getByText("原文證據與定位", { exact: true }).click();
    await expect(cells.nth(index).getByText(`原始檔 SHA-256 · ${version.hash}`)).toBeVisible();
  }
});
