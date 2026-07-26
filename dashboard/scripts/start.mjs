import path from "node:path";
import { parseArgs } from "node:util";

const { values } = parseArgs({
  options: {
    hostname: { type: "string", short: "H" },
    port: { type: "string", short: "p" },
  },
});

const rawPort = values.port ?? process.env.PORT ?? "3000";
const port = Number(rawPort);
const host = values.hostname ?? process.env.HOST ?? "0.0.0.0";

if (!/^\d+$/.test(rawPort) || !Number.isInteger(port) || port > 65_535) {
  throw new Error(`Invalid port: ${rawPort}`);
}
if (!host.trim()) {
  throw new Error("Hostname must not be empty.");
}

// vinext 0.0.50 stores production asset-cache keys from path.relative().
// Windows returns backslashes, while request URLs always contain slashes, so
// every built CSS/JS asset otherwise returns 404. Keep the compatibility shim
// scoped to cache construction and restore the native function immediately.
const nativeRelative = path.relative;
if (path.sep === "\\") {
  path.relative = (...args) => nativeRelative(...args).replaceAll("\\", "/");
}

try {
  const { startProdServer } = await import("vinext/server/prod-server");
  await startProdServer({
    port,
    host,
    outDir: path.resolve("dist"),
  });
} finally {
  path.relative = nativeRelative;
}
