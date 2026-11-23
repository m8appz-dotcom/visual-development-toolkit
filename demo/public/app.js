import { runEngine, showEngineResult } from "./engine-client.js";
import {
  $,
  $$,
  esc,
  load,
  save,
  draw,
  modal,
  notify,
  download,
  sha256,
  access,
  wireAccess,
} from "./core.js";
import { portableMode, portablePackage } from "./portable-package.js";
import { textPreview } from "./file-preview.js";
let artifacts = [],
  filter = "all",
  query = "",
  list = false,
  sort = "index",
  busy = false,
  error = "",
  result = "";
const valid = (s) =>
  s &&
  Array.isArray(s.selected) &&
  s.selected.length <= 32 &&
  s.selected.every(
    (n) =>
      typeof n === "string" && /^[a-z0-9_./-]+$/i.test(n) && !n.includes(".."),
  );
const saved = load("toolkit", { selected: [] }, valid);
let selected = new Set(saved.selected);
const persist = () => save("toolkit", { selected: [...selected] });
function thumbnail(a) {
  if (a.type === "image")
    return `<img src="assets/${a.path}" alt="${esc(a.label)}">`;
  return `<div class="artifact-source artifact-source-${esc(a.category || "mcp")}"><span>${esc(a.name.split(".").pop().toUpperCase())}</span><pre>${esc((a.sourcePreview || a.preview || ["Open source file"]).join("\n"))}</pre><span>${esc(a.name)}</span></div>`;
}
async function read(a) {
  const r = await fetch("assets/" + a.path);
  if (!r.ok)
    throw new Error(`Could not read ${a.name}. Retry before packaging.`);
  const bytes = new Uint8Array(await r.arrayBuffer());
  const hash = await sha256(bytes);
  if (hash !== a.sha256)
    throw new Error(
      `${a.name} differs from the included manifest. Packaging stopped.`,
    );
  return bytes;
}
async function verifyOrExport(exporting) {
  if (busy) return;
  const targets = exporting
    ? artifacts.filter((a) => selected.has(a.path))
    : artifacts;
  if (!targets.length) {
    notify("Select at least one file to build a package.", true);
    return;
  }
  busy = true;
  result = "";
  render();
  try {
    const paths = targets.map((a) => a.path);
    const job = portableMode
      ? await portablePackage(artifacts, paths, exporting)
      : await runEngine(exporting ? "package" : "verify", { paths });
    result = `${job.result.originalsVerified} original ${job.result.originalsVerified === 1 ? "file" : "files"} verified${exporting ? " and packaged without changes" : ""}.`;
    showEngineResult(
      exporting ? "Package ready" : "Originals verified",
      job,
      `<p>${esc(result)}</p>`,
    );
    notify(result);
  } catch (e) {
    result = e.message;
    notify(e.message, true);
  } finally {
    busy = false;
    render();
  }
}
async function openArtifact(a) {
  modal(a.label, "<p>Opening file…</p>");
  try {
    const bytes = await read(a);
    const url = "assets/" + a.path;
    let body =
      a.type === "image"
        ? `<img src="${url}" alt="${esc(a.label)}">`
        : ["binary", "package"].includes(a.type)
          ? `<pre>${esc((a.preview || ["Original binary file"]).join("\n"))}</pre>`
          : a.name.endsWith(".html")
            ? `<iframe title="${esc(a.name)}" sandbox src="${url}"></iframe>`
            : `<pre>${esc(new TextDecoder().decode(bytes))}</pre>`;
    modal(
      a.label,
      `${body}<dl class="file-details"><dt>File</dt><dd>${esc(a.path)}</dd><dt>Size</dt><dd>${a.bytes.toLocaleString("en-US")} bytes</dd><dt>SHA-256</dt><dd class="mono">${a.sha256}</dd></dl><div class="action-row"><button class="solid" data-select-open>${selected.has(a.path) ? "Remove from package" : "Add to package"}</button><button class="text-button" data-download-open>Download original ↓</button></div>`,
    );
    $("[data-select-open]").onclick = () => {
      selected.has(a.path) ? selected.delete(a.path) : selected.add(a.path);
      persist();
      $("#viewer").close();
      render();
      notify(
        `${a.name} ${selected.has(a.path) ? "added to" : "removed from"} the package.`,
      );
    };
    $("[data-download-open]").onclick = () => download(a.name, bytes, a.mime);
  } catch (e) {
    modal(
      "Could not open file",
      `<p>${esc(e.message)}</p><button class="solid" data-retry-file>Retry file</button>`,
    );
    $("[data-retry-file]").onclick = () => openArtifact(a);
  }
}
function render() {
  let visible = artifacts.filter(
    (a) =>
      (filter === "all" || a.category === filter) &&
      `${a.name} ${a.group} ${a.label}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  if (sort === "name") visible.sort((a, b) => a.name.localeCompare(b.name));
  if (sort === "project")
    visible.sort(
      (a, b) => a.group.localeCompare(b.group) || a.name.localeCompare(b.name),
    );
  draw(
    `<div class="toolkit-shell"><header class="toolkit-header"><strong>Toolkit.</strong><span class="toolkit-description">Build app integrations. Package MCP tools and skills for Codex.</span><div class="toolkit-view"><button data-view="grid" aria-pressed="${!list}">Visual</button><button data-view="list" aria-pressed="${list}">Index</button></div>${portableMode ? '<a class="access-button" href="https://github.com/m8appz-dotcom/visual-development-toolkit/blob/main/demo/README.md">Private workspace setup ↗</a>' : access()}</header><nav class="toolkit-toolbar" aria-label="Artifact filters"><div>${[
      ["all", "All"],
      ["app", "Application"],
      ["mcp", "MCP tools"],
      ["plugin", "Plugin"],
      ["skill", "Skills"],
      ["evidence", "Evidence"],
    ]
      .map(
        ([id, title]) =>
          `<button data-type="${id}" aria-pressed="${filter === id}">[${filter === id ? "×" : " "}] ${title}</button>`,
      )
      .join(
        "",
      )}</div><label class="toolkit-search"><span>Search</span><input id="artifact-search" type="search" aria-label="Search artifacts" placeholder="Tool, file or capability" value="${esc(query)}"></label></nav><div class="package-toolbar"><span>${selected.size} selected</span><div class="action-row"><button class="text-button" data-recorded-run>View recorded MCP run</button><a class="text-button" href="assets/app-bridge/toolkit-codex-plugin.zip" download>Download Codex plugin ↓</a><label>Sort<select id="artifact-sort">${[
      ["index", "Collection order"],
      ["name", "Filename"],
      ["project", "Project"],
    ]
      .map(
        ([v, l]) =>
          `<option value="${v}" ${sort === v ? "selected" : ""}>${l}</option>`,
      )
      .join(
        "",
      )}</select></label><button class="text-button" data-select-visible ${busy || !visible.length ? "disabled" : ""}>Select visible</button><button class="text-button" data-clear ${busy || !selected.size ? "disabled" : ""}>Clear selection</button><button data-verify ${busy || !artifacts.length ? "disabled" : ""}>${busy ? "Checking files…" : "Verify files"}</button><button class="solid" data-package ${busy || !selected.size ? "disabled" : ""}>${portableMode ? "Export selection ↓" : "Export package ↓"}</button></div></div><main id="main" aria-busy="${busy}"><div class="toolkit-count"><span>${esc(artifacts[0]?.project || "Toolkit source project")}</span><span>${String(visible.length).padStart(2, "0")} / ${artifacts.length}</span></div>${error ? `<div class="empty"><h1>The collection could not load.</h1><p>${esc(error)}</p><button class="solid" data-reload>Retry collection</button></div>` : `<div id="artifact-results" class="artifact-grid ${list ? "as-list" : ""}">${visible.length ? visible.map((a) => `<article class="artifact-item ${selected.has(a.path) ? "is-selected" : ""}"><label class="artifact-select"><input type="checkbox" data-select="${esc(a.path)}" aria-label="Select ${esc(a.label)}" ${selected.has(a.path) ? "checked" : ""} ${busy ? "disabled" : ""}></label><button class="artifact" data-artifact="${a.id}" aria-label="${esc(a.label + " — " + a.group + "/" + a.name)}"><div class="artifact-preview">${thumbnail(a)}</div><div class="artifact-caption"><span>${esc(a.label)}</span><span>${String(a.id + 1).padStart(2, "0")}</span></div><div class="artifact-file"><span>${esc(a.group)}</span><span>${esc(a.name)}</span></div></button></article>`).join("") : '<div class="empty"><h2>No matching files.</h2><p>Try another name or project.</p><button class="text-button" data-reset>Reset filters</button></div>'}</div>`}${result ? `<p class="package-result" role="status">${esc(result)}</p>` : ""}</main><footer class="toolkit-footer"><span>Visual Development Toolkit</span><span>Application capabilities · MCP tools · Codex skills</span></footer></div>`,
    () => {
      $$("[data-type]").forEach(
        (b) =>
          (b.onclick = () => {
            filter = b.dataset.type;
            render();
          }),
      );
      $$("[data-view]").forEach(
        (b) =>
          (b.onclick = () => {
            list = b.dataset.view === "list";
            render();
          }),
      );
      $("#artifact-sort").onchange = (e) => {
        sort = e.target.value;
        render();
      };
      $("#artifact-search").oninput = (e) => {
        const cursor = e.target.selectionStart;
        query = e.target.value;
        render();
        $("#artifact-search").setSelectionRange(cursor, cursor);
      };
      $$("[data-select]").forEach(
        (b) =>
          (b.onchange = () => {
            b.checked
              ? selected.add(b.dataset.select)
              : selected.delete(b.dataset.select);
            persist();
            render();
          }),
      );
      $$("[data-artifact]").forEach(
        (b) =>
          (b.onclick = () =>
            openArtifact(
              artifacts.find((a) => a.id === Number(b.dataset.artifact)),
            )),
      );
      $("[data-select-visible]").onclick = () => {
        visible.forEach((a) => selected.add(a.path));
        persist();
        render();
      };
      $("[data-clear]").onclick = () => {
        selected.clear();
        persist();
        render();
      };
      $("[data-verify]").onclick = () => verifyOrExport(false);
      $("[data-package]").onclick = () => verifyOrExport(true);
      $("[data-recorded-run]").onclick = async () => {
        try {
          const response = await fetch(
            "assets/app-bridge/bridge-evidence.json",
          );
          if (!response.ok)
            throw Error("The recorded run could not load. Please try again.");
          const evidence = await response.json();
          modal(
            "Recorded application-to-MCP run",
            `<p>AssetStudio inspected and extracted an authored Unity TextAsset through the real MCP gateway. This is a saved run; opening it does not start the native application.</p><table><thead><tr><th>Check</th><th>Observed result</th></tr></thead><tbody>${evidence.checks.map((c) => `<tr><td>${esc(c.name)}</td><td>${esc(c.status)}${c.matchesOriginal ? " · Matches the original" : ""}</td></tr>`).join("")}</tbody></table><p>Tools are exposed by the MCP server. The Codex plugin bundles the server connections and a reusable skill.</p>`,
          );
        } catch (error) {
          notify(error.message, true);
        }
      };
      $("[data-reset]")?.addEventListener("click", () => {
        query = "";
        filter = "all";
        render();
      });
      $("[data-reload]")?.addEventListener("click", init);
      wireAccess(
        "toolkit",
        () => ({ selected: [...selected] }),
        (data) => {
          if (!valid(data))
            throw new Error(
              "That workspace is not a compatible package selection.",
            );
          selected = new Set(
            data.selected.filter((p) => artifacts.some((a) => a.path === p)),
          );
          persist();
          render();
        },
      );
    },
  );
}
async function init() {
  try {
    const r = await fetch("assets/collection.json");
    if (!r.ok) throw new Error();
    artifacts = await r.json();
    await Promise.all(
      artifacts.map(async (artifact) => {
        if (!["document", "data"].includes(artifact.type)) return;
        artifact.sourcePreview = textPreview(await read(artifact));
      }),
    );
    selected = new Set(
      [...selected].filter((path) => artifacts.some((a) => a.path === path)),
    );
    error = "";
  } catch {
    error = "Check that the demo files are served together, then retry.";
  }
  render();
}
await init();
