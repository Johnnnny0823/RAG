import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PATENTSCOPE_E2E_URL;
if (!baseURL || !/^http:\/\/127\.0\.0\.1:\d+$/.test(baseURL)) {
  throw new Error("Set PATENTSCOPE_E2E_URL to the isolated Compose web origin (http://127.0.0.1:PORT).");
}

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: { baseURL, trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
});
