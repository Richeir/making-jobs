import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { existsSync } from "node:fs";
import { test, expect } from "vitest";
import { buildData } from "../build-checklist.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "../../content/2027-programmer-job-skills-checklist.md");
const BASELINE_FILE = "/tmp/baseline-data.json"; // Task 3 生成；本任务允许缺失（Ruling: 见 ledger）
const BASELINE = existsSync(BASELINE_FILE) ? JSON.parse(readFileSync(BASELINE_FILE, "utf8")) : null;

test("视图模型键齐全", () => {
  const v = buildData(SRC);
  for (const k of ["docTitle", "usage", "overview", "cards", "levels", "plan", "flags", "scoring", "evidence", "sources", "closing"])
    expect(v).toHaveProperty(k);
});

test("cards 覆盖 6 个能力层，条目数 129", () => {
  const v = buildData(SRC);
  expect(v.cards.map((c) => c.no)).toEqual(["2", "3", "4", "5", "6", "7"]);
  const count = (n) => n.items.length + n.subs.reduce((a, s) => a + count(s), 0);
  const total = v.cards.reduce((a, c) => a + c.blocks.reduce((x, b) => x + count(b), 0), 0);
  expect(total).toBe(129); // Ruling 见 ledger：计划中 178 为全文计数笔误，cards 实为 129
});

test.runIf(BASELINE)("与旧 Python 基线逐字段一致", () => {
  expect(buildData(SRC, "/nonexistent-skills-dir")).toEqual(BASELINE);
});
