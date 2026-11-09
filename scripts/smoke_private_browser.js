async (page) => {
  const button = (name) => page.getByRole("button", { name, exact: true });
  const visible = (text) => page.getByText(text).waitFor({ state: "visible", timeout: 180_000 });
  const password = "browser-smoke-" + Date.now();
  const email = (label) => `demo-${label}-${Date.now()}@example.invalid`;
  const first = email("owner");

  async function signIn(address, register) {
    if (register) await button("建立帳號").click();
    await page.getByLabel("電子郵件").fill(address);
    await page.getByLabel("密碼（至少 12 字元）").fill(password);
    await button(register ? "註冊並登入" : "登入").click();
    await visible("目前帳號 · " + address);
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
  await patent.getByRole("button").click();
  await button("比對並保存證據").click();
  const quote = page.locator("blockquote");
  await quote.waitFor({ state: "visible", timeout: 180_000 });
  const originalQuote = await quote.innerText();
  await button("登出此頁").click();
  if (await quote.count() || await patent.count()) throw new Error("Private results remained after logout");
  await signIn(email("other"), true);
  await button("載入搜尋歷史").click();
  await visible("此帳號還沒有保存的搜尋。");
  await button("登出此頁").click();
  await signIn(first, false);
  await button("載入搜尋歷史").click();
  await page.getByRole("button", { name: new RegExp(id.slice(0, 8) + "$") }).click();
  await visible("已保存的查詢 · 動態導通電阻");
  await page.getByText("已保存的檢索策略", { exact: true }).click();
  await page.getByText("動態導通電阻量測電路", { exact: true }).filter({ visible: true }).first().waitFor();
  await patent.getByRole("button").click();
  await quote.waitFor({ state: "visible", timeout: 180_000 });
  if (await quote.innerText() !== originalQuote) throw new Error("Saved evidence changed");
  await button("登出此頁").click();
  return "Private browser smoke passed: preview, save, isolation and evidence replay";
}
