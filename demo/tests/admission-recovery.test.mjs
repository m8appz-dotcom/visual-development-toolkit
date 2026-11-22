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
  existsSync,
  rmSync,
} from "node:fs";
import {
  createDemoServer,
  loadWorkspaceStore,
  persistWorkspaceCandidate,
  saveWorkspaceCopy,
  invitationHash,
  requireInvitation,
  commitInvitedRegistration,
  registrationCapacityReached,
} from "../server.mjs";

// All identities/credentials here are plain storage fixtures, not authenticator simulations.
const empty = () => ({
  version: 1,
  users: {},
  credentials: {},
  workspaces: {},
});
const code = Buffer.alloc(32, 7).toString("base64url");
function fixture(t) {
  const dir = mkdtempSync(path.join(tmpdir(), "admission-recovery-"));
  t.after(() => {
    assert.ok(
      path
        .resolve(dir)
        .startsWith(path.resolve(tmpdir()) + path.sep + "admission-recovery-"),
    );
    rmSync(dir, { recursive: true });
  });
  return path.join(dir, "workspaces.json");
}
test("an invitation is consumed atomically with one account and survives restart", (t) => {
  const file = fixture(t),
    allowed = new Set([invitationHash(code)]),
    hash = invitationHash(code);
  let database = empty();
  const record = { id: "first" },
    credential = {
      id: "fixture-key",
      user: "first",
      publicKey: "fixture",
      counter: 0,
    };
  assert.throws(
    () => requireInvitation(database, allowed, invitationHash("invalid")),
    /Invitation required/,
  );
  mkdirSync(file + ".tmp");
  assert.throws(() =>
    commitInvitedRegistration(
      database,
      "first",
      record,
      credential,
      hash,
      allowed,
      file,
    ),
  );
  assert.equal(existsSync(file), false);
  assert.deepEqual(database.users, {});
  requireInvitation(database, allowed, hash);
  rmdirSync(file + ".tmp");
  database = commitInvitedRegistration(
    database,
    "first",
    record,
    credential,
    hash,
    allowed,
    file,
  );
  assert.deepEqual(database.usedInvites, [hash]);
  assert.equal(readFileSync(file, "utf8").includes(code), false);
  assert.throws(
    () =>
      commitInvitedRegistration(
        database,
        "second",
        { id: "second" },
        { ...credential, id: "other", user: "second" },
        hash,
        allowed,
        file,
      ),
    /Invitation required/,
  );
  const reloaded = loadWorkspaceStore(file).database;
  assert.throws(
    () => requireInvitation(reloaded, allowed, hash),
    /Invitation required/,
  );
  assert.deepEqual(Object.keys(reloaded.users), ["first"]);
});
test("previously valid account, workspace and credential allocations load without a rewrite", (t) => {
  const file = fixture(t);
  for (const kind of ["accounts", "workspace", "credentials"]) {
    const database = empty();
    database.users.first = { id: "first" };
    database.credentials.key = {
      id: "key",
      user: "first",
      publicKey: "fixture",
      counter: 0,
    };
    if (kind === "accounts")
      for (let i = 0; i < 16; i++)
        database.users["old-" + i] = { id: "old-" + i };
    if (kind === "workspace")
      for (const slot of ["content", "voice"])
        database.workspaces["first:" + slot] = { draft: "x".repeat(153000) };
    if (kind === "credentials")
      for (let i = 0; i < 4; i++)
        database.credentials["key-" + i] = {
          id: "key-" + i,
          user: "first",
          publicKey: "fixture",
          counter: 0,
        };
    const original = JSON.stringify(database);
    writeFileSync(file, original);
    const loaded = loadWorkspaceStore(file);
    assert.ok(loaded.legacy, kind);
    assert.equal(readFileSync(file, "utf8"), original);
    createDemoServer({ storePath: file });
    assert.equal(
      registrationCapacityReached(loaded.database, "first", loaded.legacy),
      true,
    );
    const updated = {
      ...loaded.database,
      credentials: {
        ...loaded.database.credentials,
        key: { ...loaded.database.credentials.key, counter: 10 },
      },
    };
    const saved = persistWorkspaceCandidate(file, updated, loaded.legacy);
    assert.equal(saved.credentials.key.counter, 10);
    assert.deepEqual(saved.workspaces, database.workspaces);
  }
});
test("legacy shrink preserves recovery mode across restart and rejects new identities", (t) => {
  const file = fixture(t),
    database = empty();
  database.users.first = { id: "first" };
  database.workspaces["first:content"] = { draft: "x".repeat(153000) };
  database.workspaces["first:voice"] = { draft: "x".repeat(153000) };
  writeFileSync(file, JSON.stringify(database));
  let loaded = loadWorkspaceStore(file);
  let saved = saveWorkspaceCopy(
    loaded.database,
    "first",
    "content",
    { draft: "small" },
    file,
    loaded.legacy,
  );
  saved = saveWorkspaceCopy(
    saved,
    "first",
    "voice",
    { draft: "small" },
    file,
    loaded.legacy,
  );
  loaded = loadWorkspaceStore(file);
  assert.ok(loaded.legacy);
  assert.equal(
    registrationCapacityReached(loaded.database, undefined, loaded.legacy),
    true,
  );
  assert.throws(
    () =>
      persistWorkspaceCandidate(
        file,
        { ...saved, users: { ...saved.users, new: { id: "new" } } },
        loaded.legacy,
      ),
    /Existing workspace access is preserved/,
  );
  assert.equal(loaded.database.workspaces["first:voice"].draft, "small");
});
test("credential counters retain reserved growth at the record and legacy metadata limits", (t) => {
  const file = fixture(t);
  let database = empty();
  database.users.first = { id: "first" };
  const size = (key, value) =>
    Buffer.byteLength(JSON.stringify(key)) +
    Buffer.byteLength(JSON.stringify(value)) +
    2;
  const key = "key",
    record = { id: key, user: "first", publicKey: "", counter: 4294967295 };
  record.publicKey = "x".repeat(8192 - size(key, record));
  record.counter = 9;
  database.credentials[key] = record;
  database = persistWorkspaceCandidate(file, database);
  database = persistWorkspaceCandidate(file, {
    ...database,
    credentials: { key: { ...record, counter: 10 } },
  });
  assert.equal(database.credentials.key.counter, 10);
  const legacy = empty();
  legacy.users.first = { id: "first" };
  for (let i = 0; i < 1000; i++) {
    const id = "key-" + i,
      c = { id, user: "first", publicKey: "", counter: 9 };
    c.publicKey = "x".repeat(1048 - size(id, c));
    legacy.credentials[id] = c;
  }
  writeFileSync(file, JSON.stringify(legacy));
  const loaded = loadWorkspaceStore(file);
  assert.ok(loaded.legacy);
  const saved = persistWorkspaceCandidate(
    file,
    {
      ...loaded.database,
      credentials: {
        ...loaded.database.credentials,
        "key-0": { ...loaded.database.credentials["key-0"], counter: 10 },
      },
    },
    loaded.legacy,
  );
  assert.equal(saved.credentials["key-0"].counter, 10);
  assert.equal(Object.keys(saved.credentials).length, 1000);
});
test("hosted enrollment refuses absent invitations without allocating an account or challenge", async (t) => {
  const file = fixture(t),
    origin = "https://admission.example.test";
  const server = createDemoServer({
    hosted: true,
    origin,
    storePath: file,
    registrationInvites: [invitationHash(code)],
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const request = (route, value) =>
    new Promise((resolve, reject) => {
      const req = http.request(
        {
          host: "127.0.0.1",
          port: server.address().port,
          path: route,
          method: value === undefined ? "GET" : "POST",
          headers: {
            Host: "admission.example.test",
            Origin: origin,
            "Content-Type": "application/json",
          },
        },
        (res) => {
          let body = "";
          res.on("data", (b) => (body += b));
          res.on("end", () =>
            resolve({
              status: res.statusCode,
              headers: res.headers,
              body: JSON.parse(body),
            }),
          );
        },
      );
      req.on("error", reject);
      req.end(value === undefined ? undefined : JSON.stringify(value));
    });
  for (let i = 0; i < 16; i++) {
    const refused = await request("/auth/register/options", {});
    assert.equal(refused.status, 400);
    assert.equal(refused.headers["set-cookie"], undefined);
  }
  assert.equal(existsSync(file), false);
  const options = await request("/auth/register/options", { invite: code });
  assert.equal(options.status, 200);
  assert.equal(options.body.rp.id, "admission.example.test");
  const cookie = options.headers["set-cookie"][0].split(";")[0];
  assert.ok(cookie);
  assert.equal((await request("/auth/login/options", {})).status, 200);
  assert.equal((await request("/auth/status")).body.signedIn, false);
});
