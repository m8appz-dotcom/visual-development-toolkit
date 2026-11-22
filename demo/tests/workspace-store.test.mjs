import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import path from "node:path";
import { tmpdir } from "node:os";
import {
  mkdtempSync,
  readFileSync,
  writeFileSync,
  mkdirSync,
  rmdirSync,
  rmSync,
  existsSync,
} from "node:fs";
import {
  createDemoServer,
  saveWorkspaceCopy,
  storedCredential,
  workspaceStorageLimits,
} from "../server.mjs";

const nested = () => JSON.parse('{"x":'.repeat(5000) + "0" + "}".repeat(5000));
function fixture(t) {
  const folder = mkdtempSync(path.join(tmpdir(), "workspace-transaction-"));
  t.after(() => {
    assert.ok(
      path
        .resolve(folder)
        .startsWith(
          path.resolve(tmpdir()) + path.sep + "workspace-transaction-",
        ),
    );
    rmSync(folder, { recursive: true });
  });
  return path.join(folder, "workspaces.json");
}
const empty = () => ({
  version: 1,
  users: {},
  credentials: {},
  workspaces: {},
});
test("workspace byte budgets reject aggregate growth and preserve replacement and recovery", (t) => {
  const file = fixture(t);
  let database = empty();
  const state = { draft: "😀".repeat(47000) };
  database = saveWorkspaceCopy(database, "first", "content", state, file);
  database = saveWorkspaceCopy(database, "first", "voice", state, file);
  const prior = readFileSync(file, "utf8");
  assert.throws(
    () => saveWorkspaceCopy(database, "first", "film", state, file),
    /storage is full/,
  );
  assert.equal(readFileSync(file, "utf8"), prior);
  assert.equal(database.workspaces["first:film"], undefined);
  // Replacement at the per-user limit must not double-count the previous slot.
  database = saveWorkspaceCopy(database, "first", "content", state, file);
  for (let user = 0; user < 19; user++)
    database = saveWorkspaceCopy(
      database,
      "other-" + user,
      "content",
      state,
      file,
    );
  database = saveWorkspaceCopy(database, "last", "content", state, file);
  const full = readFileSync(file, "utf8");
  assert.throws(
    () => saveWorkspaceCopy(database, "overflow", "content", state, file),
    /storage is full/,
  );
  assert.equal(readFileSync(file, "utf8"), full);
  database = saveWorkspaceCopy(
    database,
    "first",
    "content",
    { draft: "smaller" },
    file,
  );
  database = saveWorkspaceCopy(database, "overflow", "content", state, file);
  assert.equal(database.workspaces["first:voice"].draft, state.draft);
  assert.ok(
    Buffer.byteLength(readFileSync(file, "utf8")) <
      workspaceStorageLimits.storeBytes,
  );
  assert.throws(
    () =>
      saveWorkspaceCopy(
        database,
        "large",
        "content",
        { draft: "😀".repeat(50000) },
        file,
      ),
    /storage is full/,
  );
});
test("cumulative object-node budgets bound many small saved objects independently of bytes", (t) => {
  const file = fixture(t);
  let database = empty();
  const state = { items: Array.from({ length: 19000 }, () => ({})) };
  database = saveWorkspaceCopy(database, "first", "content", state, file);
  assert.throws(
    () => saveWorkspaceCopy(database, "first", "voice", state, file),
    /storage is full/,
  );
  for (let i = 1; i < 5; i++)
    database = saveWorkspaceCopy(database, "user-" + i, "content", state, file);
  const prior = readFileSync(file, "utf8");
  assert.throws(
    () => saveWorkspaceCopy(database, "overflow", "content", state, file),
    /storage is full/,
  );
  assert.equal(readFileSync(file, "utf8"), prior);
  database = saveWorkspaceCopy(
    database,
    "first",
    "content",
    { items: [] },
    file,
  );
  database = saveWorkspaceCopy(database, "overflow", "content", state, file);
  assert.equal(database.workspaces["user-1:content"].items.length, 19000);
});
test("credential metadata is bounded and untrusted transports are reduced to known unique values", (t) => {
  const file = fixture(t);
  const credential = storedCredential(
    {
      id: "test",
      publicKey: new Uint8Array([1, 2]),
      counter: 0,
      transports: ["internal", "internal", "hybrid", "x".repeat(190000)],
    },
    "first",
  );
  assert.deepEqual(credential.transports, ["internal", "hybrid"]);
  assert.ok(Buffer.byteLength(JSON.stringify(credential)) < 200);
  const database = empty();
  database.credentials.bad = { publicKey: "x".repeat(9000) };
  assert.throws(
    () => saveWorkspaceCopy(database, "first", "content", {}, file),
    /at capacity/,
  );
  assert.equal(existsSync(file), false);
  delete database.credentials.bad;
  for (let i = 0; i < 160; i++)
    database.credentials[i] = { publicKey: "x".repeat(7000) };
  assert.throws(
    () => saveWorkspaceCopy(database, "first", "content", {}, file),
    /at capacity/,
  );
  assert.equal(existsSync(file), false);
});
test("oversized existing stores fail closed without replacing their original data", (t) => {
  const file = fixture(t);
  const oversized = " ".repeat(workspaceStorageLimits.storeBytes + 1);
  writeFileSync(file, oversized);
  assert.throws(() => createDemoServer({ storePath: file }), /Preserve it/);
  assert.equal(readFileSync(file, "utf8"), oversized);
});
test("a sub-200KB deeply nested workspace cannot poison another user's saved state", (t) => {
  const file = fixture(t);
  let database = saveWorkspaceCopy(
    empty(),
    "other-user",
    "content",
    { draft: "preserve this work" },
    file,
  );
  const prior = readFileSync(file, "utf8");
  const attack = nested();
  // This input is only about30KB, well below the old body-size-only protection.
  assert.ok(
    Buffer.byteLength('{"x":'.repeat(5000) + "0" + "}".repeat(5000)) < 200000,
  );
  assert.throws(
    () => saveWorkspaceCopy(database, "attacker-test", "content", attack, file),
    /too complex/,
  );
  assert.equal(database.workspaces["attacker-test:content"], undefined);
  assert.equal(readFileSync(file, "utf8"), prior);
  database = saveWorkspaceCopy(
    database,
    "another-user",
    "content",
    { draft: "normal next save" },
    file,
  );
  assert.equal(
    database.workspaces["other-user:content"].draft,
    "preserve this work",
  );
  assert.equal(
    JSON.parse(readFileSync(file, "utf8")).workspaces["another-user:content"]
      .draft,
    "normal next save",
  );
});
test("a failed atomic write preserves memory and disk and a later save recovers", (t) => {
  const file = fixture(t);
  let database = saveWorkspaceCopy(
    empty(),
    "first-user",
    "content",
    { draft: "original" },
    file,
  );
  const prior = readFileSync(file, "utf8");
  mkdirSync(file + ".tmp");
  assert.throws(() =>
    saveWorkspaceCopy(
      database,
      "first-user",
      "content",
      { draft: "must not commit" },
      file,
    ),
  );
  assert.equal(database.workspaces["first-user:content"].draft, "original");
  assert.equal(readFileSync(file, "utf8"), prior);
  rmdirSync(file + ".tmp");
  database = saveWorkspaceCopy(
    database,
    "first-user",
    "content",
    { draft: "recovered" },
    file,
  );
  assert.equal(database.workspaces["first-user:content"].draft, "recovered");
});
test("hosted HTTP rejects deeply nested auth and engine input while access remains healthy", async (t) => {
  const file = fixture(t),
    origin = "https://workspace.example.test";
  let executions = 0;
  const server = createDemoServer({
    hosted: true,
    origin,
    storePath: file,
    engine: {
      name: "Test only",
      actions: ["plan"],
      status: async () => ({ available: true }),
      run: async () => {
        executions++;
        return { result: {}, files: [] };
      },
    },
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const post = (route, value) =>
    new Promise((resolve, reject) => {
      const req = http.request(
        {
          host: "127.0.0.1",
          port: server.address().port,
          path: route,
          method: "POST",
          headers: {
            Host: "workspace.example.test",
            Origin: origin,
            "Content-Type": "application/json",
          },
        },
        (res) => {
          let text = "";
          res.on("data", (b) => (text += b));
          res.on("end", () =>
            resolve({ status: res.statusCode, body: JSON.parse(text) }),
          );
        },
      );
      req.on("error", reject);
      req.end(value);
    });
  const attack = '{"x":'.repeat(5000) + "0" + "}".repeat(5000);
  assert.equal(
    (
      await post(
        "/auth/workspace/save",
        '{"key":"content","state":' + attack + "}",
      )
    ).status,
    400,
  );
  assert.equal(
    (await post("/engine/run", '{"action":"plan","data":' + attack + "}"))
      .status,
    400,
  );
  assert.equal(executions, 0);
  assert.equal(existsSync(file), false);
  assert.equal((await post("/auth/login/options", "{}")).status, 200);
  const registration = await post("/auth/register/options", "{}");
  assert.equal(registration.status, 200);
  assert.equal(registration.body.rp.id, "workspace.example.test");
});
