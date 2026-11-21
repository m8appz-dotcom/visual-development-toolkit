import path from "node:path";
import { fileURLToPath } from "node:url";
import { execute, inputError } from "./process.mjs";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export default {
  name: "Visual Development Toolkit",
  actions: ["verify", "package"],
  status: async () => ({
    available: true,
    capabilities: [
      "MCP import",
      "Original integrity verification",
      "Portable packaging",
    ],
  }),
  async run(action, data, { directory }) {
    if (
      !Array.isArray(data.paths) ||
      !data.paths.length ||
      data.paths.length > 20 ||
      data.paths.some((p) => typeof p !== "string")
    )
      throw inputError("Select at least one original file.");
    const output = await execute(
      process.env.DEMO_PYTHON || "python",
      ["-B", path.join(root, "demo/engine_runner.py")],
      { action, paths: data.paths, directory },
      { cwd: root, timeout: 90000 },
    );
    return {
      result: output.result,
      files: output.files.map((f) => ({
        ...f,
        path: path.join(directory, f.name),
      })),
    };
  },
};
