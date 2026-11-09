// Build the embeddable widget (../widget) into public/embed/widget.js.
// Runs before `next dev` and `next build`, so deploys always ship a fresh widget.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const widgetDir = resolve(dirname(fileURLToPath(import.meta.url)), "../../widget");
const npm = process.platform === "win32" ? "npm.cmd" : "npm";

function run(args) {
  const result = spawnSync(npm, args, { cwd: widgetDir, stdio: "inherit" });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

if (!existsSync(resolve(widgetDir, "node_modules"))) {
  run(["ci", "--no-audit", "--no-fund"]);
}
run(["run", "build"]);
