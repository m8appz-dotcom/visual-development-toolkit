import { zipStore } from "./zip.js";

export const portableMode =
  typeof document !== "undefined" &&
  document.documentElement.dataset.packagingMode === "portable";

export function packageTargets(artifacts, paths) {
  const selected = new Set(paths);
  if (!selected.size) throw Error("Select at least one source file.");
  const names = new Set(artifacts.map((a) => a.path));
  if ([...selected].some((p) => !names.has(p)))
    throw Error("Choose files from this project before packaging.");
  return artifacts.filter((a) => selected.has(a.path) || a.required === true);
}

export async function verifyFiles(artifacts, readBytes) {
  const verified = [];
  for (const artifact of artifacts) {
    if (
      !/^[a-zA-Z0-9_./-]+$/.test(artifact.path) ||
      artifact.path.startsWith("/") ||
      artifact.path.includes("..") ||
      !/^[a-f0-9]{64}$/.test(artifact.sha256)
    )
      throw Error(
        "The project file list is invalid. Reload before continuing.",
      );
    const bytes = await readBytes(artifact);
    const digest = [
      ...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    ]
      .map((n) => n.toString(16).padStart(2, "0"))
      .join("");
    if (digest !== artifact.sha256 || bytes.byteLength !== artifact.bytes)
      throw Error(
        `${artifact.name} changed. Restore the original before packaging.`,
      );
    verified.push({ artifact, bytes });
  }
  return verified;
}

export async function portablePackage(artifacts, paths, exporting) {
  const targets = exporting ? packageTargets(artifacts, paths) : artifacts;
  const verified = await verifyFiles(targets, async (a) => {
    const response = await fetch(new URL("assets/" + a.path, import.meta.url));
    if (!response.ok)
      throw Error(`Could not load ${a.name}. Please try again.`);
    return new Uint8Array(await response.arrayBuffer());
  });
  const report = {
    version: 1,
    method: "Browser SHA-256 verification",
    originalsVerified: verified.length,
    files: verified.map(({ artifact: a }) => ({
      path: a.path,
      bytes: a.bytes,
      sha256: a.sha256,
    })),
  };
  const files = [
    {
      name: "integrity-report.json",
      url: URL.createObjectURL(
        new Blob([JSON.stringify(report, null, 2) + "\n"], {
          type: "application/json",
        }),
      ),
    },
  ];
  if (exporting)
    files.unshift({
      name: "toolkit-source-package.zip",
      url: URL.createObjectURL(
        new Blob(
          [
            zipStore(
              verified.map(({ artifact: a, bytes }) => ({
                name: a.path,
                bytes,
              })),
            ),
          ],
          { type: "application/zip" },
        ),
      ),
    });
  const release = () => files.forEach((f) => URL.revokeObjectURL(f.url));
  addEventListener("pagehide", release, { once: true });
  return { result: report, files, release };
}
