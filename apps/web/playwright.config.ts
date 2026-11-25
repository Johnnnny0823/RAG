import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PATENTSCOPE_E2E_URL;
if (!baseURL || !/^http:\/\/127\.0\.0\.1:\d+$/.test(baseURL)) {
  throw new Error("Set PATENTSCOPE_E2E_URL to the isolated Compose web origin (http://127.0.0.1:PORT).");
}

const suite = process.env.PATENTSCOPE_E2E_TIPO;
const officialTag = suite === "versions" ? /@versions/ : suite === "dates" ? /@gazette/ : suite === "1" ? /@tipo/ : undefined;

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  grep: officialTag,
  grepInvert: officialTag ? undefined : /@tipo|@versions|@gazette/,
  reporter: [["list"], ["html", { open: "never" }]],
  use: { baseURL, trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "tablet-chromium", use: { ...devices["iPad (gen 7)"], browserName: "chromium" } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
    ...(process.env.PATENTSCOPE_E2E_CROSS_BROWSER === "1"
      ? [
        { name: "desktop-firefox", use: { ...devices["Desktop Firefox"] } },
        { name: "desktop-webkit", use: { ...devices["Desktop Safari"] } },
      ]
      : []),
  ],
});
