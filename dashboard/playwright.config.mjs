import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  testMatch: "**/*.spec.mjs",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 20_000,
  expect: {
    timeout: 5_000,
  },
  reporter: process.env.CI ? "line" : "list",
  use: {
    baseURL: "http://127.0.0.1:3003",
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  webServer: {
    command: "npm run build && npm run start -- --port 3003",
    url: "http://127.0.0.1:3003",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
