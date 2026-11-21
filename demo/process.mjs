import { spawn } from "node:child_process";
export function execute(
  command,
  args,
  input,
  { cwd, env = {}, timeout = 90000 } = {},
) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      env: { ...process.env, ...env },
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "",
      stderr = "",
      finished = false;
    const stop = setTimeout(() => {
      child.kill();
      const error = new Error("Engine task timed out");
      error.code = "engine_timeout";
      error.userMessage =
        "The engine took too long. Your draft is safe; retry the task.";
      reject(error);
    }, timeout);
    child.stdout.on("data", (part) => {
      stdout += part;
      if (stdout.length > 3000000) child.kill();
    });
    child.stderr.on("data", (part) => {
      stderr += part;
    });
    child.on("error", (error) => {
      clearTimeout(stop);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(stop);
      if (finished) return;
      finished = true;
      try {
        const result = JSON.parse(stdout.trim().split("\n").at(-1));
        if (code || result.error) {
          const error = new Error(
            stderr || result.error?.message || "Engine execution failed",
          );
          error.code = result.error?.code;
          error.userMessage = result.error?.message;
          reject(error);
        } else resolve(result);
      } catch (error) {
        reject(
          new Error(
            "Engine execution did not return a valid result. " +
              stderr.slice(-3000),
          ),
        );
      }
    });
    child.stdin.on("error", () => {});
    child.stdin.end(JSON.stringify(input));
  });
}
export function inputError(message) {
  return Object.assign(new Error(message), {
    code: "invalid_input",
    userMessage: message,
  });
}
