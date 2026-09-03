/**
 * Content-integrity guards for the real payload (content md + docs/skills).
 *
 * These catch silent data-loss that the renderers would never complain about:
 *  - a typo'd `checklist:` id in a skill page silently drops its backlink;
 *  - two items sharing a localStorage key silently share one checkbox;
 *  - levels/plan renderers only draw top-level items, so a nested block
 *    there would make its items vanish from the site;
 *  - scoring weights that no longer sum to 100 skew the 0–3 total.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import { readdirSync } from "node:fs";
import matter from "gray-matter";
import { test, expect } from "vitest";
import { buildData } from "../build-checklist.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "../../content/2027-programmer-job-skills-checklist.md");
const SKILLS = resolve(here, "../../docs/skills");
const v = buildData(SRC, SKILLS);

const walk = (n, fn) => {
  fn(n);
  n.subs.forEach((s) => walk(s, fn));
};

test("skill 页 frontmatter 的 checklist id 必须命中清单块（拼错会静默丢回链）", () => {
  const blockIds = new Set();
  for (const c of v.cards) for (const b of c.blocks) walk(b, (n) => blockIds.add(n.id));
  for (const f of readdirSync(SKILLS)) {
    if (!f.endsWith(".md") || f.startsWith("_")) continue;
    const { data } = matter(readFileSync(join(SKILLS, f), "utf8"));
    for (const id of data.checklist || [])
      expect(blockIds.has(id), `docs/skills/${f} → checklist: "${id}" 不存在于清单`).toBe(true);
  }
});

test("条目 key 全局唯一（撞 key = 共享同一个勾选）", () => {
  const seen = new Map();
  const add = (k, where) => {
    expect(seen.has(k), `key "${k}" 同时出现在 ${seen.get(k) ?? "?"} 和 ${where}`).toBe(false);
    seen.set(k, where);
  };
  for (const c of v.cards) for (const b of c.blocks) walk(b, (n) => n.items.forEach((i) => add(i.k, `card ${c.no}`)));
  for (const lv of v.levels.cards) walk(lv, (n) => n.items.forEach((i) => add(i.k, "levels")));
  for (const ph of v.plan.phases) walk(ph, (n) => n.items.forEach((i) => add(i.k, "plan")));
  v.flags.items.forEach((i) => add(i.k, "flags"));
  v.scoring.rows.forEach((r) => add(r.k, "scoring"));
});

test("顶层块 id 在 cards 内唯一（折叠/进度按 id 记账）", () => {
  const ids = v.cards.flatMap((c) => c.blocks.map((b) => b.id));
  expect(new Set(ids).size).toBe(ids.length);
});

test("levels / plan 块无嵌套 subs（渲染器只画顶层 items，嵌套会静默丢条目）", () => {
  const offenders = [
    ...v.levels.cards.filter((n) => n.subs.length).map((n) => n.id),
    ...v.plan.phases.filter((n) => n.subs.length).map((n) => n.id),
  ];
  expect(offenders, `这些块含嵌套子块，LevelsList/PlanTimeline 不渲染 subs: ${offenders}`).toEqual([]);
});

test("打分表权重和为 100，类型与跳转合法", () => {
  expect(v.scoring.rows.length).toBeGreaterThan(0);
  expect(v.scoring.rows.reduce((a, r) => a + r.weight, 0)).toBe(100);
  const cardNos = new Set(v.cards.map((c) => c.no));
  for (const r of v.scoring.rows) {
    expect(["门票", "基础", "溢价", "转化"]).toContain(r.type);
    expect(r.weight).toBeGreaterThan(0);
    expect(cardNos.has((r.link || "").split(".")[0]), `scoring row "${r.axis}" → link "${r.link}" 指向不存在的卡`).toBe(true);
  }
});

test("scoring / evidence / sources 均非空（页面靠它们撑内容）", () => {
  expect(v.evidence.rows.length).toBeGreaterThan(0);
  expect(v.sources.items.length).toBeGreaterThan(0);
  expect(v.flags.items.length).toBeGreaterThan(0);
  expect(v.closing.length).toBeGreaterThan(0);
});
