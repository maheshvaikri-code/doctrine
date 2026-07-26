import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import test from "node:test";

function startProductionServer() {
  const child = spawn(
    process.execPath,
    ["scripts/start.mjs", "--hostname", "127.0.0.1", "--port", "0"],
    {
      cwd: new URL("..", import.meta.url),
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  let output = "";
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Production server did not start.\n${output}`));
    }, 15_000);

    const inspect = (chunk) => {
      output += chunk.toString();
      const match = output.match(
        /Production server running at (http:\/\/127\.0\.0\.1:\d+)/,
      );
      if (match) {
        clearTimeout(timer);
        resolve(match[1]);
      }
    };

    child.stdout.on("data", inspect);
    child.stderr.on("data", inspect);
    child.once("exit", (code) => {
      clearTimeout(timer);
      reject(
        new Error(`Production server exited with code ${code}.\n${output}`),
      );
    });
    child.once("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
  });

  return { child, ready };
}

async function stopProductionServer(child) {
  if (child.exitCode !== null) return;
  const exited = new Promise((resolve) => child.once("exit", resolve));
  child.kill();
  await Promise.race([
    exited,
    new Promise((resolve) => setTimeout(resolve, 5_000)),
  ]);
  if (child.exitCode === null) {
    child.kill("SIGKILL");
    await exited;
  }
}

test("production launcher rejects a malformed port", async () => {
  const child = spawn(
    process.execPath,
    ["scripts/start.mjs", "--port", "3011junk"],
    {
      cwd: new URL("..", import.meta.url),
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  let stderr = "";
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  const [code] = await new Promise((resolve, reject) => {
    child.once("exit", (...args) => resolve(args));
    child.once("error", reject);
  });

  assert.notEqual(code, 0);
  assert.match(stderr, /Invalid port: 3011junk/);
});

test("production server delivers every rendered CSS and JavaScript asset", async () => {
  const { child, ready } = startProductionServer();

  try {
    const baseUrl = await ready;
    const response = await fetch(`${baseUrl}/`);
    assert.equal(response.status, 200);

    const html = await response.text();
    assert.doesNotMatch(html, /url\([A-Za-z]:[\\/]/);

    const assetPaths = [
      ...new Set(
        [...html.matchAll(/(?:src|href)="(\/assets\/[^"]+)"/g)].map(
          (match) => match[1],
        ),
      ),
    ];
    assert.ok(assetPaths.some((path) => path.endsWith(".css")));
    assert.ok(assetPaths.some((path) => path.endsWith(".js")));

    for (const assetPath of assetPaths) {
      const asset = await fetch(`${baseUrl}${assetPath}`);
      assert.equal(asset.status, 200, `${assetPath} must be served`);
      const contentType = asset.headers.get("content-type") ?? "";
      assert.match(
        contentType,
        assetPath.endsWith(".css")
          ? /^text\/css\b/
          : /^application\/javascript\b/,
        `${assetPath} has the wrong content type`,
      );
      assert.ok(
        Number(asset.headers.get("content-length") ?? 0) > 0,
        `${assetPath} must not be empty`,
      );
    }
  } finally {
    await stopProductionServer(child);
  }
});
