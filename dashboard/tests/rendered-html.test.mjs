import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
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
  assert.match(html, /Confidence has/);
  assert.match(html, /Portfolio verification/);
  assert.match(html, /Doctrine/);
  assert.match(html, /Maple Runtime/);
  assert.match(html, /Policy Shield/);
  assert.match(html, /Trust Engine/);
  assert.match(html, /aria-label="Primary navigation"/);
  assert.match(html, /Skip to dashboard/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/i);
});

test("ships an accessible, state-complete, dependency-scoped surface", async () => {
  const [controlRoom, css, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/control-room.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  for (const state of ["live", "loading", "partial", "error", "empty"]) {
    assert.match(controlRoom, new RegExp(`value="${state}"`));
  }

  assert.match(controlRoom, /role="dialog"/);
  assert.match(controlRoom, /aria-modal="true"/);
  assert.match(controlRoom, /role="alert"/);
  assert.match(controlRoom, /aria-live="polite"/);
  assert.match(controlRoom, /window\.addEventListener\("keydown"/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(css, /button:focus-visible/);
  assert.match(layout, /title:\s*"Doctrine Control Room"/);

  assert.match(packageJson, /"motion": "12\.42\.2"/);
  assert.match(packageJson, /"lucide-react": "1\.26\.0"/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton|animejs/);

  await assert.rejects(
    access(new URL("../app/_sites-preview/SkeletonPreview.tsx", import.meta.url)),
  );
});
