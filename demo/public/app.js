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
import { zipStore } from "./zip.js";
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
  const lines = a.preview || [];
  return `<div class="artifact-${a.style || "script"}"><span>${esc(a.group.toUpperCase())}</span><strong>${lines.map(esc).join("<br>")}</strong><span>${esc(a.name)}</span></div>`;
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
    const files = [];
    for (const a of targets) {
      const bytes = await read(a);
      files.push({ name: a.path, bytes });
    }
    if (exporting) {
      const manifest = {
        kind: "authored-english-demo-package",
        files: targets.map((a) => ({
          path: a.path,
          bytes: a.bytes,
          sha256: a.sha256,
        })),
        transformation: "none",
      };
      files.push({
        name: "package-manifest.json",
        bytes: new TextEncoder().encode(
          JSON.stringify(manifest, null, 2) + "\n",
        ),
      });
      download("toolkit-example-package.zip", zipStore(files));
      result = `${targets.length} original files packaged. SHA-256 checked against the included manifest.`;
    } else
      result = `${targets.length} of ${artifacts.length} files match the included manifest. No file was changed.`;
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
      (filter === "all" || a.type === filter) &&
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
    `<div class="toolkit-shell"><header class="toolkit-header"><strong>Toolkit.</strong><span class="toolkit-description">A working archive of sources and outputs.</span><div class="toolkit-view"><button data-view="grid" aria-pressed="${!list}">Visual</button><button data-view="list" aria-pressed="${list}">Index</button></div>${access()}</header><nav class="toolkit-toolbar" aria-label="Artifact filters"><div>${[
      ["all", "All"],
      ["image", "Images"],
      ["document", "Documents"],
      ["data", "Data"],
    ]
      .map(
        ([id, title]) =>
          `<button data-type="${id}" aria-pressed="${filter === id}">[${filter === id ? "×" : " "}] ${title}</button>`,
      )
      .join(
        "",
      )}</div><label class="toolkit-search"><span>Search</span><input id="artifact-search" type="search" aria-label="Search artifacts" placeholder="Name or project" value="${esc(query)}"></label></nav><div class="package-toolbar"><span>${selected.size} selected</span><div class="action-row"><label>Sort<select id="artifact-sort">${[
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
      )}</select></label><button class="text-button" data-select-visible ${busy || !visible.length ? "disabled" : ""}>Select visible</button><button class="text-button" data-clear ${busy || !selected.size ? "disabled" : ""}>Clear selection</button><button data-verify ${busy || !artifacts.length ? "disabled" : ""}>${busy ? "Checking files…" : "Verify originals"}</button><button class="solid" data-package ${busy || !selected.size ? "disabled" : ""}>Export package ↓</button></div></div><main id="main" aria-busy="${busy}"><div class="toolkit-count"><span>English example collection</span><span>${String(visible.length).padStart(2, "0")} / ${artifacts.length}</span></div>${error ? `<div class="empty"><h1>The collection could not load.</h1><p>${esc(error)}</p><button class="solid" data-reload>Retry collection</button></div>` : `<div id="artifact-results" class="artifact-grid ${list ? "as-list" : ""}">${visible.length ? visible.map((a) => `<article class="artifact-item ${selected.has(a.path) ? "is-selected" : ""}"><label class="artifact-select"><input type="checkbox" data-select="${esc(a.path)}" aria-label="Select ${esc(a.label)}" ${selected.has(a.path) ? "checked" : ""} ${busy ? "disabled" : ""}></label><button class="artifact" data-artifact="${a.id}" aria-label="${esc(a.label + " — " + a.group + "/" + a.name)}"><div class="artifact-preview">${thumbnail(a)}</div><div class="artifact-caption"><span>${esc(a.label)}</span><span>${String(a.id + 1).padStart(2, "0")}</span></div><div class="artifact-file"><span>${esc(a.group)}</span><span>${esc(a.name)}</span></div></button></article>`).join("") : '<div class="empty"><h2>No matching files.</h2><p>Try another name or project.</p><button class="text-button" data-reset>Reset filters</button></div>'}</div>`}${result ? `<p class="package-result" role="status">${esc(result)}</p>` : ""}</main><footer class="toolkit-footer"><span>Visual Development Toolkit</span><span>Original bytes preserved · files stay in this browser until exported</span></footer></div>`,
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
    const r = await fetch("assets/manifest.json");
    if (!r.ok) throw new Error();
    artifacts = await r.json();
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
