import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PATENTSCOPE_E2E_URL;
if (!baseURL || !/^http:\/\/127\.0\.0\.1:\d+$/.test(baseURL)) {
  throw new Error("Set PATENTSCOPE_E2E_URL to the isolated Compose web origin (http://127.0.0.1:PORT).");
}

const suite = process.env.PATENTSCOPE_E2E_TIPO;
const suiteTag = suite === "versions" ? /@versions/ : suite === "grant-types" ? /@grant-types/ : suite === "derived-design" ? /@derived-design/ : suite === "dates" ? /@gazette/ : suite === "loc" ? /@loc/ : suite === "events" ? /@legal-events/ : suite === "grant-events" ? /@grant-events/ : suite === "1" ? /@tipo/ : undefined;
const tag = process.env.PATENTSCOPE_E2E_DEPLOY === "1" ? /@packaged/ : suiteTag;

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  grep: tag,
  grepInvert: tag ? undefined : /@tipo|@versions|@grant-types|@derived-design|@gazette|@loc|@legal-events|@grant-events|@packaged/,
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
