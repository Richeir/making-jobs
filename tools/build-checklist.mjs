#!/usr/bin/env node
/**
 * build-checklist.mjs — Node port of tools/build_web.py (parse + view-model layers).
 *
 * Usage (CLI, from Task 3 on):  node tools/build-checklist.mjs [input.md]
 * Emits docs/.vitepress/data/checklist.json for the VitePress theme components.
 *
 * Fidelity contract: the produced view-model must deep-equal the `const DATA`
 * payload embedded in the legacy index.html (gate: tools/__tests__/parse.test.mjs).
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import matter from "gray-matter";

// --------------------------------------------------------------------------- //
// helpers mirroring Python semantics
// --------------------------------------------------------------------------- //
const pylen = (s) => [...s].length; // Python len() counts code points
const pyStrip = (s) => s.replace(/^[ \t\n\r\f\v\u3000]+|[ \t\n\r\f\v\u3000]+$/g, "");
/** Python str.partition(sep) -> always [pre, sep, post] (JS split can't: separator is consumed) */
function pyPartition(s, sep) {
  const i = s.indexOf(sep);
  return i < 0 ? [s, "", ""] : [s.slice(0, i), sep, s.slice(i + sep.length)];
}

export function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function inline(s) {
  s = esc(pyStrip(s));
  s = s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  s = s.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<i>$1</i>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  return s;
}

/** '3. ② AI ...' -> ['3', rest]; '附录 A：...' -> ['A', rest]; else [null, title] */
export function secNo(title) {
  let m = title.match(/^(\d+)\.\s*(.*)$/);
  if (m) return [m[1], m[2]];
  m = title.match(/^附录\s*([A-Z])[:：]\s*(.*)$/);
  if (m) return [m[1], m[2]];
  return [null, title];
}

const newBlock = (name, sub = "", level = 3) => ({
  level, name, sub, notes: [], items: [], cutoff: "", blocks: [],
});

