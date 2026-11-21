export const $ = (s, parent = document) => parent.querySelector(s);
export const $$ = (s, parent = document) => [...parent.querySelectorAll(s)];
export const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export const words = (text) =>
  text.trim() ? text.trim().split(/\s+/).length : 0;
export function load(
  key,
  fallback,
  validate = (value) => value && typeof value === "object",
) {
  try {
    const parsed = JSON.parse(localStorage.getItem(`portfolio-demo:${key}`));
    return validate(parsed) ? parsed : structuredClone(fallback);
  } catch {
    return structuredClone(fallback);
  }
}
export function save(key, value) {
  try {
    localStorage.setItem(`portfolio-demo:${key}`, JSON.stringify(value));
    return true;
  } catch {
    notify(
      "This browser could not save. Export your work before leaving.",
      true,
    );
    return false;
  }
}
export function notify(message, error = false) {
  const status = $("#notice");
  status.textContent = message;
  status.classList.toggle("error", error);
  clearTimeout(notify.timer);
  notify.timer = setTimeout(() => {
    status.textContent = "";
  }, 6500);
}
let returnFocus;
export function modal(title, body) {
  const dialog = $("#viewer");
  returnFocus = document.activeElement;
  if (dialog.open) dialog.close();
  dialog.innerHTML = `<div class="dialog-head"><h2>${esc(title)}</h2><button type="button" data-close aria-label="Close dialog">Close ×</button></div><div class="dialog-body">${body}</div>`;
  dialog.showModal();
  $("[data-close]", dialog).onclick = () => dialog.close();
  dialog.onclose = () =>
    returnFocus?.isConnected && returnFocus.focus({ preventScroll: true });
}
export function draw(html, bind) {
  const active = document.activeElement,
    id = active?.id;
  const marker = active?.dataset ? Object.entries(active.dataset)[0] : null;
  $("#app").innerHTML = html;
  bind?.();
  const target = id
    ? document.getElementById(id)
    : marker
      ? $$("button").find((b) => b.dataset[marker[0]] === marker[1])
      : null;
  target?.focus({ preventScroll: true });
}
export function download(name, body, type = "application/json") {
  const blob =
    body instanceof Blob
      ? body
      : new Blob(
          [
            typeof body === "string" || body instanceof Uint8Array
              ? body
              : JSON.stringify(body, null, 2) + "\n",
          ],
          { type },
        );
  const url = URL.createObjectURL(blob),
    link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
export const sha256 = async (bytes) =>
  [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
    .map((v) => v.toString(16).padStart(2, "0"))
    .join("");
export const tabs = (items, current, attribute = "tab") =>
  `<nav class="work-tabs" aria-label="Workspace sections">${items.map(([id, label]) => `<button data-${attribute}="${id}" aria-current="${current === id ? "page" : "false"}">${label}</button>`).join("")}</nav>`;
export const scope = "Interactive example · saved in this browser";
export const access = () =>
  '<button class="access-button" data-workspace>Private workspace ↗</button>';
const recoveryControls =
  '<section class="workspace-recovery"><h3>Keep a recoverable copy</h3><p>Export this workspace before changing devices. Restore a compatible export to replace the current local copy.</p><div class="action-row"><button data-backup>Export workspace ↓</button><label class="restore-file">Restore workspace<input id="workspace-file" type="file" accept="application/json,.json"></label></div><p id="recovery-message" role="status"></p></section>';
function wireRecovery(key, getState, setState) {
  $("[data-backup]").onclick = () =>
    download(`${key}-workspace.json`, {
      schema: "portfolio-workspace/1",
      app: key,
      state: getState(),
    });
  $("#workspace-file").onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      if (file.size > 200000)
        throw new Error("Choose a workspace export smaller than 200 KB.");
      const backup = JSON.parse(await file.text());
      if (backup.schema !== "portfolio-workspace/1" || backup.app !== key)
        throw new Error("Choose a workspace export for this product.");
      const previous = structuredClone(getState());
      setState(backup.state);
      modal(
        "Workspace restored",
        '<p>The export replaced the current local workspace. You can undo this change.</p><button class="solid" data-undo-import>Undo restore</button>',
      );
      $("[data-undo-import]").onclick = () => {
        setState(previous);
        $("#viewer").close();
        notify("The previous local workspace is back.");
      };
    } catch (e) {
      $("#recovery-message").textContent =
        e instanceof SyntaxError
          ? "This file is not a readable workspace export. Choose a JSON export from this demo."
          : e.message;
    } finally {
      event.target.value = "";
    }
  };
}
export function wireAccess(key, getState, setState) {
  $("[data-workspace]")?.addEventListener("click", async () => {
    modal("Private workspace", "<p>Checking workspace access…</p>");
    try {
      const response = await fetch("/auth/status");
      if (!response.ok) throw new Error();
      const status = await response.json();
      modal(
        "Private workspace",
        `<p>Save a private copy on this demo server using a passkey. Your browser keeps its local draft. The server stores your public credential and workspace; it never receives a PIN, fingerprint or private key.</p><p class="workspace-status">${status.signedIn ? "Signed in with a passkey." : "Not signed in."}</p><div class="action-row">${status.signedIn ? '<button class="solid" data-remote-save>Save private copy</button><button data-remote-load>Load private copy</button><button data-second-key>Add another passkey</button><button data-signout>Sign out</button>' : '<button class="solid" data-enroll>Create workspace with a passkey</button><button data-signin>Sign in with a passkey</button>'}</div><p>Add a second passkey after signing in so you retain access if one authenticator is lost.</p><p id="auth-message" role="status"></p>${recoveryControls}`,
      );
      wireRecovery(key, getState, setState);
      const message = (text) => {
        $("#auth-message").textContent = text;
      };
      const run = (fn) => async (event) => {
        const b = event.currentTarget;
        b.disabled = true;
        try {
          await fn();
        } catch (e) {
          message(
            e.message ||
              "The action could not finish. Your local work is safe.",
          );
        } finally {
          if (b.isConnected) b.disabled = false;
        }
      };
      const request = async (path, body) => {
        const r = await fetch("/auth/" + path, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body || {}),
        });
        const json = await r.json();
        if (!r.ok)
          throw new Error(json.error || "Could not complete workspace access.");
        return json;
      };
      const credential = async (kind) => {
        if (!window.isSecureContext || !window.PublicKeyCredential)
          throw new Error(
            "Passkeys need a supported browser on localhost or HTTPS.",
          );
        const { startRegistration, startAuthentication } =
          await import("/vendor/webauthn.js");
        const options = await request(kind + "/options");
        let response;
        try {
          response = await (kind === "register"
            ? startRegistration({ optionsJSON: options })
            : startAuthentication({ optionsJSON: options }));
        } catch {
          throw new Error(
            "Passkey access was cancelled or unavailable. Your local work is safe.",
          );
        }
        await request(kind + "/verify", response);
        $("#viewer").close();
        $("[data-workspace]").click();
      };
      $("[data-enroll]")?.addEventListener(
        "click",
        run(() => credential("register")),
      );
      $("[data-signin]")?.addEventListener(
        "click",
        run(() => credential("login")),
      );
      $("[data-second-key]")?.addEventListener(
        "click",
        run(() => credential("register")),
      );
      $("[data-signout]")?.addEventListener(
        "click",
        run(async () => {
          await request("logout");
          $("#viewer").close();
          notify("Signed out. Your local draft is still here.");
        }),
      );
      $("[data-remote-save]")?.addEventListener(
        "click",
        run(async () => {
          await request("workspace/save", { key, state: getState() });
          message("Private copy saved.");
        }),
      );
      $("[data-remote-load]")?.addEventListener(
        "click",
        run(async () => {
          const data = await request("workspace/load", { key });
          if (data.state === null) {
            message("There is no private copy yet. Save one first.");
            return;
          }
          setState(data.state);
          $("#viewer").close();
          notify("Private copy loaded.");
        }),
      );
    } catch {
      modal(
        "Private workspace",
        "<p>This copy supports local editing and exports. Private workspace access needs the included local server; see the demo README. No account has been created.</p>" +
          recoveryControls,
      );
      wireRecovery(key, getState, setState);
    }
  });
}
