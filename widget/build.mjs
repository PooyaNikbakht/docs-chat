// Bundle the widget into one minified IIFE, and copy it into the frontend's public/embed/.
import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as esbuild from "esbuild";

const root = dirname(fileURLToPath(import.meta.url));
const outfile = resolve(root, "dist/widget.js");
const embed = resolve(root, "../frontend/public/embed/widget.js");
const watch = process.argv.includes("--watch");

const copyToFrontend = {
  name: "copy-to-frontend",
  setup(build) {
    build.onEnd(async (result) => {
      if (result.errors.length) return;
      await mkdir(dirname(embed), { recursive: true });
      await copyFile(outfile, embed);
      console.log(`widget: built ${outfile} and copied it to frontend/public/embed/`);
    });
  },
};

const options = {
  entryPoints: [resolve(root, "src/index.ts")],
  outfile,
  bundle: true,
  minify: true,
  format: "iife",
  target: ["es2020", "safari15"],
  legalComments: "none",
  banner: { js: "/* docs-chat widget. Source: https://github.com/PooyaNikbakht/docs-chat */" },
  plugins: [copyToFrontend],
  logLevel: "warning",
};

if (watch) {
  const ctx = await esbuild.context(options);
  await ctx.watch();
  console.log("widget: watching src/ for changes");
} else {
  await esbuild.build(options);
}
