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
  await page.getByLabel("文件種類").selectOption("publication");
  await page.getByLabel("申請人（中英文名稱）").fill("陽明交通");
  await button("搜尋臺灣專利").click();
  await patent.waitFor();
  await visible("文件 公開 · 申請人 陽明交通");
  if (await page.getByRole("listitem").filter({ hasText: "公告 I941082" }).count()) {
    throw new Error("Stage filter kept the grant version");
  }
  await page.getByLabel("公開／公告起日").fill("2026-10-02");
  await page.getByLabel("公開／公告迄日").fill("2026-10-01");
  await button("搜尋臺灣專利").click();
  await page.getByRole("alert").filter({ hasText: "起日不得晚於迄日" }).waitFor();
  await page.getByLabel("公開／公告起日").fill("");
  await page.getByLabel("公開／公告迄日").fill("");
  await page.getByLabel("文件種類").selectOption("");
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
  await visible("申請人 陽明交通");
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
  await button("收藏此版本").click();
  await visible("已收藏此文件版本。");
  await page.getByLabel("依研究專案篩選").selectOption({ label: projectName });
  const sessionTitle = "公開技術拆解驗收";
  await page.getByLabel("Session 名稱").fill(sessionTitle);
  const sessionResponse = page.waitForResponse((response) =>
    response.url().endsWith("/api/v1/sessions") && response.request().method() === "POST"
  );
  await button("建立 AI Session").click();
  const aiSession = await (await sessionResponse).json();
  await visible("目前 Session · " + sessionTitle);
  const idea = "動態導通電阻";
  await page.getByLabel("Session 構想（最多 160 字）").fill(idea);
  await button("拆解並保存至 Session").click();
  await button("帶入檢索表單").click();
  await visible("已帶入構想及技術草稿，可在檢索前編輯。");
  if (await page.getByLabel("構想描述（最多 160 字）").inputValue() !== idea) {
    throw new Error("Saved AI analysis could not be applied");
  }
  await button("載入專案收藏").click();
  const note = page.getByLabel("私人筆記 · 202640162");
  await note.fill("驗收筆記：核對公開文件的請求項。");
  await button("保存筆記").click();
  await page.getByText("筆記已保存。", { exact: true }).first().waitFor();
  await button("收藏此版本").click();
  await button("比對並保存證據").click();
  const quote = page.locator("blockquote");
  await quote.waitFor({ state: "visible", timeout: 180_000 });
  const originalQuote = await quote.innerText();
  const matrix = page.getByRole("table", { name: "跨文件比對矩陣" });
  await matrix.getByRole("columnheader", { name: /公開 202640162/ }).waitFor();
  const grant = page.getByRole("listitem").filter({ hasText: "公告 I941082 · 請求項" });
  await grant.getByRole("button").click();
  await button("比對並保存證據").click();
  await matrix.getByRole("columnheader", { name: /公告 I941082/ }).waitFor();
  await matrix.getByRole("rowheader", { name: "動態導通電阻量測電路" }).waitFor();
  const evidenceCell = matrix.getByRole("cell").filter({ hasText: originalQuote }).first();
  await evidenceCell.getByText("原文證據與定位", { exact: true }).click();
  await evidenceCell.getByText(/原始檔 SHA-256/).waitFor();
  await button("登出此頁").click();
  if (await quote.count() || await patent.count()) throw new Error("Private results remained after logout");
  const otherToken = await signIn(email("other"), true);
  await button("載入搜尋歷史").click();
  await visible("此帳號還沒有保存的搜尋。");
  if (await page.getByRole("option", { name: projectName }).count()) throw new Error("Private project leaked");
  const headers = { Authorization: "Bearer " + otherToken };
  const projectUrl = new URL(`/api/v1/projects/${projectId}`, page.url()).href;
  for (const result of await Promise.all([
    page.request.get(projectUrl, { headers }),
    page.request.patch(projectUrl, { headers, data: { name: "cross-account fixture" } }),
    page.request.delete(projectUrl, { headers }),
  ])) {
    if (result.status() !== 404) throw new Error("Cross-account project access was not isolated");
  }
  const messageUrl = new URL(`/api/v1/sessions/${aiSession.id}/messages`, page.url()).href;
  const sessionListUrl = new URL(`/api/v1/sessions?project_id=${projectId}`, page.url()).href;
  for (const result of await Promise.all([
    page.request.get(sessionListUrl, { headers }),
    page.request.get(messageUrl, { headers }),
    page.request.post(messageUrl, { headers, data: { query: idea } }),
  ])) {
    if (result.status() !== 404) throw new Error("Cross-account AI Session access was not isolated");
  }
  const filtered = await page.request.get(new URL("/api/v1/search-runs?project_id=" + projectId, page.url()).href, { headers });
  const moved = await page.request.patch(new URL(`/api/v1/search-runs/${id}/project`, page.url()).href, {
    headers, data: { project_id: null },
  });
  if (filtered.status() !== 404 || moved.status() !== 404) throw new Error("Project or run access was not isolated");
  const bookmarkUrl = new URL(`/api/v1/projects/${projectId}/patents`, page.url()).href;
  if ((await page.request.get(bookmarkUrl, { headers })).status() !== 404) throw new Error("Private bookmarks leaked");
  await button("登出此頁").click();
  const ownerToken = await signIn(first, false);
  const ownBookmarks = await page.request.get(bookmarkUrl, { headers: { Authorization: "Bearer " + ownerToken } });
  const items = await ownBookmarks.json();
  if (!ownBookmarks.ok() || items.length !== 1 || items[0].note !== "驗收筆記：核對公開文件的請求項。") {
    throw new Error("Repeated bookmark save changed the note");
  }
  const bookmarkItem = bookmarkUrl + "/" + items[0].document_id;
  for (const response of await Promise.all([
    page.request.put(bookmarkItem, { headers }),
    page.request.patch(bookmarkItem, { headers, data: { note: "cross-account fixture" } }),
    page.request.delete(bookmarkItem, { headers }),
  ])) {
    if (response.status() !== 404) throw new Error("Cross-account bookmark mutation was not blocked");
  }
  await page.getByLabel("依研究專案篩選").selectOption({ label: projectName });
  await button("載入 AI Session").click();
  await button(sessionTitle).click();
  await visible("構想 · " + idea);
  await visible(/AI 技術草稿 · qwen/);
  const auth = { Authorization: "Bearer " + ownerToken };
  const messages = await (await page.request.get(messageUrl, { headers: auth })).json();
  if (messages.length !== 2 || messages[0].role !== "user" || messages[1].role !== "assistant" ||
      !messages[1].content.features.length || !messages[1].content.model_digest) {
    throw new Error("Stored AI turn is incomplete");
  }
  const earlier = await (await page.request.get(messageUrl + "?limit=1&before=" + messages[1].id, { headers: auth })).json();
  if (earlier.length !== 1 || earlier[0].id !== messages[0].id) throw new Error("AI message cursor lost ordering");
  await button("載入專案收藏").click();
  if (await note.inputValue() !== items[0].note) throw new Error("Bookmark note did not persist");
  await page.getByRole("article").filter({ has: note }).getByRole("button", { name: "動態導通電阻量測電路", exact: true }).click();
  await page.getByRole("heading", { name: "專利詳情" }).waitFor();
  await button("載入搜尋歷史").click();
  await page.getByRole("button", { name: new RegExp(id.slice(0, 8) + "$") }).click();
  await visible("已保存的查詢 · 動態導通電阻");
  await visible("申請人 陽明交通");
  await visible("目前歸檔 · " + projectName);
  await matrix.getByRole("columnheader", { name: /公開 202640162/ }).waitFor();
  await matrix.getByRole("columnheader", { name: /公告 I941082/ }).waitFor();
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
  await button("移除收藏").click();
  await button("確認移除收藏及筆記").click();
  await visible("此專案還沒有收藏。");
  if (await note.count()) throw new Error("Removed bookmark note is still visible");
  if (await quote.innerText() !== originalQuote) throw new Error("Removing a bookmark affected saved evidence");
  await page.getByText("管理研究專案", { exact: true }).click();
  await page.getByLabel("修改專案名稱").fill("已更新的動態導通電阻研究");
  await page.getByLabel("修改專案說明").fill("修改後的公開測試說明");
  await button("保存專案資料").click();
  await visible("專案資料已更新。");
  await page.getByRole("paragraph").filter({ hasText: "修改後的公開測試說明" }).waitFor();
  const updatedProject = await (await page.request.get(projectUrl, { headers: auth })).json();
  if (updatedProject.name !== "已更新的動態導通電阻研究") throw new Error("Project rename did not persist");
  await button("刪除空白專案").click();
  const blockedDelete = page.waitForResponse((result) => result.url() === projectUrl && result.request().method() === "DELETE");
  await button("確認刪除空白專案").click();
  if ((await blockedDelete).status() !== 409) throw new Error("Non-empty project could be deleted");
  await page.getByRole("alert").filter({ hasText: "專案仍有搜尋紀錄、收藏或 AI Session" }).waitFor();
  if (!(await page.request.get(messageUrl, { headers: auth })).ok()) throw new Error("Failed project deletion affected its Session");
  await button("取消刪除專案").click();
  const emptyTitle = "待刪除空白專案";
  await page.getByText("建立研究專案", { exact: true }).click();
  await page.getByLabel("專案名稱", { exact: true }).fill(emptyTitle);
  await button("新增研究專案").click();
  const projectSelector = page.getByLabel("依研究專案篩選");
  await projectSelector.selectOption({ label: emptyTitle });
  await page.getByText("管理研究專案", { exact: true }).click();
  await button("刪除空白專案").click();
  await button("確認刪除空白專案").click();
  await visible("空白專案已刪除。");
  if (await projectSelector.getByRole("option", { name: emptyTitle }).count()) throw new Error("Deleted project is still selectable");
  await button("登出此頁").click();
  return "Private browser smoke passed: metadata filters, comparison matrix, projects, AI sessions and isolation";
}
