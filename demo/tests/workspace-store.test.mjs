import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import path from "node:path";
import { tmpdir } from "node:os";
import {
  mkdtempSync,
  readFileSync,
  mkdirSync,
  rmdirSync,
  rmSync,
  existsSync,
} from "node:fs";
import { createDemoServer, saveWorkspaceCopy } from "../server.mjs";

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
