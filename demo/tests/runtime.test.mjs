import { test } from "node:test";
import assert from "node:assert/strict";
import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  copyFileSync,
  rmSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { verifyRuntime } from "../sync-runtime.mjs";
const demo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
test("runtime restoration rejects one altered member before changing any file", () => {
  const temp = mkdtempSync(path.join(os.tmpdir(), "demo-runtime-"));
  try {
    const target = path.join(temp, "target"),
      source = path.join(temp, "source");
    const lock = JSON.parse(
      readFileSync(path.join(demo, "runtime-lock.json"), "utf8"),
    );
    for (const root of [target, source]) {
      mkdirSync(path.join(root, "public"), { recursive: true });
      copyFileSync(
        path.join(demo, "runtime-lock.json"),
        path.join(root, "runtime-lock.json"),
      );
      for (const name of Object.keys(lock.files))
        copyFileSync(path.join(demo, name), path.join(root, name));
    }
    writeFileSync(path.join(target, "server.mjs"), "retain this local repair");
    writeFileSync(path.join(source, "public/core.js"), "tampered source");
    assert.throws(() => verifyRuntime(target, source), /checksum mismatch/);
    assert.equal(
      readFileSync(path.join(target, "server.mjs"), "utf8"),
      "retain this local repair",
    );
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});
test("default workspace server denies microphone access", async () => {
  const { createDemoServer } = await import("../server.mjs");
  const server = createDemoServer({
    root: path.join(demo, "public"),
    origin: "http://localhost:0",
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const { port } = server.address();
    const response = await fetch("http://127.0.0.1:" + port + "/", {
      headers: { Host: "localhost:0" },
    });
    assert.match(response.headers.get("permissions-policy"), /microphone=\(\)/);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("a complete trusted source restores a deleted runtime member", () => {
  const temp = mkdtempSync(path.join(os.tmpdir(), "demo-runtime-"));
  try {
    const target = path.join(temp, "target"),
      source = path.join(temp, "source");
    const lock = JSON.parse(
      readFileSync(path.join(demo, "runtime-lock.json"), "utf8"),
    );
    for (const root of [target, source]) {
      mkdirSync(path.join(root, "public"), { recursive: true });
      copyFileSync(
        path.join(demo, "runtime-lock.json"),
        path.join(root, "runtime-lock.json"),
      );
      for (const name of Object.keys(lock.files))
        copyFileSync(path.join(demo, name), path.join(root, name));
    }
    rmSync(path.join(target, "public/core.js"));
    assert.equal(verifyRuntime(target, source), 5);
    assert.equal(
      readFileSync(path.join(target, "public/core.js"), "utf8"),
      readFileSync(path.join(source, "public/core.js"), "utf8"),
    );
  } finally {
    if (
      !path
        .resolve(temp)
        .startsWith(path.resolve(os.tmpdir()) + path.sep + "demo-runtime-")
    )
      throw Error("Unexpected test cleanup target");
    rmSync(temp, { recursive: true, force: true });
  }
});
