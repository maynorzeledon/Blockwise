import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const projectRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const workerPath = resolve(projectRoot, "dist/server/index.js");
const manifestPath = resolve(projectRoot, "dist/.openai/hosting.json");

const [source, manifest] = await Promise.all([
  readFile(workerPath, "utf8"),
  readFile(manifestPath, "utf8"),
]);
JSON.parse(manifest);

// A data URL forces ESM parsing even though the generated output has no package.json.
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const workerModule = await import(moduleUrl);
assert.equal(
  typeof workerModule.default?.fetch,
  "function",
  `${pathToFileURL(workerPath)} must export default.fetch`,
);

console.log("Artifact is valid ESM and exports default.fetch");

// The hosting proxy must receive decoded bytes, not gzip bytes with a header it may strip.
for (const [path, marker] of [['/', '<!DOCTYPE html>'], ['/app.js', "'use strict';"] , ['/catalog.js', 'let '] , ['/versions.json', '{'], ['/facts.json', '[']]) {
  const response = await workerModule.default.fetch(new Request('https://blockwise.test'+path), {});
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('Content-Encoding'), null);
  const text = await response.text();
  assert.ok(text.trimStart().toLowerCase().startsWith(marker.toLowerCase()), path+' must return decoded content');
}
console.log('HTTP response bodies are decoded HTML, JavaScript and JSON');
