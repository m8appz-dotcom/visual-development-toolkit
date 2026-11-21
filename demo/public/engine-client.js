import { $, esc, modal, notify } from "./core.js";
export async function runEngine(action, data, { onStatus } = {}) {
  const response = await fetch("/engine/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, data }),
  });
  const initial = await response.json();
  if (!response.ok) {
    const error = new Error(
      initial.error || "The engine request could not start.",
    );
    error.code = initial.code;
    throw error;
  }
  const deadline = Date.now() + 300000;
  while (Date.now() < deadline) {
    const result = await fetch("/engine/jobs/" + initial.id);
    const job = await result.json();
    if (!result.ok) throw Error(job.error || "The engine task is unavailable.");
    if (job.status === "complete") return job;
    if (job.status === "failed")
      throw Object.assign(new Error(job.error.message), {
        code: job.error.code,
      });
    onStatus?.(job.status);
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
  throw Error(
    "The task is still running. Keep this page open and check again shortly.",
  );
}
export async function engineAction(button, action, data, renderResult) {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "Working…";
  try {
    const job = await runEngine(action, data);
    renderResult(job);
    return job;
  } catch (error) {
    notify(error.message, true);
    if (error.code === "sign_in_required") $("[data-workspace]")?.click();
    return null;
  } finally {
    if (button.isConnected) {
      button.disabled = false;
      button.textContent = label;
    }
  }
}
export function showEngineResult(title, job, body = "") {
  modal(
    title,
    body +
      `<div class="action-row">${(job.files || []).map((f) => `<a class="solid" href="${esc(f.url)}" download="${esc(f.name)}">Download ${esc(f.name)} ↓</a>`).join("")}</div>`,
  );
}
