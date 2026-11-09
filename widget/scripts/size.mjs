// Fail if the bundle is over the budget (30 KB gzipped, from the PRD).
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const BUDGET = 30 * 1024;
const file = resolve(dirname(fileURLToPath(import.meta.url)), "../dist/widget.js");
const raw = readFileSync(file);
const gz = gzipSync(raw, { level: 9 }).length;
const kb = (n) => `${(n / 1024).toFixed(1)} KB`;
console.log(`widget.js: ${kb(raw.length)} minified, ${kb(gz)} gzipped (budget ${kb(BUDGET)})`);
if (gz > BUDGET) {
  console.error("widget.js is over the size budget.");
  process.exit(1);
}
