import { engineGateway } from "./engine-gateway.mjs";
import { validateJsonValue } from "./process.mjs";
import http from "node:http";
import { isIP } from "node:net";
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
import { randomBytes, createHash } from "node:crypto";
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
export const workspaceStorageLimits = Object.freeze({
  users: 16,
  credentialsPerUser: 4,
  credentials: 64,
  entryBytes: 192 * 1024,
  userBytes: 256 * 1024,
  totalBytes: 4 * 1024 * 1024,
  userNodes: 6000,
  totalNodes: 100000,
  metadataBytes: 1024 * 1024,
  recordBytes: 8 * 1024,
  userRecordBytes: 512,
  storeBytes: 8 * 1024 * 1024,
});
export function registrationCapacityReached(database, user, legacy = null) {
  return (
    Boolean(legacy) ||
    (!database.users[user] &&
      Object.keys(database.users).length >= workspaceStorageLimits.users) ||
    Object.keys(database.credentials).length >=
      workspaceStorageLimits.credentials ||
    Object.values(database.credentials).filter((record) => record.user === user)
      .length >= workspaceStorageLimits.credentialsPerUser
  );
}
function jsonNodeCount(value) {
  let count = 0;
  const pending = [value];
  while (pending.length) {
    const node = pending.pop();
    count++;
    if (node && typeof node === "object")
      for (const child of Object.values(node)) pending.push(child);
  }
  return count;
}
export function storedCredential(credential, user) {
  const allowed = new Set([
    "usb",
    "nfc",
    "ble",
    "smart-card",
    "hybrid",
    "internal",
  ]);
  return {
    id: credential.id,
    publicKey: encode(credential.publicKey),
    counter: credential.counter,
    transports: Array.isArray(credential.transports)
      ? [
          ...new Set(
            credential.transports.filter((value) => allowed.has(value)),
          ),
        ]
      : [],
    user,
  };
}
function recordBytes(key, value, credential = false) {
  // Reserve the largest uint32 WebAuthn counter so login cannot outgrow its allocation.
  const bounded = credential ? { ...value, counter: 4294967295 } : value;
  return (
    Buffer.byteLength(JSON.stringify(key)) +
    Buffer.byteLength(JSON.stringify(bounded)) +
    2
  );
}
function allocationStats(database) {
  const result = {};
  for (const user of Object.keys(database.users))
    Object.defineProperty(result, user, {
      value: { bytes: 0, nodes: 0 },
      enumerable: true,
    });
  for (const [key, value] of Object.entries(database.workspaces)) {
    const user = key.slice(0, key.lastIndexOf(":"));
    result[user].bytes += recordBytes(key, value);
    result[user].nodes += jsonNodeCount(value);
  }
  return result;
}
function validateWorkspaceStorage(candidate, legacy = null) {
  const userLimit = legacy ? 250 : workspaceStorageLimits.users;
  const credentialLimit = legacy ? 1000 : workspaceStorageLimits.credentials;
  if (
    Object.keys(candidate.users).length > userLimit ||
    Object.keys(candidate.credentials).length > credentialLimit
  )
    throw Error("Workspace access is at capacity. Your saved work is safe.");
  if (
    legacy?.identities &&
    (Object.keys(candidate.users).some(
      (key) => !legacy.identities.includes(key),
    ) ||
      Object.keys(candidate.credentials).some(
        (key) => !legacy.credentials.includes(key),
      ))
  )
    throw Error(
      "Existing workspace access is preserved. Ask the administrator before adding a passkey.",
    );
  if (
    candidate.usedInvites !== undefined &&
    (!Array.isArray(candidate.usedInvites) ||
      candidate.usedInvites.length > 16 ||
      candidate.usedInvites.some(
        (hash) => typeof hash !== "string" || !/^[a-f0-9]{64}$/.test(hash),
      ) ||
      new Set(candidate.usedInvites).size !== candidate.usedInvites.length)
  )
    throw Error(
      "Unrecognized workspace admission records. Preserve the store for offline recovery.",
    );
  let metadataBytes = 0;
  const credentialCounts = new Map();
  for (const records of [candidate.users, candidate.credentials])
    for (const [key, value] of Object.entries(records)) {
      validateJsonValue(value);
      const credential = records === candidate.credentials;
      const bytes = recordBytes(key, value, credential);
      metadataBytes += bytes;
      if (credential) {
        if (!Object.hasOwn(candidate.users, value.user))
          throw Error(
            "Unrecognized workspace owner. Preserve the store for offline recovery.",
          );
        const count = (credentialCounts.get(value.user) || 0) + 1;
        if (!legacy && count > workspaceStorageLimits.credentialsPerUser)
          throw Error(
            "Workspace access is at capacity. Your saved work is safe.",
          );
        credentialCounts.set(value.user, count);
      }
      const recordLimit =
        !credential && !legacy
          ? workspaceStorageLimits.userRecordBytes
          : workspaceStorageLimits.recordBytes +
            (legacy && credential ? 10 : 0);
      if (
        bytes > recordLimit ||
        metadataBytes >
          workspaceStorageLimits.metadataBytes + (legacy ? 10000 : 0)
      )
        throw Error(
          "Workspace access is at capacity. Your saved work is safe.",
        );
    }
  let totalBytes = 0,
    totalNodes = 0;
  const stats = new Map();
  for (const [key, value] of Object.entries(candidate.workspaces)) {
    validateJsonValue(value);
    const user = key.slice(0, key.lastIndexOf(":")),
      slot = key.slice(key.lastIndexOf(":") + 1);
    if (
      !Object.hasOwn(candidate.users, user) ||
      !["content", "jev", "toolkit", "voice", "film"].includes(slot)
    )
      throw Error(
        "Unrecognized workspace owner or slot. Preserve the store for offline recovery.",
      );
    const bytes = recordBytes(key, value),
      nodes = jsonNodeCount(value),
      prior = stats.get(user) || { bytes: 0, nodes: 0 };
    const next = { bytes: prior.bytes + bytes, nodes: prior.nodes + nodes };
    stats.set(user, next);
    totalBytes += bytes;
    totalNodes += nodes;
    const userBytes = legacy
      ? (legacy.allocations?.[user]?.bytes ?? 384 * 1024)
      : workspaceStorageLimits.userBytes;
    const userNodes = legacy
      ? (legacy.allocations?.[user]?.nodes ?? 30000)
      : workspaceStorageLimits.userNodes;
    if (
      bytes > workspaceStorageLimits.entryBytes ||
      next.bytes > userBytes ||
      next.nodes > userNodes ||
      totalBytes > workspaceStorageLimits.totalBytes ||
      totalNodes > workspaceStorageLimits.totalNodes ||
      stats.size > userLimit
    )
      throw Error(
        "Saved workspace storage is full. Export a local copy or reduce your saved work and try again.",
      );
  }
}
function checkedLegacyProfile(database, profile) {
  if (
    profile.version !== 1 ||
    !Array.isArray(profile.identities) ||
    !Array.isArray(profile.credentials) ||
    profile.identities.length > 250 ||
    profile.credentials.length > 1000 ||
    !profile.allocations ||
    profile.identities.some((user) => !Object.hasOwn(database.users, user)) ||
    profile.credentials.some(
      (key) => !Object.hasOwn(database.credentials, key),
    ) ||
    Object.keys(profile.allocations).length !== profile.identities.length
  )
    throw Error(
      "Unrecognized recovery profile. Preserve the store for offline recovery.",
    );
  for (const user of profile.identities) {
    const entry = Object.hasOwn(profile.allocations, user)
      ? profile.allocations[user]
      : null;
    if (
      !entry ||
      !Number.isSafeInteger(entry.bytes) ||
      entry.bytes < 0 ||
      entry.bytes > 384 * 1024 ||
      !Number.isSafeInteger(entry.nodes) ||
      entry.nodes < 0 ||
      entry.nodes > 30000
    )
      throw Error(
        "Unrecognized recovery profile. Preserve the store for offline recovery.",
      );
  }
  validateWorkspaceStorage(database, profile);
  return profile;
}
export function loadWorkspaceStore(storePath) {
  let database = { version: 1, users: {}, credentials: {}, workspaces: {} };
  if (existsSync(storePath)) {
    if (statSync(storePath).size > workspaceStorageLimits.storeBytes)
      throw Error(
        "Workspace store exceeds its safe capacity. Preserve it for offline recovery.",
      );
    database = JSON.parse(readFileSync(storePath, "utf8"));
  }
  if (
    database.version !== 1 ||
    !database.users ||
    !database.credentials ||
    !database.workspaces
  )
    throw Error("Unrecognized workspace store. Preserve it and investigate.");
  if (database.legacyAdmission)
    return {
      database,
      legacy: checkedLegacyProfile(database, database.legacyAdmission),
    };
  try {
    validateWorkspaceStorage(database);
    return { database, legacy: null };
  } catch {
    // Only a valid bounded previous-format store is grandfathered. Do not rewrite on startup.
    validateWorkspaceStorage(database, {});
    const legacy = {
      version: 1,
      identities: Object.keys(database.users),
      credentials: Object.keys(database.credentials),
      allocations: allocationStats(database),
    };
    return { database, legacy };
  }
}
export function persistWorkspaceCandidate(storePath, candidate, legacy = null) {
  if (legacy) candidate = { ...candidate, legacyAdmission: legacy };
  validateWorkspaceStorage(candidate, legacy);
  const serialized = JSON.stringify(candidate);
  if (Buffer.byteLength(serialized) > workspaceStorageLimits.storeBytes)
    throw Error(
      "Saved workspace storage is full. Export a local copy and try again.",
    );
  mkdirSync(path.dirname(storePath), { recursive: true, mode: 0o700 });
  writeFileSync(storePath + ".tmp", serialized, { mode: 0o600 });
  renameSync(storePath + ".tmp", storePath);
  return candidate;
}
export function saveWorkspaceCopy(
  database,
  user,
  key,
  state,
  storePath,
  legacy = null,
) {
  validateJsonValue(state);
  if (state === null || typeof state !== "object")
    throw Error("That workspace could not be saved.");
  return persistWorkspaceCandidate(
    storePath,
    {
      ...database,
      workspaces: { ...database.workspaces, [user + ":" + key]: state },
    },
    legacy,
  );
}
export function invitationHash(code) {
  return typeof code === "string" && /^[A-Za-z0-9_-]{43}$/.test(code)
    ? createHash("sha256").update(code).digest("hex")
    : "";
}
export function requireInvitation(database, allowed, hash) {
  if (!hash || !allowed.has(hash) || database.usedInvites?.includes(hash))
    throw Error(
      "Invitation required. Ask the administrator for a new code to create a private workspace.",
    );
}
export function commitInvitedRegistration(
  database,
  user,
  record,
  credential,
  hash,
  allowed,
  storePath,
) {
  requireInvitation(database, allowed, hash);
  if (registrationCapacityReached(database, user))
    throw Error("Workspace access is at capacity. Your saved work is safe.");
  return persistWorkspaceCandidate(storePath, {
    ...database,
    users: { ...database.users, [user]: record },
    credentials: { ...database.credentials, [credential.id]: credential },
    usedInvites: [...(database.usedInvites || []), hash],
  });
}
export function createDemoServer({
  root = path.join(HERE, "site"),
  storePath = path.join(HERE, ".demo-state", "workspaces.json"),
  origin = "http://localhost:8875",
  hosted = false,
  enableCapture = false,
  engine = null,
  registrationInvites = [],
} = {}) {
  const url = new URL(origin);
  const secureHost =
    hosted === true &&
    url.protocol === "https:" &&
    origin === url.origin &&
    !url.port &&
    !url.username &&
    !url.password &&
    /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$/.test(
      url.hostname,
    ) &&
    !/^[0-9.]+$/.test(url.hostname) &&
    !url.hostname.endsWith(".localhost");
  if (
    hosted
      ? !secureHost
      : url.hostname !== "localhost" || url.protocol !== "http:"
  )
    throw new Error(
      "This local demo server only supports its documented localhost origin. Configure production separately.",
    );
  if (
    hosted &&
    (enableCapture ||
      path.resolve(storePath).startsWith(path.resolve(root) + path.sep))
  )
    throw Error("Hosted access requires private storage and capture disabled.");
  const rpID = url.hostname;
  const sessions = new Map(),
    challenges = new Map(),
    rates = new Map(),
    captureToken = encode(randomBytes(32));
  const loaded = loadWorkspaceStore(storePath);
  let db = loaded.database;
  const legacy = loaded.legacy;
  if (
    !Array.isArray(registrationInvites) ||
    registrationInvites.length > 16 ||
    registrationInvites.some(
      (hash) => typeof hash !== "string" || !/^[a-f0-9]{64}$/.test(hash),
    )
  )
    throw Error("Configure at most sixteen private invitation hashes.");
  const invitations = new Set(registrationInvites);
  const persist = (candidate) => {
    db = persistWorkspaceCandidate(storePath, candidate, legacy);
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
    if (hosted && sessions.size >= 1024)
      throw Error("Workspace access is busy. Try again later.");
    const token = encode(randomBytes(32));
    sessions.set(token, { user, until: Date.now() + 3_600_000 });
    return cookie("__Host-workspace", token);
  };
  const pending = (res, data) => {
    if (hosted && challenges.size >= 512)
      throw Error("Workspace access is busy. Try again later.");
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
    return validateJsonValue(
      JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"),
    );
  };
  const handleEngine = engineGateway({
    engine:
      hosted && engine
        ? { ...engine, protectedActions: engine.actions }
        : engine,
    origin,
    stateRoot: path.dirname(storePath),
    authenticated: signedIn,
    storedJobsLimit: hosted ? 300 : Infinity,
  });
  const server = http.createServer(async (req, res) => {
    if (hosted) res.setHeader("Strict-Transport-Security", "max-age=31536000");
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("Referrer-Policy", "no-referrer");
    res.setHeader(
      "Content-Security-Policy",
      "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; media-src 'self' blob:; frame-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'; form-action 'self'",
    );
    res.setHeader(
      "Permissions-Policy",
      engine?.allowMicrophone === true
        ? "camera=(), microphone=(self), geolocation=()"
        : "camera=(), microphone=(), geolocation=()",
    );
    if (req.headers.host !== url.host) {
      json(res, 400, {
        error: "Open this workspace using its configured address.",
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
      const remote = req.socket.remoteAddress;
      const forwarded = req.headers["cf-connecting-ip"];
      const ip =
        hosted &&
        ["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(remote) &&
        typeof forwarded === "string" &&
        isIP(forwarded)
          ? forwarded
          : remote;
      if (!rates.has(ip) && rates.size >= 4096) {
        json(res, 429, {
          error: "Workspace access is busy. Try again shortly.",
        });
        return;
      }
      const rate = rates.get(ip) || { count: 0, until: now + 60000 };
      rate.count++;
      rates.set(ip, rate);
      if (rate.count > 120) {
        json(res, 429, {
          error: "Too many access attempts. Wait a minute and retry.",
        });
        return;
      }
      if (req.method === "GET" && pathname === "/auth/status") {
        json(res, 200, {
          signedIn: Boolean(signedIn(req)),
          passkeys: true,
          invitationRequired: hosted,
          registrationOpen:
            !legacy &&
            (!hosted ||
              [...invitations].some((hash) => !db.usedInvites?.includes(hash))),
        });
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
          const invite =
            hosted && !session ? invitationHash(input.invite) : null;
          if (hosted && !session) requireInvitation(db, invitations, invite);
          if (hosted && registrationCapacityReached(db, session?.user, legacy))
            throw Error(
              "This workspace has reached its access capacity. Existing passkeys still work.",
            );
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
            rpID,
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
            invite,
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
            expectedRPID: rpID,
            requireUserVerification: true,
          });
          if (!result.verified || !result.registrationInfo)
            throw new Error("That passkey could not be verified.");
          const c = result.registrationInfo.credential;
          if (db.credentials[c.id])
            throw new Error("That passkey is already registered.");
          // Verification yields: capacity may have changed since options were issued.
          if (hosted && registrationCapacityReached(db, expected.user, legacy))
            throw Error(
              "This workspace has reached its access capacity. Existing passkeys still work.",
            );
          const credential = storedCredential(c, expected.user);
          if (hosted && !expected.existingSession) {
            db = commitInvitedRegistration(
              db,
              expected.user,
              expected.record,
              credential,
              expected.invite,
              invitations,
              storePath,
            );
          } else
            persist({
              ...db,
              users: { ...db.users, [expected.user]: expected.record },
              credentials: { ...db.credentials, [c.id]: credential },
            });
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
            rpID,
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
            expectedRPID: rpID,
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
          persist({
            ...db,
            credentials: {
              ...db.credentials,
              [input.id]: {
                ...record,
                counter: result.authenticationInfo.newCounter,
              },
            },
          });
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
            db = saveWorkspaceCopy(
              db,
              session.user,
              input.key,
              input.state,
              storePath,
              legacy,
            );
            json(res, 200, { saved: true });
          } else json(res, 200, { state: db.workspaces[key] ?? null });
          return;
        }
        json(res, 404, { error: "That workspace action does not exist." });
      } catch (e) {
        json(res, 400, {
          error:
            /expired|already used|not registered|Sign in again|not match|already registered|too large|workspace type|Saved workspace storage is full|Workspace access is at capacity|access capacity|Invitation required|Existing workspace access is preserved/.test(
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
  if (hosted) {
    server.requestTimeout = 15000;
    server.headersTimeout = 10000;
    server.keepAliveTimeout = 5000;
    server.maxRequestsPerSocket = 100;
  }
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
