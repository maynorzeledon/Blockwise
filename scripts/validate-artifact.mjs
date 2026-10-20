import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const projectRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const workerPath = resolve(projectRoot, process.argv[2] || "dist/server/index.js");
const manifestPath = resolve(projectRoot, "dist/.openai/hosting.json");

const [source, manifest] = await Promise.all([
  readFile(workerPath, "utf8"),
  process.argv[2] ? Promise.resolve("{}") : readFile(manifestPath, "utf8"),
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
const get=(path,options)=>workerModule.default.fetch(new Request('https://blockwise.test'+path,options),{});
let r=await get('/api/v1/facts?limit=1000');let data=await r.json();assert.equal(data.count,100);assert.ok(data.total>=901);assert.ok(data.next);assert.equal(r.headers.get('Access-Control-Allow-Origin'),'*');assert.ok(data.data.every(f=>f.minecraft_wiki_url.startsWith('https://minecraft.wiki/')));
const ids=new Set();let next='/api/v1/facts?limit=100';while(next){const page=await (await get(next)).json();for(const f of page.data){assert.ok(!ids.has(f.id));ids.add(f.id)}next=page.next?new URL(page.next).pathname+new URL(page.next).search:null}assert.equal(ids.size,data.total);
r=await get('/api/v1/facts/all?format=jsonl');const lines=(await r.text()).trim().split('\n').map(JSON.parse);assert.equal(lines.length,data.total);assert.ok(lines.every(f=>f.url.includes('/facts/')));
data=await (await get('/api/v1/facts?topic=history')).json();assert.ok(data.total>=3);assert.ok(data.data.every(f=>f.topics.includes('history')));data=await (await get('/api/v1/facts?edition=java&version=26.2')).json();assert.ok(data.data.every(f=>f.edition_versions.some(r=>r.edition==='java'&&r.verified)));
assert.equal((await get('/api/v1/facts?limit=-1')).status,400);assert.equal((await get('/api/v1/facts/no-such-id')).status,404);assert.equal((await get('/api/v1/facts',{method:'POST'})).status,405);assert.equal((await get('/api/v1/facts',{method:'OPTIONS'})).status,204);assert.equal(await (await get('/api/v1/facts',{method:'HEAD'})).text(),'');
r=await get('/facts/creeper-early-death-explosion');const factHtml=await r.text();assert.match(factHtml,/Creepers once exploded when killed/);assert.match(factHtml,/application\/ld\+json/);assert.match(factHtml,/rel="canonical"/);assert.match(factHtml,/minecraft.wiki/);assert.match(await(await get('/entry/creeper')).text(),/Selected history/);assert.match(await(await get('/facts/creeper-early-death-explosion?lang=es')).text(),/Los creepers explotaban al morir/);
assert.match(await(await get('/robots.txt')).text(),/Sitemap: https:\/\/blockwise.test\/sitemap.xml/);assert.match(await(await get('/llms.txt')).text(),/Do not invent or duplicate/);assert.match(await(await get('/sitemap.xml')).text(),/\/facts\/creeper-early-death-explosion/);assert.equal((await(await get('/openapi.json')).json()).openapi,'3.1.0');assert.equal((await workerModule.default.fetch(new Request('https://blockwise.test/api/progress'),{BUCKET:{}})).status,401);
console.log('Public HTTP: pagination without duplicates, bulk JSONL, source attribution, history/version filters, CORS, read-only methods, real HTML/JSON-LD pages, sitemap and private progress isolation passed.');

const supplement=await(await get('/api/v1/facts/discovery-sulfur-cube-1')).json();assert.equal(supplement.source_snapshot,'2026-06-16');assert.ok(supplement.supplemental_source.includes('minecraft.net'));assert.ok((await(await get('/api/v1/facts?tag=allay')).json()).data.every(f=>f.archive_url&&f.source_snapshot));
