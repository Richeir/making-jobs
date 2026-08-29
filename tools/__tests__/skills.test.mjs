import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, expect } from "vitest";
import { scanSkills } from "../build-checklist.mjs";

test("scanSkills 读出 frontmatter 回链，跳过下划线文件", () => {
  const d = mkdtempSync(join(tmpdir(), "sk-"));
  writeFileSync(join(d, "ctx.md"), '---\ntitle: 上下文工程\nchecklist: ["3.1", "3.2"]\n---\n# x\n');
  writeFileSync(join(d, "_template.md"), "跳过下划线开头\n");
  const got = scanSkills(d);
  const hit31 = got.find((s) => s.id === "3.1");
  expect(hit31.link).toContain("/skills/ctx");
  expect(hit31.title).toBe("上下文工程");
  expect(got.find((s) => s.id === "3.2").file).toBe("ctx");
  expect(got.some((s) => s.file === "_template")).toBe(false);
});

test("scanSkills 容忍缺 frontmatter / 空 checklist", () => {
  const d = mkdtempSync(join(tmpdir(), "sk2-"));
  writeFileSync(join(d, "bare.md"), "# 没有 frontmatter\n");
  writeFileSync(join(d, "empty.md"), "---\ntitle: t\n---\n# t\n");
  expect(scanSkills(d)).toEqual([]);
});
