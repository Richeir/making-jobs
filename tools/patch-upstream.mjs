#!/usr/bin/env node
/**
 * patch-upstream.mjs — idempotent micro-patches for known upstream bugs in
 * pinned dependencies, run from `postinstall` (and safe to run by hand:
 * `npm run patch:upstream`).
 *
 * Each patch declares the exact text it replaces. If the installed file no
 * longer matches (dependency bumped / fixed upstream), we WARN and skip —
 * never fail the install — so the list here is also a to-do of things to
 * delete once upstream ships the fix.
 *
 * Patches:
 *  1. vitepress@1.6.4 VPSidebar: `watch([props, navEl], …)` passes the raw
 *     props proxy inside a watch source array. Vue 3.5 rejects it
 *     ("Invalid watch source: Proxy({ open: false })" — printed once per
 *     page during `vitepress build`) and the watcher then only fires on
 *     navEl, so opening the mobile sidebar neither scroll-locks the body
 *     nor moves focus. Fixed by watching `() => props.open` instead.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const PATCHES = [
  {
    id: "vitepress@1.6.4 · VPSidebar watch props",
    expectVersion: "1.6.4",
    pkg: "vitepress",
    file: "dist/client/theme-default/components/VPSidebar.vue",
    find: "watch(\n  [props, navEl],",
    replace:
      "watch(\n  // patched by tools/patch-upstream.mjs: raw props proxy is an invalid\n  // watch source under Vue 3.5 (see the script header for the full story)\n  [() => props.open, navEl],",
  },
];

let applied = 0;
for (const p of PATCHES) {
  const pkgDir = resolve(ROOT, "node_modules", p.pkg);
  const target = resolve(pkgDir, p.file);
  if (!existsSync(target)) {
    console.warn(`[patch-upstream] skip ${p.id}: ${p.pkg}/${p.file} not found`);
    continue;
  }
  const version = JSON.parse(readFileSync(resolve(pkgDir, "package.json"), "utf8")).version;
  const src = readFileSync(target, "utf8");
  if (src.includes(p.replace)) {
    applied++; // already patched (postinstall ran twice / manual run)
    continue;
  }
  if (!src.includes(p.find)) {
    console.warn(
      `[patch-upstream] STALE ${p.id}: pattern not found in ${p.pkg}@${version}. ` +
        `Upstream may have fixed it — delete the entry from tools/patch-upstream.mjs.`,
    );
    continue;
  }
  if (version !== p.expectVersion) {
    console.warn(
      `[patch-upstream] NOTE ${p.id}: applying to ${p.pkg}@${version} (patch authored for ${p.expectVersion}) — verify behavior.`,
    );
  }
  writeFileSync(target, src.replace(p.find, p.replace));
  applied++;
  console.log(`[patch-upstream] applied ${p.id}`);
}
if (applied === PATCHES.length) console.log(`[patch-upstream] all ${applied} patch(es) in place`);
