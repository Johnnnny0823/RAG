import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

test("signed-in users can reopen and cancel a pending search without entering it again @pending-search", async ({ page, request }) => {
  const credentials = { email: `resume-${randomUUID()}@example.invalid`, password: randomUUID() };
  expect((await request.post("/api/v1/auth/register", { data: credentials })).status()).toBe(201);
  const login = await request.post("/api/v1/auth/login", { data: credentials });
  expect(login.ok()).toBe(true);
  const { access_token } = await login.json();
  const headers = { Authorization: `Bearer ${access_token}` };
  try {
    const queued = await request.post("/api/v1/search-jobs", { headers, data: { query: "DEMO resumable search" } });
    expect(queued.status()).toBe(202);
    const jobPath = queued.headers().location;

    await page.goto("/");
    await page.getByLabel("電子郵件").fill(credentials.email);
    await page.getByLabel("密碼（至少 12 字元）").fill(credentials.password);
    await page.getByRole("button", { name: "登入", exact: true }).click();
    await expect(page.getByText(`目前帳號 · ${credentials.email}`)).toBeVisible();
    const idea = page.getByLabel(/^構想描述（最多 /);
    await expect(idea).toHaveValue("");

    const reopen = page.getByRole("button", { name: "查看背景搜尋", exact: true });
    await expect(reopen).toBeVisible();
    await reopen.click();
    await expect(page.getByText("先前的背景搜尋等待中…")).toBeVisible();
    await page.getByRole("button", { name: "取消背景搜尋", exact: true }).click();
    await expect(page.getByText("已取消背景搜尋。")).toBeVisible();
    const status = await (await request.get(jobPath, { headers })).json();
    expect(status.status).toBe("cancelled");
    expect(status.run_id).toBeNull();
    await expect(idea).toHaveValue("");

    await expect(reopen).toBeVisible();
    await reopen.click();
    await expect(page.getByText("目前沒有背景搜尋。")).toBeVisible();
    expect(await (await request.get("/api/v1/search-runs", { headers })).json()).toEqual([]);
  } finally {
    const removed = await request.delete("/api/v1/me", { headers, data: { password: credentials.password } });
    expect(removed.status()).toBe(204);
  }
});
