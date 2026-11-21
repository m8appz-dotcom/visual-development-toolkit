import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { createDemoServer } from "../server.mjs";

test("engine requests enforce origin, access, session ownership, and safe error responses", async (t) => {
  const state = mkdtempSync(path.join(tmpdir(), "portfolio-engine-"));
  const secret = "test-service-identity-32-characters-long";
  const previous = process.env.DEMO_SERVICE_TOKEN;
  process.env.DEMO_SERVICE_TOKEN = secret;
  const origin = "http://localhost:9876";
  const engine = {
    name: "Test adapter",
    actions: ["public", "paid", "fail", "escape"],
    protectedActions: ["paid"],
    status: async () => ({ available: true }),
    async run(action, data, { directory }) {
      if (action === "fail") throw Error("private-secret-that-must-not-leak");
      const file = path.join(directory, "report.json");
      writeFileSync(file, '{"ok":true}');
      return {
        result: { actualInput: data.value },
        files: [
          {
            path: action === "escape" ? path.join(state, "outside.json") : file,
            name: "report.json",
            mime: "application/json",
          },
        ],
      };
    },
  };
  const server = createDemoServer({
    origin,
    storePath: path.join(state, "workspace.json"),
    engine,
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    rmSync(state, { recursive: true, force: true });
    if (previous === undefined) delete process.env.DEMO_SERVICE_TOKEN;
    else process.env.DEMO_SERVICE_TOKEN = previous;
  });
  const request = (route, method = "GET", value, headers = {}) =>
    new Promise((resolve, reject) => {
      const req = http.request(
        {
          host: "127.0.0.1",
          port: server.address().port,
          path: route,
          method,
          headers: {
            Host: "localhost:9876",
            Origin: origin,
            "Content-Type": "application/json",
            ...headers,
          },
        },
        (res) => {
          let body = "";
          res.on("data", (part) => (body += part));
          res.on("end", () =>
            resolve({
              status: res.statusCode,
              headers: res.headers,
              body: body ? JSON.parse(body) : null,
            }),
          );
        },
      );
      req.on("error", reject);
      req.end(value === undefined ? undefined : JSON.stringify(value));
    });
  assert.equal(
    (await request("/engine/run", "POST", { action: "paid" })).status,
    401,
  );
  assert.equal(
    (
      await request(
        "/engine/run",
        "POST",
        { action: "public" },
        { Origin: "https://other.example" },
      )
    ).status,
    403,
  );
  assert.equal((await request("/engine/run", "POST", null)).status, 400);
  assert.equal(
    (await request("/engine/run", "POST", { action: "unknown" })).status,
    400,
  );
  assert.equal(
    (
      await request(
        "/engine/run",
        "POST",
        { action: "paid" },
        { Authorization: "Bearer " + "é".repeat(secret.length) },
      )
    ).status,
    401,
  );
  const created = await request("/engine/run", "POST", {
    action: "public",
    data: { value: 7 },
  });
  assert.equal(created.status, 202);
  const cookie = created.headers["set-cookie"][0].split(";")[0],
    route = "/engine/jobs/" + created.body.id;
  assert.equal((await request(route)).status, 404);
  let job;
  for (let n = 0; n < 20; n++) {
    job = await request(route, "GET", undefined, { Cookie: cookie });
    if (job.body.status !== "running") break;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  assert.equal(job.body.status, "complete");
  assert.equal(job.body.result.actualInput, 7);
  assert.equal((await request(route + "/files/report.json")).status, 404);
  assert.equal(
    (
      await request(route + "/files/report.json", "GET", undefined, {
        Cookie: cookie,
      })
    ).status,
    200,
  );
  for (const action of ["fail", "escape"]) {
    const start = await request(
      "/engine/run",
      "POST",
      { action },
      { Authorization: "Bearer " + secret },
    );
    let check;
    for (let n = 0; n < 20; n++) {
      check = await request("/engine/jobs/" + start.body.id, "GET", undefined, {
        Authorization: "Bearer " + secret,
      });
      if (check.body.status !== "running") break;
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
    assert.equal(check.body.status, "failed");
    assert.ok(!JSON.stringify(check.body).includes("private-secret"));
    assert.equal(check.body.files.length, 0);
  }
  assert.equal(
    (
      await request(
        "/engine/run",
        "POST",
        { action: "paid" },
        { Authorization: "Bearer " + secret },
      )
    ).status,
    202,
  );
});
