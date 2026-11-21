import { randomBytes, randomUUID, timingSafeEqual } from "node:crypto";
import { mkdirSync, createReadStream, statSync, writeFileSync } from "node:fs";
import path from "node:path";

export function engineGateway({ engine, origin, stateRoot, authenticated }) {
  const jobs = new Map(),
    limits = new Map();
  let active = 0;
  const reply = (res, code, data) => {
    res.writeHead(code, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(data));
  };
  const service = (req) => {
    const configured = Buffer.from(process.env.DEMO_SERVICE_TOKEN || ""),
      token = Buffer.from(
        (req.headers.authorization || "").replace(/^Bearer /, ""),
      );
    return (
      configured.length >= 32 &&
      token.length === configured.length &&
      timingSafeEqual(token, configured)
    );
  };
  const owner = (req, res, create = false) => {
    if (service(req)) return "service";
    const cookie = (req.headers.cookie || "")
      .split(";")
      .map((v) => v.trim())
      .find((v) => v.startsWith("__Host-engine="))
      ?.slice(14);
    if (cookie && /^[a-f0-9]{48}$/.test(cookie)) return cookie;
    if (!create) return null;
    const token = randomBytes(24).toString("hex");
    res.setHeader(
      "Set-Cookie",
      `__Host-engine=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`,
    );
    return token;
  };
  return async function handle(req, res, pathname) {
    if (!pathname.startsWith("/engine/")) return false;
    if (!engine) {
      reply(res, 503, {
        error: "The engine adapter is not enabled in this copy.",
        code: "engine_unavailable",
      });
      return true;
    }
    if (pathname === "/engine/status" && req.method === "GET") {
      const status = await engine.status();
      reply(res, 200, {
        name: engine.name,
        ...status,
        signedIn: !!authenticated(req),
        actions: engine.actions,
      });
      return true;
    }
    const now = Date.now();
    for (const [id, job] of jobs)
      if (job.expires < now && !["running", "queued"].includes(job.status))
        jobs.delete(id);
    for (const [id, entry] of limits) if (entry.until < now) limits.delete(id);
    if (pathname === "/engine/run" && req.method === "POST") {
      if (req.headers.origin !== origin && !service(req)) {
        reply(res, 403, {
          error: "Open this action from the original demo page.",
          code: "origin_rejected",
        });
        return true;
      }
      if (!String(req.headers["content-type"]).startsWith("application/json")) {
        reply(res, 415, {
          error: "Send a JSON request.",
          code: "invalid_request",
        });
        return true;
      }
      let input;
      try {
        let size = 0;
        const chunks = [];
        for await (const part of req) {
          size += part.length;
          if (size > 180000) throw Error();
          chunks.push(part);
        }
        input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      } catch {
        reply(res, 400, {
          error: "The request is unreadable or too large.",
          code: "invalid_request",
        });
        return true;
      }
      if (
        !input ||
        typeof input !== "object" ||
        !engine.actions.includes(input.action)
      ) {
        reply(res, 400, {
          error: "Choose a supported engine action.",
          code: "unsupported_action",
        });
        return true;
      }
      if (
        engine.protectedActions?.includes(input.action) &&
        !authenticated(req) &&
        !service(req)
      ) {
        reply(res, 401, {
          error:
            "Sign in with a passkey before starting a live service request.",
          code: "sign_in_required",
        });
        return true;
      }
      const who = owner(req, res, true),
        rate = limits.get(who) || { count: 0, until: now + 60000 };
      if (rate.count >= 12 || active >= 2 || jobs.size >= 60) {
        reply(res, 429, {
          error: "The engine is busy. Wait for the current task, then retry.",
          code: "engine_busy",
        });
        return true;
      }
      rate.count++;
      limits.set(who, rate);
      const id = randomUUID(),
        directory = path.join(stateRoot, "engine", id);
      mkdirSync(directory, { recursive: true });
      const job = {
        id,
        owner: who,
        status: "running",
        createdAt: new Date().toISOString(),
        expires: now + 3600000,
        result: null,
        files: [],
        error: null,
      };
      jobs.set(id, job);
      active++;
      reply(res, 202, { id, status: job.status });
      Promise.resolve()
        .then(() =>
          engine.run(input.action, input.data || {}, { directory, id }),
        )
        .then((output) => {
          job.result = output.result;
          job.files = (output.files || []).map((file) => {
            const target = path.resolve(file.path);
            if (!target.startsWith(path.resolve(directory) + path.sep))
              throw Error("Artifact outside run directory");
            if (!/^[a-zA-Z0-9_.-]+$/.test(file.name))
              throw Error("Unsafe artifact name");
            return { ...file, path: target };
          });
          job.status = "complete";
        })
        .catch((error) => {
          const permitted = new Set([
            "provider_not_configured",
            "provider_unavailable",
            "invalid_input",
            "validation_failed",
            "engine_timeout",
            "engine_unavailable",
            "source_changed",
          ]);
          job.result = null;
          job.files = [];
          job.error = {
            code: permitted.has(error.code) ? error.code : "engine_failed",
            message: permitted.has(error.code)
              ? error.userMessage ||
                "The engine could not finish this request. Your local work is safe."
              : "The engine could not finish this request. Check its private run log and retry.",
          };
          writeFileSync(
            path.join(directory, "private-error.log"),
            String(error.stack || error),
          );
          job.status = "failed";
        })
        .finally(() => {
          active--;
        });
      return true;
    }
    const match = pathname.match(
      /^\/engine\/jobs\/([a-f0-9-]{36})(?:\/files\/([a-zA-Z0-9_.-]+))?$/,
    );
    if (req.method === "GET" && match) {
      const job = jobs.get(match[1]);
      if (!job || job.owner !== owner(req, res)) {
        reply(res, 404, {
          error: "This engine task is not available in this browser session.",
          code: "not_found",
        });
        return true;
      }
      if (!match[2]) {
        reply(res, 200, {
          id: job.id,
          status: job.status,
          createdAt: job.createdAt,
          result: job.result,
          error: job.error,
          files: job.files.map((f) => ({
            name: f.name,
            mime: f.mime,
            url: `/engine/jobs/${job.id}/files/${f.name}`,
          })),
        });
        return true;
      }
      const file = job.files.find((f) => f.name === match[2]);
      if (job.status !== "complete" || !file) {
        reply(res, 404, {
          error: "The output is not ready.",
          code: "not_found",
        });
        return true;
      }
      const size = statSync(file.path).size,
        range = req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
      res.setHeader("Content-Type", file.mime);
      res.setHeader("Cache-Control", "no-store");
      res.setHeader("Content-Disposition", `inline; filename="${file.name}"`);
      res.setHeader("Accept-Ranges", "bytes");
      if (range) {
        const start = Number(range[1]),
          end = Math.min(range[2] ? Number(range[2]) : size - 1, size - 1);
        if (start > end || start >= size) {
          res.writeHead(416, { "Content-Range": `bytes */${size}` });
          res.end();
          return true;
        }
        res.writeHead(206, {
          "Content-Range": `bytes ${start}-${end}/${size}`,
          "Content-Length": end - start + 1,
        });
        createReadStream(file.path, { start, end }).pipe(res);
      } else {
        res.writeHead(200, { "Content-Length": size });
        createReadStream(file.path).pipe(res);
      }
      return true;
    }
    reply(res, 404, {
      error: "That engine action does not exist.",
      code: "not_found",
    });
    return true;
  };
}