// --------------------------------------------------------------------------- //
// parse: document -> tree (section -> block -> nested block, items)
// --------------------------------------------------------------------------- //
export function parse(text) {
  const doc = { title: "", usage: [], sections: [] };
  let holder = doc; // object we are currently appending to
  let stack = [];   // active block stack inside a section
  let inCode = false;
  let tableBuf = [];

  const deepest = () => (stack.length ? stack[stack.length - 1] : holder);
  const closeTable = () => {
    if (tableBuf.length && holder && Array.isArray(holder.table)) holder.table = tableBuf;
    tableBuf = [];
  };

  for (const raw of text.split("\n")) {
    const s = pyStrip(raw);

    if (inCode) {
      if (s.startsWith("```")) inCode = false;
      else if (holder && Array.isArray(holder.code)) holder.code.push(raw.replace(/[ \t]+$/g, ""));
      continue;
    }
    if (s.startsWith("```")) { inCode = true; continue; }

    if (tableBuf.length && !s.startsWith("|")) closeTable();
    if (s.startsWith("|")) {
      const cells = s.replace(/^\|+|\|+$/g, "").split("|").map((c) => inline(c));
      if (!cells.every((c) => /^:?-{2,}:?$/.test(pyStrip(c)))) tableBuf.push(cells);
      continue;
    }
    if (!s || s === "---") continue;

    // ---- headings -------------------------------------------------------
    if (s.startsWith("## ")) {
      closeTable();
      const title = pyStrip(s.slice(3));
      const [no, rest] = secNo(title);
      holder = {
        no, raw: title, title: rest, notes: [], prose: [],
        ordered: [], bullets: [], table: [], code: [], blocks: [],
      };
      doc.sections.push(holder);
      stack = [];
      continue;
    }
    if (s.startsWith("### ")) {
      const name = s.slice(4).trim().replace(/^\s*\d+\.\d+\s*/, "");
      const blk = newBlock(name, "", 3);
      holder.blocks.push(blk);
      stack = [blk]; // a ### heading always starts a new branch
      continue;
    }
    if (s.startsWith("# ")) {
      if (!doc.title) doc.title = s.slice(2).trim();
      continue;
    }

    if (holder === doc) { // front matter, before the first ##
      if (s.startsWith(">")) doc.usage.push(inline(s.replace(/^>+ ?/g, "").replace(/^ /, "")));
      continue;
    }

    // ---- checklist items ------------------------------------------------
    if (s.startsWith("- [ ]") || s.startsWith("- [x]")) {
      const txt = inline(s.replace(/^-\s+\[[ xX]\]\s*/, ""));
      const target = deepest();
      if (target && Array.isArray(target.items)) target.items.push(txt);
      else {
        const blk = newBlock("", "", 3);
        holder.blocks.push(blk);
        stack = [blk];
        blk.items.push(txt);
      }
      continue;
    }

    // ---- blockquotes / notes --------------------------------------------
    if (s.startsWith(">")) {
      const note = inline(s.replace(/^>+ ?/g, "").replace(/^ /, ""));
      const target = deepest();
      if (target && Array.isArray(target.notes)) target.notes.push(note);
      else holder.notes.push(note);
      continue;
    }

    // ---- bold pseudo headings -------------------------------------------
    const m = s.match(/^\*\*(.+?)\*\*\s*[:：]?\s*(.*)$/);
    if (m) {
      const name = pyStrip(m[1]);
      const rest = pyStrip(m[2]);
      if (pylen(name) <= 22 && pylen(rest) <= 60) {
        while (stack.length && stack[stack.length - 1].level >= 4) stack.pop(); // siblings
        const parent = deepest();
        const blk = newBlock(name, rest, stack.length ? 4 : 3);
        if (parent && Array.isArray(parent.blocks) && parent !== holder) {
          parent.blocks.push(blk);
          stack = [...stack, blk];
        } else {
          holder.blocks.push(blk);
          stack = [blk];
        }
      } else {
        holder.prose.push(inline(s));
      }
      continue;
    }

    // ---- ordered / plain bullets ----------------------------------------
    if (/^\d+\.\s+/.test(s)) {
      holder.ordered.push(inline(s.replace(/^\d+\.\s+/, "")));
      continue;
    }
    if (s.startsWith("- ")) {
      const body = inline(s.slice(2));
      const mb = body.match(/^<b>淘汰线<\/b>\s*[:：]?\s*(.*)$/);
      if (mb) deepest().cutoff = mb[1];
      else holder.bullets.push(body);
      continue;
    }

    holder.prose.push(inline(s));
  }

  closeTable();
  return doc;
}

// --------------------------------------------------------------------------- //
// view model
// --------------------------------------------------------------------------- //
export const TYPE_BY_BLOCK = { "2.1": "门票", "2.2": "基础" };
export const LAYER = {
  "2": ["①", "工程底座"], "3": ["②", "AI 协作力"], "4": ["③", "AI 构建力"],
  "5": ["④", "判断力 / 业务"], "6": ["⑤", "信任资本"], "7": ["★", "求职资产"],
};
export const ORDER = ["2", "3", "4", "5", "6", "7"];
export const SECTION_TYPE = { "2": "溢价", "3": "溢价", "4": "溢价", "5": "溢价", "6": "溢价", "7": "转化" };

const blockId = (no, idx, total) => (total > 1 ? `${no}.${idx + 1}` : no);

export function flatten(blk, prefix, depth = 0) {
  return {
    id: prefix,
    name: blk.name,
    sub: blk.sub,
    notes: blk.notes,
    cutoff: blk.cutoff,
    depth,
    items: blk.items.map((t, i) => ({ k: `${prefix}:${i}`, t })),
    subs: blk.blocks.map((child, i) => flatten(child, `${prefix}#${i}`, depth + 1)),
  };
}

