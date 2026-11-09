async (page) => {
  const button = (name) => page.getByRole("button", { name, exact: true });
  const visible = (text) => page.getByText(text).waitFor({ state: "visible", timeout: 180_000 });
  const password = "browser-smoke-" + Date.now();
  const email = (label) => `demo-${label}-${Date.now()}@example.invalid`;
  const first = email("owner");
  const projectName = "動態導通電阻研究";

  async function signIn(address, register) {
    if (register) await button("建立帳號").click();
    await page.getByLabel("電子郵件").fill(address);
    await page.getByLabel("密碼（至少 12 字元）").fill(password);
    const loginResponse = page.waitForResponse((response) => response.url().endsWith("/api/v1/auth/login"));
    await button(register ? "註冊並登入" : "登入").click();
    await visible("目前帳號 · " + address);
    return (await (await loginResponse).json()).access_token;
  }

  await signIn(first, true);
  await page.getByLabel("構想描述（最多 160 字）").fill("動態導通電阻");
  await button("新增特徵").click();
  await page.getByLabel("特徵描述", { exact: true }).fill("動態導通電阻量測電路");
  await page.getByLabel("繁中檢索詞（逗號分隔）").fill("動態導通電阻");
  await page.getByLabel("IPC 篩選（選填）").fill("G01R");
  const patent = page.getByRole("listitem").filter({ hasText: "公開 202640162 · 全文" });
  await button("搜尋臺灣專利").click();
  await visible("本次查詢 · 動態導通電阻");
  await button("載入搜尋歷史").click();
  await visible("此帳號還沒有保存的搜尋。");
  const saveResponse = page.waitForResponse((response) =>
    response.url().endsWith("/api/v1/search-runs") && response.request().method() === "POST"
  );
  await button("搜尋並保存").click();
  const response = await saveResponse;
  if (response.status() !== 201) throw new Error("Expected a saved run");
  const { id } = await response.json();
  await visible("已保存的查詢 · 動態導通電阻");
  await page.getByText("建立研究專案", { exact: true }).click();
  await page.getByLabel("專案名稱").fill(projectName);
  await page.getByLabel("專案說明").fill("瀏覽器驗收使用的公開技術案例");
  await button("新增研究專案").click();
  const assignment = page.getByLabel("歸檔至研究專案");
  const projectOption = assignment.getByRole("option", { name: projectName });
  await projectOption.waitFor({ state: "attached" });
  const projectId = await projectOption.getAttribute("value");
  await assignment.selectOption({ label: projectName });
  await button("更新歸檔").click();
  await visible("目前歸檔 · " + projectName);
  await patent.getByRole("button").click();
  await button("比對並保存證據").click();
  const quote = page.locator("blockquote");
  await quote.waitFor({ state: "visible", timeout: 180_000 });
  const originalQuote = await quote.innerText();
  await button("登出此頁").click();
  if (await quote.count() || await patent.count()) throw new Error("Private results remained after logout");
  const otherToken = await signIn(email("other"), true);
  await button("載入搜尋歷史").click();
  await visible("此帳號還沒有保存的搜尋。");
  if (await page.getByRole("option", { name: projectName }).count()) throw new Error("Private project leaked");
  const headers = { Authorization: "Bearer " + otherToken };
  const filtered = await page.request.get(new URL("/api/v1/search-runs?project_id=" + projectId, page.url()).href, { headers });
  const moved = await page.request.patch(new URL(`/api/v1/search-runs/${id}/project`, page.url()).href, {
    headers, data: { project_id: null },
  });
  if (filtered.status() !== 404 || moved.status() !== 404) throw new Error("Project or run access was not isolated");
  await button("登出此頁").click();
  await signIn(first, false);
  await page.getByLabel("依研究專案篩選").selectOption({ label: projectName });
  await button("載入搜尋歷史").click();
  await page.getByRole("button", { name: new RegExp(id.slice(0, 8) + "$") }).click();
  await visible("已保存的查詢 · 動態導通電阻");
  await visible("目前歸檔 · " + projectName);
  await page.getByText("已保存的檢索策略", { exact: true }).click();
  await page.getByText("動態導通電阻量測電路", { exact: true }).filter({ visible: true }).first().waitFor();
  await patent.getByRole("button").click();
  await quote.waitFor({ state: "visible", timeout: 180_000 });
  if (await quote.innerText() !== originalQuote) throw new Error("Saved evidence changed");
  await assignment.selectOption({ label: "未歸檔" });
  await button("更新歸檔").click();
  await visible("目前歸檔 · 未歸檔");
  await button("載入搜尋歷史").click();
  await visible("此專案還沒有搜尋紀錄。");
  await button("登出此頁").click();
  return "Private browser smoke passed: save, project assignment and removal, isolation and evidence replay";
}
