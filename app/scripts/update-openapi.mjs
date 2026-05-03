import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backendRootDir = resolve(rootDir, "..");
const venvPython = resolve(backendRootDir, ".venv/bin/python");
const generatedDir = resolve(rootDir, "src/generated");
const schemaPath = resolve(generatedDir, "openapi.json");
const typesPath = resolve(generatedDir, "openapi-types.ts");
const openapiUrl = process.env.BACKEND_OPENAPI_URL ?? "http://127.0.0.1:8000/openapi.json";
const pythonCode = [
    "import json",
    "from src.api.main import app",
    "print(json.dumps(app.openapi()))",
].join("; ");

async function readIfExists(filePath) {
    try {
        return await readFile(filePath, "utf-8");
    } catch {
        return null;
    }
}

async function main() {
    await mkdir(generatedDir, { recursive: true });

    let schema;

    try {
        const response = await fetch(openapiUrl);
        if (!response.ok) {
            throw new Error(
                `Failed to fetch OpenAPI schema (${response.status} ${response.statusText}) from ${openapiUrl}`,
            );
        }
        schema = await response.json();
    } catch (fetchError) {
        console.warn(
            `Could not fetch ${openapiUrl}. Falling back to local backend schema generation.`,
        );

        let pythonOutput = "";
        let pythonSucceeded = false;

        for (const pythonCommand of [venvPython, "python3", "python"]) {
            try {
                const result = await execFileAsync(pythonCommand, ["-c", pythonCode], {
                    cwd: backendRootDir,
                });
                pythonOutput = result.stdout;
                pythonSucceeded = true;
                break;
            } catch {
                continue;
            }
        }

        if (!pythonSucceeded) {
            throw new Error(
                `Unable to retrieve OpenAPI schema from ${openapiUrl} or local Python app. ${fetchError instanceof Error ? fetchError.message : String(fetchError)
                }`,
            );
        }

        schema = JSON.parse(pythonOutput);
    }

    const schemaText = `${JSON.stringify(schema, null, 2)}\n`;
    const currentSchema = await readIfExists(schemaPath);

    if (currentSchema !== schemaText) {
        await writeFile(schemaPath, schemaText, "utf-8");
        console.log("Updated src/generated/openapi.json");
    } else {
        console.log("OpenAPI schema unchanged");
    }

    await execFileAsync("npx", ["openapi-typescript", schemaPath, "-o", typesPath], {
        cwd: rootDir,
    });

    console.log("Updated src/generated/openapi-types.ts");
}

main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
});
