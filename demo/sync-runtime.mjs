import { readFileSync, writeFileSync, realpathSync, lstatSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const root = path.dirname(fileURLToPath(import.meta.url));
const allowed = new Set([
  "server.mjs",
  "engine-gateway.mjs",
  "process.mjs",
  "public/core.js",
  "public/engine-client.js",
]);
function checkedFile(base, name, allowMissing = false) {
  if (!allowed.has(name)) throw Error("Unexpected runtime member.");
  const resolved = path.join(base, name);
  const boundary = realpathSync(base);
  const parent = realpathSync(path.dirname(resolved));
  if (parent !== boundary && !parent.startsWith(boundary + path.sep))
    throw Error("Runtime member escapes its source.");
  const info = lstatSync(resolved, { throwIfNoEntry: false });
  if (info?.isSymbolicLink() || (info && !info.isFile()))
    throw Error("Runtime member is not an original regular file.");
  if (!info && !allowMissing) throw Error("Missing runtime member: " + name);
  return resolved;
}
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
export function verifyRuntime(base = root, source = null) {
  const lock = JSON.parse(
    readFileSync(path.join(base, "runtime-lock.json"), "utf8"),
  );
  if (
    !["1.0.0", "1.1.0", "1.1.1", "1.1.2", "1.1.3", "1.1.4"].includes(
      lock.version,
    ) ||
    lock.upstream.repository !== "m8appz-dotcom/visual-development-toolkit" ||
    !/^[a-f0-9]{40}$/.test(lock.upstream.commit)
  )
    throw Error("Unsupported runtime source.");
  if (Object.keys(lock.files).length !== allowed.size)
    throw Error("Incomplete runtime lock.");
  const pending = [];
  for (const [name, expected] of Object.entries(lock.files)) {
    if (!/^[a-f0-9]{64}$/.test(expected))
      throw Error("Invalid runtime checksum.");
    const target = checkedFile(base, name, Boolean(source));
    const bytes = readFileSync(source ? checkedFile(source, name) : target);
    if (digest(bytes) !== expected)
      throw Error("Runtime checksum mismatch: " + name);
    pending.push([target, bytes]);
  }
  // Verify every source and destination before writing any runtime member.
  if (source)
    for (const [target, bytes] of pending) writeFileSync(target, bytes);
  return pending.length;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const option = process.argv[2] || "--check";
  if (option !== "--check" && option !== "--from")
    throw Error("Use --check or --from <trusted-demo-directory>.");
  if (option === "--from" && !process.argv[3])
    throw Error("A local canonical demo directory is required.");
  console.log(
    "Verified " +
      verifyRuntime(
        root,
        option === "--from" ? path.resolve(process.argv[3]) : null,
      ) +
      " pinned runtime files.",
  );
}
