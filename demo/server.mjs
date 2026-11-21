import { engineGateway } from "./engine-gateway.mjs";
import http from "node:http";
import {
  readFileSync,
  writeFileSync,
  renameSync,
  mkdirSync,
  existsSync,
  statSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes } from "node:crypto";
import { createRequire } from "node:module";
import {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} from "@simplewebauthn/server";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url),
  vendor = path.dirname(
    require
      .resolve("@simplewebauthn/browser")
      .replace(/script[\\/]index\.js$/, "esm/index.js"),
  );
const encode = (bytes) => Buffer.from(bytes).toString("base64url");
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/plain; charset=utf-8",
  ".csv": "text/csv; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
};
const safeFile = (root, name) => {
  const full = path.resolve(root, name);
  if (!full.startsWith(path.resolve(root) + path.sep)) return null;
  return full;
};
export function createDemoServer({
  root = path.join(HERE, "site"),
  storePath = path.join(HERE, ".demo-state", "workspaces.json"),
  origin = "http://localhost:8875",
  enableCapture = false,
  engine = null,
} = {}) {
  const url = new URL(origin);
  if (url.hostname !== "localhost" || url.protocol !== "http:")
    throw new Error(
      "This local demo server only supports its documented localhost origin. Configure production separately.",
    );
  const sessions = new Map(),
    challenges = new Map(),
    rates = new Map(),
    captureToken = encode(randomBytes(32));
  let db = { version: 1, users: {}, credentials: {}, workspaces: {} };
  if (existsSync(storePath)) db = JSON.parse(readFileSync(storePath, "utf8"));
  if (db.version !== 1 || !db.users || !db.credentials || !db.workspaces)
    throw new Error(
      "Unrecognized workspace store. Preserve it and investigate.",
    );
  const persist = () => {
    mkdirSync(path.dirname(storePath), { recursive: true, mode: 0o700 });
    const temporary = storePath + ".tmp";
    writeFileSync(temporary, JSON.stringify(db), { mode: 0o600 });
    renameSync(temporary, storePath);
  };
  const cookies = (req) =>
    Object.fromEntries(
      (req.headers.cookie || "").split(";").map((v) => v.trim().split("=")),
    );
  const cookie = (name, value, maxAge = 3600) =>
    `${name}=${value}; Path=/; Max-Age=${maxAge}; HttpOnly; SameSite=Strict; Secure`;
  const json = (res, status, value, headers = {}) => {
    res.writeHead(status, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...headers,
    });
    res.end(JSON.stringify(value));
  };
  const signedIn = (req) => {
    const s = sessions.get(cookies(req)["__Host-workspace"]);
    return s && s.until > Date.now() ? s : null;
  };
  const sessionCookie = (user) => {
    const token = encode(randomBytes(32));
    sessions.set(token, { user, until: Date.now() + 3_600_000 });
    return cookie("__Host-workspace", token);
  };
  const pending = (res, data) => {
    const token = encode(randomBytes(32));
    challenges.set(token, { ...data, until: Date.now() + 120000 });
    res.setHeader("Set-Cookie", cookie("__Host-challenge", token, 120));
  };
  const consume = (req, kind) => {
    const token = cookies(req)["__Host-challenge"],
      value = challenges.get(token);
    challenges.delete(token);
    if (!value || value.until < Date.now() || value.kind !== kind)
      throw new Error(
        "Start passkey access again. That request expired or was already used.",
      );
    return value;
  };
  const body = async (req) => {
    const chunks = [];
    let length = 0;
    for await (const chunk of req) {
      length += chunk.length;
      if (length > 200000)
        throw new Error(
          "This workspace is too large. Export a local copy instead.",
        );
      chunks.push(chunk);
    }
    return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
  };
  const handleEngine = engineGateway({
    engine,
    origin,
    stateRoot: path.dirname(storePath),
    authenticated: signedIn,
  });
  const server = http.createServer(async (req, res) => {
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("Referrer-Policy", "no-referrer");
    res.setHeader(
      "Content-Security-Policy",
      "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; media-src 'self' blob:; frame-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'; form-action 'self'",
    );
    res.setHeader(
      "Permissions-Policy",
      "camera=(), microphone=(), geolocation=()",
    );
    if (req.headers.host !== url.host) {
      json(res, 400, {
        error: "Open this demo using its configured localhost address.",
      });
      return;
    }
    let pathname;
    try {
      pathname = decodeURIComponent(new URL(req.url, origin).pathname);
    } catch {
      json(res, 400, { error: "That address is not valid." });
      return;
    }
    try {
      if (await handleEngine(req, res, pathname)) return;
    } catch {
      json(res, 500, {
        error: "The engine request could not finish. Your work is safe.",
      });
      return;
    }
    if (pathname.startsWith("/auth/")) {
      const now = Date.now();
      for (const map of [sessions, challenges])
        for (const [id, value] of map) if (value.until < now) map.delete(id);
      for (const [id, value] of rates) if (value.until < now) rates.delete(id);
      const ip = req.socket.remoteAddress,
        rate = rates.get(ip) || { count: 0, until: now + 60000 };
      rate.count++;
      rates.set(ip, rate);
      if (rate.count > 120) {
        json(res, 429, {
          error: "Too many access attempts. Wait a minute and retry.",
        });
        return;
      }
      if (req.method === "GET" && pathname === "/auth/status") {
        json(res, 200, { signedIn: Boolean(signedIn(req)), passkeys: true });
        return;
      }
      if (
        req.method !== "POST" ||
        req.headers.origin !== origin ||
        !String(req.headers["content-type"]).startsWith("application/json")
      ) {
        json(res, 403, {
          error: "Open the workspace from its original demo page and retry.",
        });
        return;
      }
      try {
        const input = await body(req),
          session = signedIn(req);
        if (pathname === "/auth/register/options") {
          const user = session?.user || encode(randomBytes(24)),
            record = db.users[user] || {
              id: user,
              webauthnUserID: encode(randomBytes(32)),
              name: "Private demo workspace",
            };
          const existing = Object.values(db.credentials).filter(
            (c) => c.user === user,
          );
          const options = await generateRegistrationOptions({
            rpName: "Portfolio demo workspace",
            rpID: "localhost",
            userID: new Uint8Array(
              Buffer.from(record.webauthnUserID, "base64url"),
            ),
            userName: record.name,
            attestationType: "none",
            authenticatorSelection: {
              residentKey: "required",
              userVerification: "required",
            },
            excludeCredentials: existing.map((c) => ({
              id: c.id,
              transports: c.transports,
            })),
          });
          pending(res, {
            kind: "register",
            challenge: options.challenge,
            user,
            record,
            existingSession: session?.user || null,
          });
          json(res, 200, options);
          return;
        }
        if (pathname === "/auth/register/verify") {
          const expected = consume(req, "register");
          if (
            expected.existingSession &&
            session?.user !== expected.existingSession
          )
            throw new Error("Sign in again before adding a passkey.");
          const result = await verifyRegistrationResponse({
            response: input,
            expectedChallenge: expected.challenge,
            expectedOrigin: origin,
            expectedRPID: "localhost",
            requireUserVerification: true,
          });
          if (!result.verified || !result.registrationInfo)
            throw new Error("That passkey could not be verified.");
          const c = result.registrationInfo.credential;
          if (db.credentials[c.id])
            throw new Error("That passkey is already registered.");
          db.users[expected.user] = expected.record;
          db.credentials[c.id] = {
            ...c,
            publicKey: encode(c.publicKey),
            user: expected.user,
          };
          persist();
          json(
            res,
            200,
            { verified: true },
            { "Set-Cookie": sessionCookie(expected.user) },
          );
          return;
        }
        if (pathname === "/auth/login/options") {
          const options = await generateAuthenticationOptions({
            rpID: "localhost",
            userVerification: "required",
          });
          pending(res, { kind: "login", challenge: options.challenge });
          json(res, 200, options);
          return;
        }
        if (pathname === "/auth/login/verify") {
          const expected = consume(req, "login"),
            record = db.credentials[input.id];
          if (!record)
            throw new Error(
              "That passkey is not registered with this workspace server.",
            );
          if (
            input.response?.userHandle &&
            input.response.userHandle !== db.users[record.user].webauthnUserID
          )
            throw new Error("That passkey does not match this workspace.");
          const result = await verifyAuthenticationResponse({
            response: input,
            expectedChallenge: expected.challenge,
            expectedOrigin: origin,
            expectedRPID: "localhost",
            credential: {
              ...record,
              publicKey: new Uint8Array(
                Buffer.from(record.publicKey, "base64url"),
              ),
            },
            requireUserVerification: true,
          });
          if (!result.verified)
            throw new Error("That passkey could not be verified.");
          record.counter = result.authenticationInfo.newCounter;
          persist();
          json(
            res,
            200,
            { verified: true },
            { "Set-Cookie": sessionCookie(record.user) },
          );
          return;
        }
        if (pathname === "/auth/logout") {
          sessions.delete(cookies(req)["__Host-workspace"]);
          json(
            res,
            200,
            { signedIn: false },
            { "Set-Cookie": cookie("__Host-workspace", "", 0) },
          );
          return;
        }
        if (
          pathname === "/auth/workspace/save" ||
          pathname === "/auth/workspace/load"
        ) {
          if (!session) {
            json(res, 401, {
              error:
                "Sign in with a passkey before accessing a private workspace.",
            });
            return;
          }
          if (
            !["content", "jev", "toolkit", "voice", "film"].includes(input.key)
          )
            throw new Error("That workspace type is not supported.");
          const key = session.user + ":" + input.key;
          if (pathname.endsWith("/save")) {
            if (input.state === null || typeof input.state !== "object")
              throw new Error("That workspace could not be saved.");
            db.workspaces[key] = input.state;
            persist();
            json(res, 200, { saved: true });
          } else json(res, 200, { state: db.workspaces[key] ?? null });
          return;
        }
        json(res, 404, { error: "That workspace action does not exist." });
      } catch (e) {
        json(res, 400, {
          error:
            /expired|already used|not registered|Sign in again|not match|already registered|too large|workspace type/.test(
              e.message,
            )
              ? e.message
              : "Passkey access could not be verified. Start again; your local work is safe.",
        });
      }
      return;
    }
    if (enableCapture && pathname === "/__capture") {
      console.log(
        "Development capture request",
        JSON.stringify({
          method: req.method,
          origin: req.headers.origin || null,
          host: req.headers.host,
        }),
      );
      const form = `<form method="post"><input type="hidden" name="captureToken" value="${captureToken}"><label>Filename<input name="filename"></label><label>Image bytes<textarea name="data"></textarea></label><button>Save capture</button></form>`;
      if (req.method === "GET") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(form);
        return;
      }
      // The no-referrer policy gives form navigations an opaque Origin. The per-process
      // random hidden nonce, loopback binding, Host check and fixed filenames protect this
      // development-only endpoint. Authentication routes still require the exact Origin.
      if (req.method === "POST") {
        let raw = "";
        for await (const chunk of req) {
          raw += chunk;
          if (raw.length > 5000000) {
            res.writeHead(413);
            res.end();
            return;
          }
        }
        const f = new URLSearchParams(raw),
          name = f.get("filename");
        if (
          f.get("captureToken") !== captureToken ||
          !/^(content|jev|toolkit|voice|film)-(first|desktop|mobile|tablet|state)\.jpg$/.test(
            name || "",
          )
        ) {
          res.writeHead(400);
          res.end();
          return;
        }
        const bytes = Buffer.from(f.get("data") || "", "base64");
        if (bytes[0] !== 255 || bytes[1] !== 216) {
          res.writeHead(400);
          res.end();
          return;
        }
        mkdirSync(path.join(HERE, "captures"), { recursive: true });
        writeFileSync(path.join(HERE, "captures", name), bytes);
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(
          form + `<p role="status">Saved ${name}: ${bytes.length} bytes</p>`,
        );
        return;
      }
      res.writeHead(403, { "Content-Type": "text/html; charset=utf-8" });
      res.end(
        '<p role="status">Capture request origin was rejected. No file was written.</p>',
      );
      return;
    }
    if (req.method !== "GET" && req.method !== "HEAD") {
      res.writeHead(405);
      res.end();
      return;
    }
    let file;
    if (pathname.startsWith("/vendor/")) {
      const relative =
        pathname === "/vendor/webauthn.js"
          ? "index.js"
          : pathname.slice("/vendor/".length);
      file = relative.endsWith(".js") ? safeFile(vendor, relative) : null;
    } else {
      let relative = pathname.slice(1);
      if (!relative || relative.endsWith("/")) relative += "index.html";
      file = safeFile(root, relative);
    }
    if (!file || !existsSync(file) || !statSync(file).isFile()) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("Not found");
      return;
    }
    res.writeHead(200, {
      "Content-Type": mime[path.extname(file)] || "application/octet-stream",
      "Cache-Control": "no-cache",
    });
    if (req.method === "HEAD") res.end();
    else res.end(readFileSync(file));
  });
  engine?.attach?.(server, { origin, authenticated: signedIn });
  return server;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const port = Number(process.env.PORT || 8875),
    origin = `http://localhost:${port}`;
  createDemoServer({
    origin,
    root: existsSync(path.join(HERE, "public"))
      ? path.join(HERE, "public")
      : path.join(HERE, "site"),
    enableCapture: process.env.ENABLE_CAPTURE === "1",
    engine: (await import("./engine-adapter.mjs")).default,
  }).listen(port, "127.0.0.1", () =>
    console.log(`English demos ready at ${origin}`),
  );
}
