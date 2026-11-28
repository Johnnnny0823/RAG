import { expect, test } from "@playwright/test";

test("packaged app shows an offline notice without serving cached API data @packaged", async ({ context, page }) => {
  await page.goto("/");
  await expect.poll(() => page.evaluate(() => navigator.serviceWorker.controller?.state)).toBe("activated");

  const apiPath = "/api/v1/corpus/status";
  const apiResponse = page.waitForResponse((response) => response.url() === new URL(apiPath, page.url()).href);
  const onlineStatus = await page.evaluate(async (path) => (await fetch(path)).status, apiPath);
  expect(onlineStatus).toBe(200);
  expect((await apiResponse).fromServiceWorker()).toBe(false);
  const cachedPaths = await page.evaluate(async () => {
    const keys = await caches.keys();
    const requests = await Promise.all(keys.map(async (key) => (await caches.open(key)).keys()));
    return requests.flat().map((request) => new URL(request.url).pathname);
  });
  expect(cachedPaths).toContain("/offline.html");
  expect(cachedPaths.filter((path) => path.startsWith("/api/"))).toEqual([]);

  await context.setOffline(true);
  await page.reload();
  const offlinePage = page.getByRole("heading", { name: "目前離線", exact: true });
  const offlineBanner = page.getByRole("status").filter({ hasText: "目前離線。搜尋及存取研究紀錄需要連線。" });
  await expect(offlinePage.or(offlineBanner)).toBeVisible();
  await expect(page.evaluate((path) => fetch(path).then(() => true, () => false), apiPath)).resolves.toBe(false);

  await context.setOffline(false);
  await page.goto("/");
  await expect(offlinePage.or(offlineBanner)).toHaveCount(0);
  await expect(page.evaluate(async (path) => (await fetch(path)).status, apiPath)).resolves.toBe(200);
});
