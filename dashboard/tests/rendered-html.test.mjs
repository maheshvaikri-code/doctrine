import assert from "node:assert/strict";
import { access, readdir, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the Doctrine control room", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Doctrine Control Room<\/title>/i);
  assert.match(html, /Connecting to Doctrine/);
  assert.match(html, /Reading the repository control state/);
  assert.match(html, /local bridge is collecting activation/i);
  assert.match(html, /aria-label="Primary navigation"/);
  assert.match(html, /Skip to dashboard/);
  assert.doesNotMatch(
    html,
    /codex-preview|Your site is taking shape|Prototype data/i,
  );
});

test("ships an accessible, state-complete, dependency-scoped surface", async () => {
  const [controlRoom, apiClient, css, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/live-control-room.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/doctrine-api.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  for (const state of ["live", "loading", "partial", "error", "empty"]) {
    assert.match(controlRoom, new RegExp(`"${state}"`));
  }

  assert.match(controlRoom, /fetchSnapshot/);
  assert.match(controlRoom, /startVerification/);
  assert.match(controlRoom, /verification\.status === "running"/);
  assert.match(controlRoom, /setInterval/);
  assert.match(controlRoom, /AbortController/);
  assert.match(controlRoom, /role="dialog"/);
  assert.match(controlRoom, /aria-modal="true"/);
  assert.match(controlRoom, /role="alert"/);
  assert.match(controlRoom, /aria-live="polite"/);
  assert.match(controlRoom, /window\.addEventListener\("keydown"/);
  assert.doesNotMatch(controlRoom, /prototype mode|Prototype data|48 repositories/);

  assert.match(apiClient, /parseSnapshot\(value: unknown\)/);
  assert.match(apiClient, /cache: "no-store"/);
  assert.match(apiClient, /"Content-Type": "application\/json"/);
  assert.match(apiClient, /NEXT_PUBLIC_DOCTRINE_API_URL/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(css, /button:focus-visible/);
  assert.match(layout, /title:\s*"Doctrine Control Room"/);

  assert.match(packageJson, /"motion": "12\.42\.2"/);
  assert.match(packageJson, /"lucide-react": "1\.26\.0"/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton|animejs/);

  await assert.rejects(
    access(new URL("../app/_sites-preview/SkeletonPreview.tsx", import.meta.url)),
  );
  await assert.rejects(
    access(new URL("../app/control-room.tsx", import.meta.url)),
  );
});

test("source CI enforces every dashboard gate without changing consumer CI", async () => {
  const [workflow, packageJson, installer] = await Promise.all([
    readFile(
      new URL("../../.github/workflows/dashboard.yml", import.meta.url),
      "utf8",
    ),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(
      new URL("../../tools/doctrine_install.py", import.meta.url),
      "utf8",
    ),
  ]);
  const manifest = JSON.parse(packageJson);
  const scripts = manifest.scripts;

  assert.equal(manifest.packageManager, "npm@10.9.2");
  assert.equal(manifest.scripts["test:e2e"], "playwright test");
  assert.equal(scripts.typecheck, "tsc --noEmit --incremental false");
  assert.equal(scripts.audit, "npm audit --audit-level=moderate");
  assert.match(workflow, /permissions:\s*\n\s+contents: read/);
  assert.match(
    workflow,
    /actions\/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1/,
  );
  assert.match(
    workflow,
    /actions\/setup-node@820762786026740c76f36085b0efc47a31fe5020/,
  );
  assert.match(workflow, /node-version: "22\.13\.0"/);
  assert.match(workflow, /fail-fast: false/);
  assert.match(workflow, /os: \[ubuntu-latest, windows-latest\]/);
  assert.match(workflow, /runs-on: \$\{\{ matrix\.os \}\}/);
  assert.match(workflow, /cache-dependency-path: dashboard\/package-lock\.json/);
  assert.match(workflow, /working-directory: dashboard/);
  assert.match(workflow, /npx playwright install --with-deps chromium/);
  assert.match(workflow, /npm run test:e2e/);

  let previousIndex = -1;
  for (const command of [
    "npm ci",
    "npm run lint",
    "npm run typecheck",
    "npm test",
    "npm run audit",
  ]) {
    const commandIndex = workflow.indexOf(`run: ${command}`);
    assert.ok(commandIndex > previousIndex, `${command} is missing or out of order`);
    previousIndex = commandIndex;
  }

  assert.doesNotMatch(installer, /workflows[" /\\]+dashboard\.yml/);

  const workflowDirectory = new URL("../../.github/workflows/", import.meta.url);
  const workflowFiles = (await readdir(workflowDirectory)).filter((file) =>
    file.endsWith(".yml"),
  );
  for (const file of workflowFiles) {
    const source = await readFile(new URL(file, workflowDirectory), "utf8");
    for (const match of source.matchAll(/uses:\s*[\w-]+\/[\w-]+@([^\s#]+)/g)) {
      assert.match(
        match[1],
        /^[0-9a-f]{40}$/,
        `${file} contains an unpinned action reference: ${match[0]}`,
      );
    }
  }
});
