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
  invitationHash,
  saveWorkspaceCopy,
  registrationCapacityReached,
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
// These are plain persistence fixtures, not simulated WebAuthn credentials or sessions.
function save(database, user, key, state, file) {
  const candidate = database.users[user]
    ? database
    : {
        ...database,
        users: {
          ...database.users,
          [user]: { id: user, name: "Storage fixture" },
        },
      };
  return saveWorkspaceCopy(candidate, user, key, state, file);
}
test("reserved identity budgets preserve a new user's save when others fill their allocations", (t) => {
  const file = fixture(t);
  let database = empty();
  const first = { draft: "x".repeat(180000) };
  const second = { draft: "x".repeat(80000) };
  for (let user = 0; user < workspaceStorageLimits.users - 1; user++) {
    database = save(database, "user-" + user, "content", first, file);
    database = save(database, "user-" + user, "voice", second, file);
  }
  const prior = readFileSync(file, "utf8");
  assert.throws(
    () => save(database, "user-0", "film", { draft: "x".repeat(4000) }, file),
    /storage is full/,
  );
  assert.equal(readFileSync(file, "utf8"), prior);
  database = save(database, "last", "content", first, file);
  database = save(database, "last", "voice", second, file);
  database = save(database, "last", "content", first, file);
  assert.throws(
    () => save(database, "seventeenth", "content", {}, file),
    /at capacity/,
  );
  database = save(database, "user-0", "content", { draft: "smaller" }, file);
  database = save(database, "user-0", "film", { draft: "recovered" }, file);
  assert.equal(database.workspaces["last:content"].draft, first.draft);
  assert.ok(
    Buffer.byteLength(readFileSync(file, "utf8")) <
      workspaceStorageLimits.storeBytes,
  );
  assert.throws(
    () =>
      save(database, "user-0", "toolkit", { draft: "😀".repeat(50000) }, file),
    /storage is full/,
  );
});
test("object-node capacity is reserved per admitted identity and smaller replacements recover", (t) => {
  const file = fixture(t);
  let database = empty();
  const state = { items: Array.from({ length: 5997 }, () => ({})) };
  for (let i = 0; i < 15; i++)
    database = save(database, "user-" + i, "content", state, file);
  const prior = readFileSync(file, "utf8");
  assert.throws(
    () => save(database, "user-0", "voice", { items: [{}] }, file),
    /storage is full/,
  );
  assert.equal(readFileSync(file, "utf8"), prior);
  database = save(database, "last", "content", state, file);
  database = save(database, "user-0", "content", { items: [] }, file);
  database = save(database, "user-0", "voice", { items: [{}] }, file);
  assert.equal(database.workspaces["last:content"].items.length, 5997);
});
test("access capacity reserves four bounded credentials per admitted identity", (t) => {
  const file = fixture(t),
    database = empty();
  for (let i = 0; i < 16; i++)
    database.users["user-" + i] = { id: "user-" + i };
  for (let user = 0; user < 15; user++)
    for (let key = 0; key < 4; key++)
      database.credentials[user + "-" + key] = {
        id: user + "-" + key,
        user: "user-" + user,
        publicKey: "x".repeat(7900),
      };
  assert.equal(registrationCapacityReached(database, undefined), true);
  assert.equal(registrationCapacityReached(database, "user-0"), true);
  assert.equal(registrationCapacityReached(database, "user-15"), false);
  for (let key = 0; key < 4; key++)
    database.credentials["last-" + key] = {
      id: "last-" + key,
      user: "user-15",
      publicKey: "x".repeat(7900),
    };
  assert.equal(registrationCapacityReached(database, "user-15"), true);
  saveWorkspaceCopy(
    database,
    "user-15",
    "content",
    { draft: "still works" },
    file,
  );
  database.credentials["one-extra"] = { user: "user-0", publicKey: "x" };
  assert.throws(
    () => saveWorkspaceCopy(database, "user-0", "content", {}, file),
    /at capacity/,
  );
});
test("orphaned state and unknown slots fail closed without rewriting the store", (t) => {
  const file = fixture(t);
  const database = save(
    empty(),
    "first",
    "content",
    { draft: "preserved" },
    file,
  );
  const prior = readFileSync(file, "utf8");
  for (const candidate of [
    {
      ...database,
      workspaces: { ...database.workspaces, "unknown:content": {} },
    },
    {
      ...database,
      workspaces: { ...database.workspaces, "first:unknown": {} },
    },
    { ...database, credentials: { unknown: { user: "unknown" } } },
    { ...database, credentials: { unknown: { user: "toString" } } },
  ]) {
    assert.throws(
      () => saveWorkspaceCopy(candidate, "first", "content", {}, file),
      /Unrecognized workspace owner/,
    );
    writeFileSync(file, JSON.stringify(candidate));
    const invalid = readFileSync(file, "utf8");
    assert.throws(
      () => createDemoServer({ storePath: file }),
      /Unrecognized workspace owner/,
    );
    assert.equal(readFileSync(file, "utf8"), invalid);
    writeFileSync(file, prior);
  }
});
test("credential metadata is bounded and untrusted transports retain only recognized unique values", (t) => {
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
  const database = empty();
  database.users.first = { id: "first" };
  database.credentials.bad = { user: "first", publicKey: "x".repeat(9000) };
  assert.throws(
    () => saveWorkspaceCopy(database, "first", "content", {}, file),
    /at capacity/,
  );
  assert.equal(existsSync(file), false);
  delete database.credentials.bad;
  database.users.first.name = "x".repeat(600);
  assert.throws(
    () => saveWorkspaceCopy(database, "first", "content", {}, file),
    /at capacity/,
  );
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
  let database = save(
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
    () => save(database, "attacker-test", "content", attack, file),
    /too complex/,
  );
  assert.equal(database.workspaces["attacker-test:content"], undefined);
  assert.equal(readFileSync(file, "utf8"), prior);
  database = save(
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
  let database = save(
    empty(),
    "first-user",
    "content",
    { draft: "original" },
    file,
  );
  const prior = readFileSync(file, "utf8");
  mkdirSync(file + ".tmp");
  assert.throws(() =>
    save(database, "first-user", "content", { draft: "must not commit" }, file),
  );
  assert.equal(database.workspaces["first-user:content"].draft, "original");
  assert.equal(readFileSync(file, "utf8"), prior);
  rmdirSync(file + ".tmp");
  database = save(
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
    registrationInvites: [
      invitationHash(Buffer.alloc(32, 8).toString("base64url")),
    ],
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
  const registration = await post(
    "/auth/register/options",
    JSON.stringify({ invite: Buffer.alloc(32, 8).toString("base64url") }),
  );
  assert.equal(registration.status, 200);
  assert.equal(registration.body.rp.id, "workspace.example.test");
});