export function buildViews(doc) {
  const byNo = {};
  for (const sec of doc.sections) if (sec.no) byNo[sec.no] = sec;

  // ---------------- overview ----------------
  const quick = doc.sections.find((s) => s.raw.startsWith("30 秒速览")) || {};
  const modelSec = byNo["1"] || {};
  const marketSec = byNo["0"] || {};
  const model = [];
  for (const line of modelSec.code || []) {
    const m = line.match(/^\s*([①②③④⑤])\s+(.+?)\s{2,}(.*)$/);
    if (m) model.push({ code: m[1], name: m[2], desc: m[3] });
  }
  const overview = {
    quick: quick.ordered || [],
    model,
    modelNote: (modelSec.prose || []).concat(modelSec.notes || []),
    market: {
      title: marketSec.title || "",
      rows: marketSec.table || [],
      notes: (marketSec.notes || []).concat(marketSec.prose || []),
    },
  };

  // ---------------- capability checklist ----------------
  const cards = [];
  for (const no of ORDER) {
    const sec = byNo[no];
    if (!sec) continue;
    const blocks = sec.blocks;
    cards.push({
      no,
      title: sec.title,
      layer: (LAYER[no] || ["", ""])[0],
      layerName: (LAYER[no] || ["", ""])[1],
      notes: sec.notes,
      prose: sec.prose,
      blocks: blocks.map((b, i) => flatten(b, blockId(no, i, blocks.length))),
    });
  }
  for (const card of cards)
    for (const blk of card.blocks) {
      blk.type = TYPE_BY_BLOCK[blk.id] || "溢价";
      blk.weight = { 门票: 15, 基础: 15 }[blk.type] ?? null;
    }

  // ---------------- levels / plan / flags ----------------
  const simpleSections = (nos) => {
    const out = [];
    for (const no of nos) {
      const sec = byNo[no];
      if (!sec) continue;
      sec.blocks.forEach((b, i) => out.push(flatten(b, `s${no}b${i}`)));
    }
    return out;
  };
  const levelsSec = byNo["8"] || {};
  const levels = {
    title: levelsSec.title || "",
    notes: (levelsSec.prose || []).concat(levelsSec.notes || []),
    cards: simpleSections(["8"]),
  };
  const planSec = byNo["9"] || {};
  const plan = {
    title: planSec.title || "",
    notes: (planSec.prose || []).concat(planSec.notes || []),
    phases: simpleSections(["9"]),
  };
  const flagsSec = byNo["10"] || {};
  const flags = {
    title: flagsSec.title || "",
    notes: (flagsSec.prose || []).concat(flagsSec.notes || []),
    items: (flagsSec.blocks || []).flatMap((b) => b.items).map((t, i) => ({ k: `f${i}`, t })),
  };

  // ---------------- appendix A: score sheet ----------------
  const appA = byNo["A"] || {};
  const rows = (appA.table || []).filter((r) => r && !r[0].includes("合计"));
  const scoreRows = [];
  for (const r of rows.slice(1)) {
    if (r.length < 3) continue;
    const w = r[2].match(/(\d+)\s*%/);
    scoreRows.push({
      k: `a${scoreRows.length}`,
      layer: r[0],
      axis: r[0].replace(/<[^>]+>/g, "").split("（")[0].trim(),
      type: r[1].replace(/<[^>]+>/g, ""),
      weight: w ? Number(w[1]) : 0,
    });
  }
  const scoring = {
    title: appA.title || "",
    rows: scoreRows,
    prose: appA.prose || [],
    legend: appA.bullets || [],
    notes: appA.notes || [],
  };

  // ---------------- appendix B: evidence ----------------
  const appB = byNo["B"] || {};
  const brows = appB.table || [];
  const evidence = {
    title: appB.title || "",
    rows: brows.length > 1 ? brows.slice(1) : [],
    notes: (appB.prose || []).concat(appB.notes || []),
  };

  // ---------------- appendix C: sources ----------------
  const appC = byNo["C"] || {};
  const cnotes = appC.notes || [];
  const revisions = cnotes.filter((n) => n.startsWith("修订说明"));
  const closing = cnotes.find((n) => !n.startsWith("修订说明")) || "";
  const sources = {
    title: appC.title || "",
    items: appC.bullets || [],
    revisions,
  };

  return {
    docTitle: doc.title,
    usage: doc.usage,
    overview,
    cards,
    levels,
    plan,
    flags,
    scoring,
    evidence,
    sources,
    closing,
  };
}

export function blockCount(node) {
  return node.subs.reduce((a, c) => a + c.items.length + blockCount(c), 0);
}

