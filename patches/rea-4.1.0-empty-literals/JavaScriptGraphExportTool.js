import { z } from "zod";
import { mkdir, open, rename, access } from "node:fs/promises";
import { join, resolve } from "node:path";
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { reconstructJavaScriptArtifact } from "../application/JavaScriptArtifactReconstruction.js";

// Serialize top-level graph arrays incrementally, avoiding V8's aggregate-string limit.
const writeGraph = async (path, value) => {
    try { await access(path); throw new Error(`Output already exists: ${path}`); }
    catch (error) { if (error.code !== "ENOENT") throw error; }
    const temporary = `${path}.part`;
    const file = await open(temporary, "wx");
    let buffer = "";
    const append = async text => {
        buffer += text;
        if (buffer.length >= 1024 * 1024) { await file.writeFile(buffer); buffer = ""; }
    };
    try {
        await append("{"); let first = true;
        for (const [key, item] of Object.entries(value)) {
            await append(`${first ? "" : ","}${JSON.stringify(key)}:`); first = false;
            if (Array.isArray(item)) {
                await append("[");
                for (let index=0; index<item.length; index++)
                    await append(`${index ? "," : ""}${JSON.stringify(item[index])}`);
                await append("]");
            } else await append(JSON.stringify(item));
        }
        await append("}"); if (buffer) await file.writeFile(buffer);
    } finally { await file.close(); }
    await rename(temporary, path);
    const hash = createHash("sha256"); let bytes = 0;
    for await (const chunk of createReadStream(path)) { hash.update(chunk); bytes += chunk.length; }
    return { path, bytes, sha256: hash.digest("hex") };
};

/** File-based companion to the existing inline tool for large application graphs. */
export const registerJavaScriptGraphExport = server => server.registerTool(
    "export_javascript_application_graph",
    {
        title: "Export JavaScript Application Graph",
        description: "Statically reconstruct a complete local JavaScript/ASAR application and export its validated application and semantic graphs to new files. Does not execute application code or overwrite existing output files. Returns paths, hashes, counts, statistics and limitations rather than an unbounded inline graph.",
        inputSchema: z.object({ input_path: z.string().min(1), format: z.enum(["auto","asar","directory"]).default("auto"), output_directory: z.string().min(1) }),
        annotations: { readOnlyHint:false, destructiveHint:false, idempotentHint:false, openWorldHint:false },
    },
    async (input, context) => {
        try {
            const output = resolve(input.output_directory); await mkdir(output, {recursive:true});
            // Reject conflicts before doing expensive analysis.
            for (const name of ["semantic-graph.json","application-graph.json","analysis.json"])
                try { await access(join(output,name)); throw new Error(`Output already exists: ${name}`); }
                catch(error) { if(error.code!=="ENOENT") throw error; }
            const r = await reconstructJavaScriptArtifact({input_path:input.input_path,format:input.format}, context.mcpReq?.signal ?? context.signal);
            const files = {};
            files.semantic_graph = await writeGraph(join(output,"semantic-graph.json"),r.semantic_graph);
            files.application_graph = await writeGraph(join(output,"application-graph.json"),r.graph);
            const {graph,semantic_graph,electron_summary,...metadata}=r;
            const analysis = {...metadata,summary:electron_summary,application_graph_id:graph.graph_id,semantic_graph_id:semantic_graph.graph_id};
            files.analysis = await writeGraph(join(output,"analysis.json"),analysis);
            const result={exported_files:files,statistics:r.statistics,semantic_nodes:semantic_graph.nodes.length,semantic_relations:semantic_graph.relations.length,application_nodes:graph.nodes.length,application_edges:graph.edges.length,coverage_status:semantic_graph.coverage.status,root_artifact_sha256:r.root_artifact_sha256};
            return {content:[{type:"text",text:JSON.stringify({result})}],structuredContent:{result}};
        } catch(error) {
            const diagnostic={name:error.name,message:error.message};
            return {isError:true,content:[{type:"text",text:JSON.stringify({error:diagnostic})}],structuredContent:{error:diagnostic}};
        }
    }
);
