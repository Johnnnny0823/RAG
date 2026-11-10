import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

test("workspace uses the live API and persists project changes", async ({ page, request }, testInfo) => {
  const browserErrors: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(message.text());
  });

  const email = `e2e-${randomUUID()}@example.invalid`;
  const password = randomUUID();
  const button = (name: string) => page.getByRole("button", { name, exact: true });

  try {
    expect((await request.get("/api/v1/projects")).status()).toBe(401);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "PatentScope AI" })).toBeVisible();
    await expect(page.getByText("API、資料庫與向量擴充功能已就緒。")).toBeVisible();

    await button("建立帳號").click();
    await page.getByLabel("電子郵件").fill(email);
    await page.getByLabel("密碼（至少 12 字元）").fill(password);
    await button("註冊並登入").click();
    await expect(page.getByText(`目前帳號 · ${email}`)).toBeVisible();

    await page.getByText("建立研究專案", { exact: true }).click();
    await page.getByLabel("專案名稱", { exact: true }).fill("瀏覽器測試專案");
    await button("新增研究專案").click();
    const project = page.getByLabel("依研究專案篩選");
    await expect(project.getByRole("option", { name: "瀏覽器測試專案" })).toBeAttached();
    await project.selectOption({ label: "瀏覽器測試專案" });
    await page.getByText("管理研究專案", { exact: true }).click();
    await page.getByLabel("修改專案名稱").fill("已更新的測試專案");
    await button("保存專案資料").click();
    await expect(page.getByText("專案資料已更新。")).toBeVisible();

    await button("登出此頁").click();
    await page.getByLabel("電子郵件").fill(email);
    await page.getByLabel("密碼（至少 12 字元）").fill(password);
    await button("登入").click();
    await expect(page.getByText(`目前帳號 · ${email}`)).toBeVisible();
    await expect(project.getByRole("option", { name: "已更新的測試專案" })).toBeAttached();
    await project.selectOption({ label: "已更新的測試專案" });
    await page.getByText("管理研究專案", { exact: true }).click();
    await button("刪除空白專案").click();
    await button("確認刪除空白專案").click();
    await expect(page.getByText("空白專案已刪除。")).toBeVisible();
    await expect(project.getByRole("option", { name: "已更新的測試專案" })).toHaveCount(0);

    await page.getByText("刪除帳號與私人資料", { exact: true }).click();
    await page.getByLabel("確認帳號密碼").fill(password);
    await button("永久刪除我的帳號").click();
    await expect(page.getByText("帳號與伺服器上的私人研究資料已刪除。")).toBeVisible();
  } catch (error) {
    await testInfo.attach("browser-errors", {
      body: browserErrors.join("\n"),
      contentType: "text/plain",
    });
    throw error;
  }
});