export function annotate(v) {
  const rec = (node, t) => {
    node.type = node.type || t;
    for (const c of node.subs) rec(c, t);
  };
  for (const card of v.cards) {
    for (const blk of card.blocks) {
      blk.type = TYPE_BY_BLOCK[blk.id] || SECTION_TYPE[card.no] || "溢价";
      rec(blk, blk.type);
    }
    card.total = card.blocks.reduce((a, b) => a + b.items.length + blockCount(b), 0);
  }
  return v;
}

export function refine(v) {
  for (const card of v.levels.cards) {
    const [name, _, kw] = pyPartition(card.name, "（关键词");
    card.name = pyStrip(name);
    card.keyword = kw ? kw.replace(/）\s*$/, "").replace(/^[:：]\s*/, "").trim() : "";
    card.years = card.name.split("（")[0].trim();
  }
  for (const ph of v.plan.phases) {
    const [week, _, rest] = pyPartition(ph.name, "：");
    ph.week = week.trim();
    ph.name = (rest.trim() || week.trim());
  }
  const link = { "①a": "2.1", "①b": "2.2", "②": "3.1", "③": "4", "④": "5", "⑤": "6" };
  for (const row of v.scoring.rows) {
    const first = row.axis ? (row.axis.split(" ")[0] ?? "") : "";
    row.link = link[first] ?? "7.1";
  }
  annotate(v);
  return v;
}

export function buildData(src, skillsDir = null) {
  const v = refine(buildViews(parse(readFileSync(src, "utf8"))));
  const dir = skillsDir || resolve(dirname(resolve(src)), "..", "docs", "skills");
  if (existsSync(dir)) {
    const skills = scanSkills(dir);
    attachSkillLinks(v, skills);
    v.skillSidebar = buildSkillSidebar(skills);
  }
  return v;
}

// --------------------------------------------------------------------------- //
// skill pages: frontmatter `checklist: ["3.1"]` -> backlinks + sidebar
// --------------------------------------------------------------------------- //
export function scanSkills(dir) {
  const out = [];
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".md") || f.startsWith("_")) continue;
    const { data } = matter(readFileSync(join(dir, f), "utf8"));
    const file = f.replace(/\.md$/, "");
    for (const blk of data.checklist || [])
      out.push({ id: blk, file, link: `/making-jobs/skills/${file}`, title: data.title || file });
  }
  return out;
}

export function attachSkillLinks(v, skills) {
  const byId = {};
  for (const s of skills) (byId[s.id] ??= []).push(s);
  const rec = (n) => {
    const hits = byId[n.id];
    if (hits && hits.length) n.link = hits[0].link; // first page wins; deterministic by file scan order
    n.subs.forEach(rec);
  };
  for (const c of v.cards) c.blocks.forEach(rec);
  return v;
}

export function buildSkillSidebar(skills) {
  // group by layer (block id leading digit), dedupe per file
  const groups = {};
  for (const s of skills) {
    const layer = /^\d+/.exec(s.id)?.[0] || "7";
    (groups[layer] ??= { layer, items: [], seen: new Set() });
    if (!groups[layer].seen.has(s.file)) {
      groups[layer].seen.add(s.file);
      groups[layer].items.push({ text: s.title, link: s.link });
    }
  }
  return Object.values(groups).map(({ layer, items }) => ({ layer, items }));
}

// --------------------------------------------------------------------------- //
// CLI: write docs/.vitepress/data/checklist.json
// --------------------------------------------------------------------------- //
const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const src = process.argv[2] ? resolve(process.argv[2]) : resolve(ROOT, "content/2027-programmer-job-skills-checklist.md");
  const out = resolve(ROOT, "docs/.vitepress/data/checklist.json");
  const v = buildData(src, resolve(ROOT, "docs/skills"));
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, JSON.stringify(v)); // 紧凑输出，与旧 payload 的 separators 语义一致
  const len = (n) => n.items.length + n.subs.reduce((a, s) => a + len(s), 0);
  const n = v.cards.reduce((a, c) => a + c.blocks.reduce((x, b) => x + len(b), 0), 0);
  console.log(`wrote checklist.json · ${n} items · ${v.levels.cards.length} levels · ${v.plan.phases.length} phases · ${v.flags.items.length} flags`);
}

