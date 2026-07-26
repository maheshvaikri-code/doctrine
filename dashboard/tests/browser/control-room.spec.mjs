import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const responseHeaders = {
  "Access-Control-Allow-Origin": "http://127.0.0.1:3003",
  "Content-Type": "application/json",
};

const passedGates = [
  {
    key: "lint",
    label: "Doctrine corpus",
    status: "passed",
    evidence: "Passed",
  },
  {
    key: "ruff",
    label: "Python quality",
    status: "passed",
    evidence: "Passed",
  },
  {
    key: "tests",
    label: "Tooling tests",
    status: "passed",
    evidence: "186 tests passed",
  },
  {
    key: "state",
    label: "State chain",
    status: "passed",
    evidence: "Passed",
  },
];

const liveSnapshot = {
  apiVersion: "1",
  generatedAt: "2026-07-25T23:55:28.446609Z",
  partialReasons: [],
  repository: {
    connected: true,
    name: "doctrineos",
    version: "0.6.46",
    branch: "main",
    commit: "54c8dbffc6f1",
    isDirty: false,
    trackedFiles: 420,
  },
  activation: {
    status: "healthy",
    passing: 9,
    total: 9,
    findings: [],
  },
  statePlane: {
    status: "healthy",
    checkpointSeq: 26,
    checkpointCommit: "fe66cecfa272",
    checkpoints: 27,
    unresolvedEffects: 0,
    role: "qa-engineer",
    phase: "g5",
  },
  verification: {
    id: "browser-fixture",
    status: "passed",
    commit: "54c8dbffc6f1",
    startedAt: "2026-07-25T23:55:28.446609Z",
    finishedAt: "2026-07-25T23:56:15.000000Z",
    exitCode: 0,
    testCount: 186,
    summary: "4 Doctrine gates passed.",
    gates: passedGates,
  },
  evidence: {
    reviews: 7,
    qaReports: 6,
    adrs: 8,
    plans: 9,
    goldRecords: 0,
    trend: {
      "7D": [1, 2, 3, 2, 4, 3, 5],
      "30D": [1, 2, 2, 3, 4, 3, 5, 4, 6, 5],
      "90D": [2, 3, 4, 5, 6, 5, 7, 6, 8, 9],
    },
    activity: [
      {
        commit: "54c8dbf",
        occurredAt: "2026-07-25T23:52:14Z",
        title: "docs(dashboard): close hosted CI evidence",
      },
    ],
  },
  release: {
    currentVersion: "0.6.46",
    latestTag: "v0.6.17",
    commitsAhead: 31,
    status: "ahead",
  },
};

function snapshot(overrides = {}) {
  return {
    ...structuredClone(liveSnapshot),
    ...overrides,
  };
}

async function mockSnapshot(page, value, delayMs = 0) {
  await page.route("**/api/v1/snapshot", async (route) => {
    if (delayMs) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    await route.fulfill({
      status: 200,
      headers: responseHeaders,
      body: JSON.stringify(value),
    });
  });
}

async function openLiveControlRoom(page) {
  await mockSnapshot(page, snapshot());
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Confidence has a control plane." }),
  ).toBeVisible();
}

test("renders live evidence and passes automated WCAG A/AA checks", async ({
  page,
}) => {
  await openLiveControlRoom(page);

  await expect(page.getByText("doctrineos · Tree clean")).toBeVisible();
  await expect(page.getByRole("table", { name: "Gate status" })).toBeVisible();
  await expect(page.getByText("186 tests passed")).toBeVisible();
  await expect(page.getByText(/prototype/i)).toHaveCount(0);
  await expect(page.locator(".evidence-panel")).toHaveCSS("opacity", "1");

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("keeps keyboard focus inside the command dialog and restores it", async ({
  page,
}) => {
  await openLiveControlRoom(page);
  const trigger = page.getByRole("button", { name: "Search or run" });

  await trigger.focus();
  await page.keyboard.press("/");
  const dialog = page.getByRole("dialog", { name: "Run a Doctrine action" });
  const close = dialog.getByRole("button", { name: "Close command palette" });
  const run = dialog.getByRole("button", { name: /^Run verification/ });
  const release = dialog.getByRole("button", { name: /^Inspect release identity/ });
  await expect(dialog).toBeVisible();
  await expect(page.locator(".command-palette")).toHaveCSS("opacity", "1");
  await expect(run).toBeFocused();

  await page.keyboard.press("Shift+Tab");
  await expect(close).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(release).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();

  const dialogResults = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(dialogResults.violations).toEqual([]);

  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
});

test("supports skip navigation and narrow keyboard navigation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await openLiveControlRoom(page);

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to dashboard" });
  await expect(skipLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  const menu = page.getByRole("button", { name: "Open navigation" });
  await expect(menu).toBeVisible();
  await menu.focus();
  await page.keyboard.press("Enter");
  await expect(menu).toHaveAttribute("aria-expanded", "true");
  await expect(
    page
      .getByRole("complementary")
      .getByRole("button", { name: "Close navigation" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(menu).toHaveAttribute("aria-expanded", "false");

  const motion = await page.locator(".metric-card").first().evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      media: matchMedia("(prefers-reduced-motion: reduce)").matches,
      transitionSeconds: Number.parseFloat(style.transitionDuration),
    };
  });
  expect(motion.media).toBe(true);
  expect(motion.transitionSeconds).toBeLessThanOrEqual(0.001);
});

test("renders loading then live without fabricated evidence", async ({ page }) => {
  await mockSnapshot(page, snapshot(), 800);
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Reading the repository control state." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Confidence has a control plane." }),
  ).toBeVisible();
});

test("renders exact partial evidence while preserving known fields", async ({
  page,
}) => {
  await mockSnapshot(
    page,
    snapshot({
      partialReasons: ["The latest verification belongs to another commit."],
    }),
  );
  await page.goto("/");

  await expect(page.getByRole("status")).toContainText("Partial evidence.");
  await expect(page.getByRole("status")).toContainText(
    "The latest verification belongs to another commit.",
  );
  await expect(page.getByText("doctrineos · Tree clean")).toBeVisible();
});

test("renders the empty repository state", async ({ page }) => {
  const empty = snapshot();
  empty.repository = {
    connected: false,
    name: null,
    version: null,
    branch: null,
    commit: null,
    isDirty: false,
    trackedFiles: 0,
  };
  await mockSnapshot(page, empty);
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "The bridge is running, but this folder is not Doctrine-enabled.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Retry connection" }),
  ).toBeVisible();
});

test("renders an accessible retryable bridge error", async ({ page }) => {
  await page.route("**/api/v1/snapshot", async (route) => {
    await route.fulfill({
      status: 503,
      headers: responseHeaders,
      body: JSON.stringify({
        error: {
          code: "snapshot_failed",
          message: "Bridge fixture unavailable.",
        },
      }),
    });
  });
  await page.goto("/");

  const alert = page.getByRole("alert");
  await expect(alert).toContainText(
    "The repository control state could not be loaded.",
  );
  await expect(alert).toContainText("Bridge fixture unavailable.");
  await expect(
    page.getByRole("button", { name: "Retry connection" }),
  ).toBeVisible();
});
