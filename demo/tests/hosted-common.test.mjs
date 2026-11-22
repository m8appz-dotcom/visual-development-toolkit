import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import path from "node:path";
import { tmpdir } from "node:os";
import { mkdtempSync, rmSync, mkdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { createDemoServer } from "../server.mjs";

const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../public",
);
const origin = "https://content.example.test";
test("hosted deployment rejects insecure origins, capture and exposed storage", () => {
  for (const invalid of [
    "http://content.example.test",
    "https://localhost",
    "https://127.0.0.1",
    origin + "/path",
    "https://user@content.example.test",
    origin + "/",
    "https://content.example.test:8443",
  ])
    assert.throws(() => createDemoServer({ origin: invalid, hosted: true }));
  assert.throws(() =>
    createDemoServer({ origin, hosted: true, enableCapture: true }),
  );
  assert.throws(() =>
    createDemoServer({
      origin,
      hosted: true,
      root,
      storePath: path.join(root, "state.json"),
    }),
  );
  assert.throws(() => createDemoServer({ origin }));
});
