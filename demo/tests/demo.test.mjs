import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import os from "node:os";
import path from "node:path";
import {
  readFileSync,
  existsSync,
  mkdtempSync,
  rmSync,
  readdirSync,
} from "node:fs";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { createDemoServer } from "../server.mjs";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number(process.env.DEMO_TEST_PORT || 18875);
const origin = "http://localhost:" + port;
const temporary = mkdtempSync(path.join(os.tmpdir(), "english-demo-test-"));
let server;
before(async () => {
  server = createDemoServer({
    root: path.join(root, "public"),
    storePath: path.join(temporary, "private", "workspaces.json"),
    origin,
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
});
after(async () => {
  if (server?.listening) await new Promise((resolve) => server.close(resolve));
  const resolved = path.resolve(temporary),
    prefix = path.resolve(os.tmpdir()) + path.sep + "english-demo-test-";
  if (!resolved.startsWith(prefix))
    throw new Error("Refusing cleanup outside the test directory.");
  rmSync(resolved, { recursive: true });
});
const post = (route, value = {}, cookie = "", requestOrigin = origin) =>
  fetch(origin + "/auth/" + route, {
    method: "POST",
    headers: {
      Origin: requestOrigin,
      "Content-Type": "application/json",
      Cookie: cookie,
    },
    body: JSON.stringify(value),
  });
test("English entry point and modules load", async () => {
  const r = await fetch(origin + "/");
  assert.equal(r.status, 200);
  assert.match(await r.text(), /lang="en"/);
  for (const file of [
    "app.js",
    "core.js",
    "base.css",
    "products.css",
    "ui.css",
  ])
    assert.equal((await fetch(origin + "/" + file)).status, 200);
});
test("every authored JavaScript module parses", () => {
  for (const file of readdirSync(path.join(root, "public")).filter((n) =>
    n.endsWith(".js"),
  ))
    execFileSync(process.execPath, [
      "--check",
      path.join(root, "public", file),
    ]);
});
test("private state and server files cannot be downloaded", async () => {
  for (const route of [
    "/server.mjs",
    "/package.json",
    "/.demo-state/workspaces.json",
    "/%2e%2e%2fserver.mjs",
  ])
    assert.equal((await fetch(origin + route)).status, 404);
});
test("workspace read and write require a real passkey session", async () => {
  for (const route of ["workspace/save", "workspace/load"])
    assert.equal(
      (await post(route, { key: "content", state: {} })).status,
      401,
    );
});
test("foreign origins cannot mutate authentication state", async () =>
  assert.equal(
    (await post("register/options", {}, "", "https://unrelated.example"))
      .status,
    403,
  ));
test("registration requires a discoverable credential and user verification", async () => {
  const r = await post("register/options");
  const d = await r.json();
  assert.equal(d.rp.id, "localhost");
  assert.equal(d.authenticatorSelection.residentKey, "required");
  assert.equal(d.authenticatorSelection.userVerification, "required");
  assert.match(
    r.headers.get("set-cookie"),
    /HttpOnly; SameSite=Strict; Secure/,
  );
});
test("invalid registration cannot sign in or reuse a challenge", async () => {
  const options = await post("register/options"),
    cookie = options.headers.get("set-cookie").split(";")[0];
  await options.json();
  assert.equal(
    (await post("register/verify", { id: "invalid" }, cookie)).status,
    400,
  );
  const replay = await post("register/verify", { id: "invalid" }, cookie);
  assert.equal(replay.status, 400);
  assert.match((await replay.json()).error, /already used/);
  assert.equal(
    (
      await (
        await fetch(origin + "/auth/status", { headers: { Cookie: cookie } })
      ).json()
    ).signedIn,
    false,
  );
});
test("an unknown login credential cannot create a session", async () => {
  const r = await post("login/options"),
    cookie = r.headers.get("set-cookie").split(";")[0],
    d = await r.json();
  assert.equal(d.userVerification, "required");
  assert.equal(
    (await post("login/verify", { id: "not-registered", response: {} }, cookie))
      .status,
    400,
  );
});
test("browser authentication code stays on the local origin", async () => {
  for (const route of [
    "/vendor/webauthn.js",
    "/vendor/methods/startRegistration.js",
  ])
    assert.equal((await fetch(origin + route)).status, 200);
});
test("camera and microphone stay disabled in the example server", async () => {
  const r = await fetch(origin + "/");
  assert.match(r.headers.get("permissions-policy"), /microphone=\(\)/);
  assert.match(r.headers.get("content-security-policy"), /script-src 'self'/);
  assert.equal((await fetch(origin + "/__capture")).status, 404);
});
test("included immutable assets retain their hashes", () => {
  const receipt = JSON.parse(
    readFileSync(path.join(root, "immutable-assets.json")),
  );
  for (const entry of receipt) {
    const bytes = readFileSync(path.join(root, "public", entry.path));
    assert.equal(bytes.length, entry.bytes);
    assert.equal(
      createHash("sha256").update(bytes).digest("hex"),
      entry.sha256,
    );
  }
});
test("collection entries match the package manifest when present", () => {
  const manifestPath = path.join(root, "public", "assets", "manifest.json");
  if (!existsSync(manifestPath)) return;
  const manifest = JSON.parse(readFileSync(manifestPath));
  assert.equal(manifest.length, 16);
  for (const item of manifest) {
    const bytes = readFileSync(path.join(root, "public", "assets", item.path));
    assert.equal(createHash("sha256").update(bytes).digest("hex"), item.sha256);
  }
});
