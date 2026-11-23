import test from "node:test";
import assert from "node:assert/strict";
import { textPreview } from "../public/file-preview.js";

test("card text comes from the original file, preserving code and bounding size", () => {
  const source = '{\n  "project": "Source handoff",\n  "files": 6\n}\n';
  assert.deepEqual(textPreview(new TextEncoder().encode(source)), [
    "{",
    '  "project": "Source handoff",',
    '  "files": 6',
    "}",
  ]);
  const long = textPreview(
    new TextEncoder().encode(("x".repeat(200) + "\n").repeat(20)),
  );
  assert.equal(long.length, 7);
  assert.ok(long.every((line) => line.length === 100));
  assert.throws(() => textPreview(new Uint8Array([255])));
});
