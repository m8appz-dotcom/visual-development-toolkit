import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { packageTargets, verifyFiles } from "../public/portable-package.js";

test("required source notices cannot be omitted from a partial package", () => {
  const entries = [
    { path: "source/model.glb" },
    { path: "source/LICENSE.txt", required: true },
    { path: "other.txt" },
  ];
  assert.deepEqual(
    packageTargets(entries, ["source/model.glb"]).map((x) => x.path),
    ["source/model.glb", "source/LICENSE.txt"],
  );
  assert.throws(() => packageTargets(entries, ["outside.txt"]));
  assert.throws(() => packageTargets(entries, []));
});

test("tampered source stops verification instead of producing a successful package", async () => {
  const original = new TextEncoder().encode("An unchanged original.\n");
  const entry = {
    path: "source/input.md",
    name: "input.md",
    bytes: original.length,
    sha256: createHash("sha256").update(original).digest("hex"),
  };
  const result = await verifyFiles([entry], async () => original);
  assert.deepEqual(result[0].bytes, original);
  await assert.rejects(
    verifyFiles([entry], async () => new TextEncoder().encode("Changed")),
    /changed/,
  );
  await assert.rejects(
    verifyFiles([{ ...entry, path: "../outside" }], async () => original),
    /invalid/,
  );
});
