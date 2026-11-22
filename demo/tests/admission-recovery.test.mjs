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
  workspaceStorageLimits,
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
test("original-format aggregate and access allocations survive stricter global limits", (t) => {
  const file = fixture(t);
  for (const kind of ["nodes", "bytes", "entry", "metadata", "depth"]) {
    const database = empty();
    const users = kind === "bytes" ? 12 : kind === "nodes" ? 4 : 1;
    for (let i = 0; i < users; i++) {
      const user = "user-" + i;
      database.users[user] = { id: user };
      for (const slot of ["content", "voice"])
        database.workspaces[user + ":" + slot] =
          kind === "nodes"
            ? { items: Array.from({ length: 14000 }, () => ({})) }
            : kind === "bytes"
              ? { draft: "x".repeat(180000) }
              : { draft: "old" };
    }
    database.credentials.key = {
      id: "key",
      user: "user-0",
      publicKey: "fixture",
      counter: 9,
    };
    if (kind === "entry")
      database.workspaces["user-0:content"] = {
        items: Array.from({ length: 25000 }, () => ({})),
      };
    if (kind === "metadata")
      database.credentials.key.transports = ["x".repeat(150000)];
    if (kind === "depth")
      database.workspaces["user-0:content"] = JSON.parse(
        '{"x":'.repeat(40) + "0" + "}".repeat(40),
      );
    const original = JSON.stringify(database);
    writeFileSync(file, original);
    const loaded = loadWorkspaceStore(file);
    assert.ok(loaded.legacy, kind);
    assert.equal(readFileSync(file, "utf8"), original);
    createDemoServer({ storePath: file });
    const saved = persistWorkspaceCandidate(
      file,
      {
        ...loaded.database,
        credentials: {
          key: { ...loaded.database.credentials.key, counter: 10 },
        },
      },
      loaded.legacy,
    );
    assert.deepEqual(saved.workspaces, database.workspaces);
    assert.equal(saved.credentials.key.counter, 10);
    const reopened = loadWorkspaceStore(file);
    assert.ok(reopened.legacy.aggregate);
    assert.ok(reopened.legacy.accessAllocations);
    assert.deepEqual(reopened.legacy.aggregate, loaded.legacy.aggregate);
    const current = readFileSync(file, "utf8");
    assert.throws(
      () =>
        saveWorkspaceCopy(
          reopened.database,
          "user-0",
          "film",
          { draft: "growth" },
          file,
          reopened.legacy,
        ),
      /migrate it/,
    );
    assert.equal(readFileSync(file, "utf8"), current);
  }
});
test("a near-limit original store retains headroom for its first login update and restart", (t) => {
  const file = fixture(t),
    database = empty();
  database.users.first = { id: "first" };
  database.credentials.key = {
    id: "key",
    user: "first",
    publicKey: "fixture",
    counter: 9,
  };
  database.workspaces["first:content"] = { draft: "" };
  const target = workspaceStorageLimits.storeBytes - 128;
  database.workspaces["first:content"].draft = "x".repeat(
    target - Buffer.byteLength(JSON.stringify(database)),
  );
  const original = JSON.stringify(database);
  assert.equal(Buffer.byteLength(original), target);
  writeFileSync(file, original);
  let loaded = loadWorkspaceStore(file);
  assert.ok(loaded.legacy);
  assert.equal(readFileSync(file, "utf8"), original);
  const candidate = {
    ...loaded.database,
    credentials: { key: { ...loaded.database.credentials.key, counter: 10 } },
  };
  const saved = persistWorkspaceCandidate(file, candidate, loaded.legacy);
  const bytes = Buffer.byteLength(readFileSync(file, "utf8"));
  assert.ok(bytes > workspaceStorageLimits.storeBytes);
  assert.ok(bytes <= workspaceStorageLimits.recoveryStoreBytes);
  loaded = loadWorkspaceStore(file);
  assert.ok(loaded.legacy);
  assert.equal(loaded.database.credentials.key.counter, 10);
  assert.equal(
    loaded.database.workspaces["first:content"].draft,
    saved.workspaces["first:content"].draft,
  );
  assert.throws(
    () =>
      saveWorkspaceCopy(
        loaded.database,
        "first",
        "content",
        { draft: "replace" },
        file,
        loaded.legacy,
      ),
    /migrate it/,
  );
});
test("legacy recovery stays read-only across restart and rejects shape changes", (t) => {
  const file = fixture(t),
    database = empty();
  database.users.first = { id: "first" };
  database.credentials.key = {
    id: "key",
    user: "first",
    publicKey: "fixture",
    counter: 9,
  };
  database.workspaces["first:content"] = {
    items: Array.from({ length: 25000 }, () => 0),
  };
  writeFileSync(file, JSON.stringify(database));
  let loaded = loadWorkspaceStore(file);
  const prior = readFileSync(file, "utf8");
  assert.throws(
    () =>
      saveWorkspaceCopy(
        loaded.database,
        "first",
        "content",
        { draft: "small" },
        file,
        loaded.legacy,
      ),
    /migrate it/,
  );
  assert.equal(readFileSync(file, "utf8"), prior);
  assert.throws(
    () =>
      persistWorkspaceCandidate(
        file,
        {
          ...loaded.database,
          workspaces: {
            "first:content": {
              items: Array.from({ length: 13000 }, () => ({})),
            },
          },
        },
        loaded.legacy,
      ),
    /migrate it/,
  );
  assert.equal(readFileSync(file, "utf8"), prior);
  const saved = persistWorkspaceCandidate(
    file,
    {
      ...loaded.database,
      credentials: { key: { ...loaded.database.credentials.key, counter: 10 } },
    },
    loaded.legacy,
  );
  loaded = loadWorkspaceStore(file);
  assert.ok(loaded.legacy.workspaceDigests);
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
  assert.equal(loaded.database.workspaces["first:content"].items.length, 25000);
  assert.equal(loaded.database.credentials.key.counter, 10);
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
