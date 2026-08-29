# VitePress Site Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「清单 md → 单文件 index.html」的 Python 生成器，迁移为以 VitePress 为骨架、可承载多个单项技能深入页、并保住（并重写为 Vue 组件）现有勾选/打分/雷达交互的稳定 MD→站点产出系统。

**Architecture:** 清单 md 仍是唯一事实源；构建期 `tools/build-checklist.mjs` 解析清单 md（+ 深入页 frontmatter）产出 `checklist.json`；VitePress 把 `docs/*.md` 编成多页静态站，交互视图由注册进自定义主题的 Vue 组件消费 `checklist.json` 渲染；进度用 `useProgress` 单例 composable 落 localStorage（沿用旧 key 与旧数据形状）。GitHub Actions 构建部署 Pages，生成物不入库。

**Tech Stack:** Node 22 / VitePress（Vue 3）/ Vitest + @vue/test-utils + jsdom / gray-matter / GitHub Actions（`actions/deploy-pages`）。

**Spec:** `docs/superpowers/specs/2026-08-29-vitepress-migration-design.md`（本计划实现该设计；执行者需同时读设计文档与本计划）

## Global Constraints

- Node 版本：开发/CI 统一 **≥ 22**（本机 v26 可用，CI 用 22）。
- `package.json` 顶层 `"type": "module"`；所有新脚本用 ESM（`.mjs`/`.ts`）。
- 清单源 md 是唯一事实源；HTML 生成物（`index.html`、`dist/`、`checklist.json`）一律**不入库**。
- localStorage 兼容：key 固定 `mj2027-progress-v1`，state 形状 `{ checks, scores, acts, view, side }`（`checks/scores/acts` 为 `{[key]: value}`）。
- 视图模型（`checklist.json`）字段与旧 `const DATA` 完全一致：`docTitle, usage, overview, cards, levels, plan, flags, scoring, evidence, sources, closing`；条目 `{k,t}`；块节点 `{id,name,sub,notes,cutoff,depth,items,subs,type,weight}`。
- SSR/SSG 安全：组件首帧不得触达 `window`/`localStorage`；恢复本地数据只在 `onMounted` 之后。
- 进度聚合口径：块/卡聚合键为 `blk:<id>`、`card:<no>`，全局 `all`，类型 `type:<门票|基础|溢价|转化>`，红旗 `flags`。
- 视觉策略：VitePress 默认主题打底，自定义主题层仅平移旧 CSS 变量语义（四类型色 `--ticket/--base/--premium/--convert`、暗色跟随系统、打印样式）。
- 提交规范：Angular/Conventional Commits，type/scope 英文小写，subject 祈使句小写无句号 ≤50 字符。
- 每个阶段结束是一个可停靠评审点（设计文档第 7 节）。

---

## 阶段 1：脚手架（先"看效果"）

### Task 1: 初始化 VitePress 工程与目录骨架

**Files:**
- Create: `package.json`
- Create: `docs/.vitepress/config.mts`
- Create: `docs/index.md`（占位首页，指向清单）
- Create: `docs/skills/_template.md`（起手模板）
- Create: `docs/skills/welcome.md`（示例深入页，验证布局）
- Move: `2027-programmer-job-skills-checklist.md` → `content/2027-programmer-job-skills-checklist.md`
- Modify: `.gitignore`（追加 VitePress 生成物、把清单源路径与生成命令注释更新）
- Create: `.npmrc`（可选，无则省略）

**Interfaces:**
- Consumes: 无（首任务）
- Produces:
  - npm 脚本 `docs:dev` / `docs:build` / `docs:preview` / `build:data`
  - VitePress `srcDir = docs/`，`base = "/making-jobs/"`
  - 清单源 md 现位于 `content/2027-programmer-job-skills-checklist.md`（阶段 2 脚本从此读）

- [ ] **Step 1: 安装依赖（VitePress + 测试栈 + frontmatter 解析）**

Run:
```bash
cd /Users/dongyiluo/dev/playground/making-jobs
npm init -y >/dev/null
npm install -D vitepress@latest vitest@latest @vue/test-utils@latest jsdom@latest gray-matter@latest
```
Expected: `package.json` 出现 devDependencies：vitepress、vitest、@vue/test-utils、jsdom、gray-matter。

- [ ] **Step 2: 写 `package.json` 脚本与顶层字段**

用下述内容替换 `package.json`（保留已装依赖块不动，仅重写 `type`/`scripts`/`engines`/`private`）：
```json
{
  "name": "making-jobs",
  "private": true,
  "type": "module",
  "engines": { "node": ">=22" },
  "scripts": {
    "build:data": "node tools/build-checklist.mjs",
    "predev": "node tools/build-checklist.mjs",
    "docs:dev": "vitepress dev docs",
    "prebuild": "node tools/build-checklist.mjs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs",
    "test": "vitest run"
  }
}
```
注：`predev`/`prebuild` 引用的 `tools/build-checklist.mjs` 在阶段 2 才创建；本阶段先手动 `npm run docs:dev` 不依赖它——为避免 predev 报错，本步先**注释式留空占位**：把 `predev`/`prebuild` 值临时设为 `echo skip-data`，阶段 2 Task 4 再改回真实命令。

- [ ] **Step 3: 移动清单源 md 到 `content/`**

Run:
```bash
mkdir -p content && git mv 2027-programmer-job-skills-checklist.md content/
```
Expected: 文件出现在 `content/`，git 记录为 rename。

- [ ] **Step 4: 写 `docs/.vitepress/config.mts`**

```ts
import { defineConfig } from "vitepress";

export default defineConfig({
  srcDir: "docs",
  base: "/making-jobs/",
  cleanUrls: true,
  lastUpdated: true,
  title: "2027 程序员求职能力清单",
  description: "AI 时代可验证行为清单 · 可视化",
  head: [["link", { rel: "icon", href: "/making-jobs/favicon.svg" }]],
  vite: {
    // 允许组件 import 构建期生成的 JSON（阶段 2 起产出）
    fs: { allow: [".."] },
  },
  themeConfig: {
    nav: [
      { text: "速览", link: "/" },
      { text: "能力清单", link: "/checklist" },
      { text: "自评打分", link: "/score" },
    ],
    sidebar: "auto",
    search: { provider: "local" },
    outline: true,
    editLink: undefined,
    footer: {
      message: "勾选与打分只保存在本机浏览器。",
      copyright: "由 Markdown 稳定产出 · VitePress",
    },
  },
});
```

- [ ] **Step 5: 写占位首页 `docs/index.md`**

```md
---
layout: home
hero:
  name: "2027 求职能力清单"
  text: "AI 时代可验证行为清单"
  tagline: 门票 / 基础 / 溢价 / 转化 · 五层能力模型
  actions:
    - theme: brand
      text: 打开能力清单
      link: /checklist
    - theme: alt
      text: 自评打分
      link: /score
features:
  - title: 五层能力模型
    details: 工程底座 → AI 协作 → AI 构建 → 判断力 → 信任资本
  - title: 178 项可验证行为
    details: 每条都是能拿出证据的行为，不是标签
  - title: 进度本地保存
    details: 勾选/打分存本机，可导出 JSON 迁移设备
---
```

- [ ] **Step 6: 写清单/打分等页面的最小占位内容（先让 nav 不 404）**

Create `docs/checklist.md`:
```md
# 能力清单

<ComingSoon name="ChecklistBoard" />
```
Create `docs/score.md`:
```md
# 自评打分

<ComingSoon name="ScorePanel" />
```
Create `docs/skills/welcome.md`:
```md
---
title: 深入页示例
checklist: []
---
# 这是一张「单项技能深入页」

本页用来验证 VitePress `doc` 布局：右侧目录、代码高亮、暗色模式、移动端。

## 一个小节

```py
print("深入页就是普通 markdown")
```

未来每个能力块对应一张这样的页面，frontmatter 的 `checklist: ["3.1"]`
会自动把它关联回清单对应块。
```
Create `docs/skills/_template.md`:
```md
---
title: 能力块名称
checklist: []   # 该页覆盖的清单块 id，如 ["3.1", "3.2"]
---
# 标题

## 为什么它进面试

## 核心动作

## 证据怎么准备
```

- [ ] **Step 7: 临时注册 `ComingSoon` 占位组件（阶段 3 会换成真实组件目录）**

Create `docs/.vitepress/theme/index.ts`:
```ts
import DefaultTheme from "vitepress/theme";
import ComingSoon from "../components/ComingSoon.vue";
import "./custom.css";

export default {
  extends: DefaultTheme,
  enhanceApp(ctx: any) {
    ctx.app.component("ComingSoon", ComingSoon);
  },
};
```
Create `docs/.vitepress/components/ComingSoon.vue`:
```vue
<script setup lang="ts">
defineProps<{ name: string }>();
</script>
<template>
  <p class="muted">组件 <code>{{ name }}</code> 将在交互重写阶段接入。</p>
</template>
```
Create `docs/.vitepress/theme/custom.css`:
```css
:root {
  --ticket: #a4570b; --base: #1c56b8; --premium: #6a2fb0; --convert: #0f7264;
}
```

- [ ] **Step 8: 更新 `.gitignore`**

在文件末尾的「index.html 说明」段落之前，追加：
```
# ---------- VitePress 构建产物（不入库） ----------
docs/.vitepress/dist/
docs/.vitepress/cache/
docs/.vitepress/data/checklist.json
```
并把末尾说明段的两行生成命令注释由 `python3 tools/build_web.py` 改为：
```
#   npm run build:data && npm run docs:build   （迁移完成后启用；旧 index.html 仍在对照期保留）
```

- [ ] **Step 9: 本地起服务验证**

Run: `npm run docs:dev`
Expected: 终端出现 `http://localhost:5173/making-jobs/`；浏览器打开看到 hero 首页；nav 进 `/checklist`、`/score` 显示占位文案；进 `skills/welcome` 显示 doc 布局 + 右侧目录 + 可切暗色。**在此停靠点做视觉评审**：满意才继续；不满意在此回退重构。按 Ctrl-C 停服务。

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "chore: scaffold vitepress site with placeholder views"
```

---

## 阶段 2：生成器移植（Python → Node，字节级 diff 验收）

### Task 2: 移植清单解析与视图模型到 Node

**Files:**
- Create: `tools/build-checklist.mjs`
- Test: `tools/__tests__/parse.test.mjs`

**Interfaces:**
- Consumes: `content/2027-programmer-job-skills-checklist.md`
- Produces（导出自 `tools/build-checklist.mjs`）:
  - `parse(text: string): Doc` — 文档树（对应 build_web.py `parse`）
  - `buildViews(doc: Doc): Views` — 视图模型（对应 `build_views`）
  - `refine(v: Views): Views` / `annotate(v: Views): Views`
  - `buildData(srcPath): Views` — 顶层：`refine(buildViews(parse(read(src))) )`
  - `Views` = 上述 Global Constraints 里的 `checklist.json` 结构

- [ ] **Step 1: 写失败测试（对照旧 `index.html` 内嵌 DATA）**

先取旧基线：Run `python3 tools/build_web.py /tmp/baseline.md /tmp/baseline.html 2>/dev/null; sed -n 's/.*const DATA = //; s/;.*//p' tools/build_web.py >/dev/null`（仅说明来源）。更直接：用现仓库根 `index.html` 抽出旧 DATA。

Create `tools/__tests__/parse.test.mjs`:
```js
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { test, expect } from "vitest";
import { buildData } from "../build-checklist.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "../../content/2027-programmer-job-skills-checklist.md");
const BASELINE = JSON.parse(
  readFileSync(resolve(here, "baseline-data.json"), "utf8") // Task 3 生成
);

test("视图模型键齐全", () => {
  const v = buildData(SRC);
  for (const k of ["docTitle","usage","overview","cards","levels","plan","flags","scoring","evidence","sources","closing"])
    expect(v).toHaveProperty(k);
});

test("cards 覆盖 6 个能力层，条目数 178", () => {
  const v = buildData(SRC);
  expect(v.cards.map(c => c.no)).toEqual(["2","3","4","5","6","7"]);
  const count = (n) => n.items.length + n.subs.reduce((a, s) => a + count(s), 0);
  const total = v.cards.reduce((a, c) => a + c.blocks.reduce((x, b) => x + count(b), 0), 0);
  expect(total).toBe(178);
});

test("与旧 Python 基线逐字段一致", () => {
  expect(buildData(SRC)).toEqual(BASELINE);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `npx vitest run tools/__tests__/parse.test.mjs`
Expected: FAIL（`buildData` 未定义 / 无 `baseline-data.json`）。

- [ ] **Step 3: 移植 `parse()`**

`tools/build-checklist.mjs` 中，按 `build_web.py` 的 `esc`/`inline`/`sec_no`/`new_block`/`parse` **逐函数 1:1 移植**为 JS。移植规则（避免 Python↔JS 差异导致 diff 失败，必须照做）：

1. `esc(s)`：`s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")`（Python 的 `str.replace` 替换全部出现，JS 需 `/g`）。
2. `inline(s)`：非贪婪正则与 Python 源一致：`\*\*(.+?)\*\*`、`(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)`、`` `([^`]+)` ``。Node 22 支持 lookbehind，保留。
3. Python `str.strip()` → 自定义 `pyStrip(s)=s.replace(/^[\s\u3000]+|[\s\u3000]+$/g,"")`（对齐 Python 默认空白含全角语义差异；清单源以半角为主，加 `\u3000` 保险）。逐行 `raw.strip()` 用它。
4. `re.match(r"^(附录|…)")` 等定长锚点：Python 变量名含中文（如 `sec_no_v`）不变；但 `parse` 内所有 `holder`/`stack` 逻辑（`deepest()`、`close_table()`、表格分隔行判定 `:?-{2,}:?`、粗体伪标题阈值 `len(name)<=22 && len(rest)<=60`）按行照抄。**`len()` 在 JS 用 `[...s].length`（码点数）近似 Python 的字符数**，清单源无 astral 字符，`.length` 即可，但统一封装 `pylen(s)=[...s].length` 以防未来 emoji。
5. 布尔/空值：Python `[]`/`{}` 保留；`None` → `null`。`build_views` 里 `TYPE_BY_BLOCK.get(id, default)` → `(TYPE_BY_BLOCK[id] ?? default)`。

先只实现 `parse`，`buildData` 暂 `throw new Error("todo: views")`。运行 `npx vitest run ...` 允许 parse 相关断言之外的用例仍红。

- [ ] **Step 4: 移植 `build_views` + `annotate` + `block_count` + `flatten` + `simple_sections` + `refine`**

同法照抄 `build_web.py` 对应函数。要点：
- `build_views` 里读 `by_no.get("8|9|10|A|B|C")`、`LAYER`、`ORDER`、`MODEL_CARD` 常量原样搬为 JS 对象/数组。
- `annotate`/`refine`/`block_count` 保持函数名（导出用 camelCase 亦可，但**导出名固定为** `parse, buildViews, refine, annotate, buildData`）。
- 顶部常量：`SECTION_TYPE`、`TYPE_BY_BLOCK` 与 Python 完全一致。
- `buildData(srcPath)`：`annotate` 在 `refine` 内已被调用（照抄 Python `refine` 末尾调 `annotate`）；`buildData = (src) => refine(buildViews(parse(readFileSync(src,"utf8"))))`。

- [ ] **Step 5: 运行结构测试**

Run: `npx vitest run -t "视图模型|178" tools/__tests__/parse.test.mjs`
Expected: 「视图模型键齐全」「cards 覆盖 6 个能力层」两条 PASS；「与旧 Python 基线」因缺 `baseline-data.json` 仍 SKIP/FAIL（Task 3 处理）。

- [ ] **Step 6: Commit**

```bash
git add tools/build-checklist.mjs tools/__tests__/parse.test.mjs
git commit -m "feat(tools): port checklist parser and view-model to node"
```

### Task 3: 生成旧基线并做字节级 diff（阶段 2 验收闸门）

**Files:**
- Create: `tools/__tests__/baseline-data.json`（由旧 Python 提取，**仅测试用、不入库长期**，加入 `.gitignore` 见 Step 5）

**Interfaces:**
- Consumes: 仓库根现存 `index.html`（旧 Python 产物，含内嵌 `const DATA`）、`content/...md`
- Produces: `tools/__tests__/parse.test.mjs` 全绿

- [ ] **Step 1: 从旧 `index.html` 抽取基线 DATA**

Run:
```bash
cd /Users/dongyiluo/dev/playground/making-jobs
node -e '
const fs=require("fs");
const html=fs.readFileSync("index.html","utf8");
const m=html.match(/const DATA = (.*?);\n/s);
if(!m){console.error("NO DATA");process.exit(1);}
// 反转义 build_web.py 注入时做的 </ -> <\/ 处理
const json=m[1].replace(/<\\\//g,"</");
fs.writeFileSync("tools/__tests__/baseline-data.json", JSON.stringify(JSON.parse(json)));
console.log("baseline bytes:", m[1].length);
'
```
Expected: 打印字节数，`baseline-data.json` 生成。

- [ ] **Step 2: 跑全量一致性测试**

Run: `npx vitest run tools/__tests__/parse.test.mjs`
Expected: 三条全 PASS，尤其「与旧 Python 基线逐字段一致」——`toEqual` 深度比较即字节级字段等价闸门（设计文档第 7 节阶段 2 验收）。若失败，diff 定位：`node -e "..."` 打印首个不同路径，回到 Task 2 Step 3/4 的移植规则修正。

- [ ] **Step 3: 写 `checklist.json` 落盘逻辑并接线 `build-checklist.mjs` 的 main**

在 `build-checklist.mjs` 末尾加：
```js
import { fileURLToPath } from "node:url";
const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (isMain) {
  const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const src = process.argv[2] ? resolve(process.argv[2]) : resolve(ROOT, "content/2027-programmer-job-skills-checklist.md");
  const out = resolve(ROOT, "docs/.vitepress/data/checklist.json");
  const v = buildData(src);
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, JSON.stringify(v, null, 0)); // 紧凑，与旧 payload 同 separators 语义
  const n = v.cards.reduce((a,c)=>a+c.blocks.reduce((x,b)=>x+len(b),0),0);
  console.log(`wrote checklist.json · ${n} items · ${v.levels.cards.length} levels · ${v.plan.phases.length} phases · ${v.flags.items.length} flags`);
}
```
（`len` 复用 Task 2 的 `block_count`；从顶部补 `import { readFileSync, writeFileSync, mkdirSync } from "node:fs"` 与 `import { dirname, resolve } from "node:path"`。）

- [ ] **Step 4: 恢复真实 predev/prebuild**

把 `package.json` 的 `predev`/`prebuild` 从 `echo skip-data` 改回 `"node tools/build-checklist.mjs"`。

- [ ] **Step 5: 基线文件不入库**

`.gitignore` 追加一行 `tools/__tests__/baseline-data.json`（本地生成物，不进 CI 提交）。

- [ ] **Step 6: 验证 CLI 与 dev 前钩子**

Run: `npm run build:data`
Expected: 打印 `wrote checklist.json · 178 items · ...`；`docs/.vitepress/data/checklist.json` 存在。

- [ ] **Step 7: Commit**

```bash
git add tools/build-checklist.mjs package.json .gitignore tools/__tests__/parse.test.mjs
git commit -m "test(tools): gate node port against python baseline data"
```

---

## 阶段 3：交互重写为 Vue 组件

### Task 4: 进度状态层 `useProgress`（localStorage 兼容 + 导出/导入）

**Files:**
- Create: `docs/.vitepress/theme/composables/useProgress.ts`
- Test: `docs/.vitepress/theme/composables/__tests__/useProgress.test.ts`

**Interfaces:**
- Consumes: `checklist.json`（用于聚合键推导 `all` / `type:*`）
- Produces:
  - `useProgress()` 单例，返回 `{ state, checks, scores, acts, setCheck, setScore, setAct, load, reset, exportJSON, importJSON }`
  - `state.view`/`state.side` 字段保留（页面可省略 UI 但数据形状不变，保兼容）
  - 聚合：`aggKeys(data): {all:string[], byType:Record<string,string[]>, blk:Record<string,string[]>, card:Record<string,string[]>, flags:string[]}`

- [ ] **Step 1: 写失败测试**

Create `docs/.vitepress/theme/composables/__tests__/useProgress.test.ts`:
```ts
import { beforeEach, describe, expect, it } from "vitest";
import { __reset, useProgress, aggKeys } from "../useProgress";
import data from "../../../data/checklist.json";

const sample = { /* 手工放 1 个含 items 的极简视图 */ } as any;

beforeEach(() => { localStorage.clear(); __reset(); });

describe("useProgress", () => {
  it("默认读旧 key mj2027-progress-v1", () => {
    localStorage.setItem("mj2027-progress-v1", JSON.stringify({ checks: { "2.1:0": true }, scores: {}, acts: {} }));
    const p = useProgress(); p.load();
    expect(p.state.checks["2.1:0"]).toBe(true);
  });
  it("坏 JSON 静默降级为空态", () => {
    localStorage.setItem("mj2027-progress-v1", "{not json");
    const p = useProgress(); expect(() => p.load()).not.toThrow();
    expect(Object.keys(p.state.checks)).length(0);
  });
  it("导出可被导入还原", () => {
    const p = useProgress(); p.setCheck("9:0", true); p.setScore("a0", 2); p.setAct("a0", "补 MVCC");
    const blob = p.exportJSON();
    localStorage.clear(); __reset();
    const q = useProgress(); q.importJSON(blob);
    expect(q.state.checks["9:0"]).toBe(true);
    expect(q.state.scores.a0).toBe(2);
  });
  it("aggKeys 覆盖 all/type/blk/flags", () => {
    const a = aggKeys(data);
    expect(a.all.length).toBe(178);
    expect(a.byType["门票"].length).toBeGreaterThan(0);
    expect(a.flags.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `npx vitest run docs/.vitepress/theme/composables/__tests__/useProgress.test.ts`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 `useProgress.ts`**

```ts
import { reactive } from "vue";
const KEY = "mj2027-progress-v1";
type Checks = Record<string, boolean>;
interface S { checks: Checks; scores: Record<string, number>; acts: Record<string, string>; view: string; side: string }
const blank = (): S => ({ checks: {}, scores: {}, acts: {}, view: "overview", side: "open" });
let singleton: S | null = null;
export function __reset() { singleton = null; }

export function useProgress() {
  if (!singleton) singleton = reactive(blank()) as S;
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(singleton)); } catch {} };
  return {
    state: singleton,
    load() {
      try { const raw = localStorage.getItem(KEY); if (raw) Object.assign(singleton, JSON.parse(raw)); } catch {}
    },
    setCheck(k: string, v: boolean) { singleton.checks[k] = v; save(); },
    setScore(k: string, v: number) { singleton.scores[k] = v; save(); },
    setAct(k: string, v: string) { singleton.acts[k] = v; save(); },
    reset() { Object.assign(singleton, blank()); save(); },
    exportJSON() { return JSON.stringify(singleton, null, 2); },
    importJSON(text: string) {
      try { const o = JSON.parse(text); if (o && typeof o.checks === "object") { Object.assign(singleton, blank(), o); save(); } } catch {}
    },
  };
}

const collect = (n: any, b: string[]) => { n.items.forEach((i: any) => b.push(i.k)); n.subs.forEach((s: any) => collect(s, b)); return b; };
export function aggKeys(data: any) {
  const all: string[] = [], byType: Record<string, string[]> = { 门票: [], 基础: [], 溢价: [], 转化: [] };
  const blk: Record<string, string[]> = {}, card: Record<string, string[]> = {};
  for (const c of data.cards) card["card:" + c.no] = c.blocks.reduce((a: string[], b: any) => collect(b, a), []);
  const seenT: Record<string, Set<string>> = { 门票: new Set(), 基础: new Set(), 溢价: new Set(), 转化: new Set() };
  for (const c of data.cards) for (const b of c.blocks) {
    const keys = collect(b, []); blk[b.id] = keys; keys.forEach(k => all.push(k));
    (seenT[b.type] ??= new Set()); keys.forEach(k => seenT[b.type].add(k));
  }
  for (const t in seenT) byType[t] = [...seenT[t]];
  const flags = data.flags.items.map((i: any) => i.k);
  // 深入页里 levels/plan 的块也纳入 all（与旧 AGG["all"] 收集范围一致：遍历所有 AGG 键去重）
  data.levels.cards.forEach((c: any) => collect(c, all).forEach(() => {}));
  data.plan.phases.forEach((c: any) => collect(c, all));
  return { all: [...new Set(all)], byType, blk, card, flags };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `npx vitest run docs/.vitepress/theme/composables/__tests__/useProgress.test.ts`
Expected: PASS。（若 `all.length!==178`：说明 levels/plan 里含清单外新 key，回查旧 `init()` 的 `AGG["all"]` 去重逻辑，保证收集范围等价。）

- [ ] **Step 5: Commit**

```bash
git add docs/.vitepress/theme/composables
git commit -m "feat(theme): add useProgress store compatible with legacy v1 key"
```

### Task 5: `ProgressRing` 与 `ChecklistBoard` 组件

**Files:**
- Create: `docs/.vitepress/theme/components/ProgressRing.vue`
- Create: `docs/.vitepress/theme/components/ChecklistBoard.vue`
- Test: `docs/.vitepress/theme/components/__tests__/ChecklistBoard.test.ts`

**Interfaces:**
- Consumes: `checklist.json`、`useProgress`、`aggKeys`
- Produces: 全局注册组件 `ChecklistBoard`（渲染 `data.cards` 全勾选/搜索/类型过滤）、`ProgressRing`（`props: { pct: number }`）

- [ ] **Step 1: 写失败测试**

Create `docs/.vitepress/theme/components/__tests__/ChecklistBoard.test.ts`:
```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach } from "vitest";
import ChecklistBoard from "../ChecklistBoard.vue";
import { __reset, useProgress } from "../../composables/useProgress";

beforeEach(() => { localStorage.clear(); __reset(); });

describe("ChecklistBoard", () => {
  const w = () => mount(ChecklistBoard, { global: { stubs: { ProgressRing: true } } });
  it("渲染 6 张能力卡", () => {
    const wrapper = w();
    expect(wrapper.findAll("[data-card]").length).toBe(6);
  });
  it("点击勾选写入 store", async () => {
    const wrapper = w();
    const box = wrapper.find('input[type=checkbox]');
    await box.setValue(true);
    expect(useProgress().state.checks[box.attributes("data-k")]).toBe(true);
  });
  it("搜索过滤隐藏无匹配块", async () => {
    const wrapper = w();
    await wrapper.find('input[type=search]').setValue("不存在的词zzz");
    expect(wrapper.text()).toContain("没有匹配的条目");
  });
});
```

- [ ] **Step 2: 运行确认失败** — Run: `npx vitest run docs/.vitepress/theme/components/__tests__/ChecklistBoard.test.ts` Expected: FAIL。

- [ ] **Step 3: 写 `ProgressRing.vue`**（平移旧 `.gauge .ring` 的两段 `stroke-dasharray=151`）

```vue
<script setup lang="ts">
const props = defineProps<{ pct: number }>();
const offset = () => 151 - (151 * Math.min(100, Math.max(0, props.pct))) / 100;
</script>
<template>
  <div class="ring" role="img" :aria-label="`总体达成进度 ${pct}%`">
    <svg width="56" height="56" viewBox="0 0 56 56">
      <circle cx="28" cy="28" r="24" fill="none" stroke="var(--vp-c-divider)" stroke-width="6" />
      <circle cx="28" cy="28" r="24" fill="none" stroke="var(--vp-c-brand-1)" stroke-width="6"
        stroke-linecap="round" stroke-dasharray="151" :stroke-dashoffset="offset()"
        style="transition:stroke-dashoffset .4s ease" />
    </svg>
    <div class="ring-val">{{ pct }}%</div>
  </div>
</template>
<style scoped>
.ring{position:relative;width:56px;height:56px}
svg{transform:rotate(-90deg)}
.ring-val{position:absolute;inset:0;display:grid;place-items:center;font-size:13px;font-weight:650}
</style>
```

- [ ] **Step 4: 写 `ChecklistBoard.vue`**

移植旧 `renderList()` + `blockHTML`/`itemHTML`/`progHTML` + `applyFilters`。要点：
- 遍历 `data.cards` → `<article class="card" :data-card="c.no">`；块 `v-for`（含 `subs` 递归子组件 `BlockNode`，或把 `blockHTML` 逻辑写成 `<template>` 内递归）。
- 每个勾选框：`<input type="checkbox" :data-k="it.k" :checked="state.checks[it.k]" @change="setCheck(it.k, ($event.target as HTMLInputElement).checked)">`。
- 搜索框 `input[type=search]` 绑 `q`；状态/类型 chips 绑 `filters.st/ty`；`shown==0` 时显示"没有匹配"。
- 顶部放 `<ProgressRing :pct="overallPct">`，`overallPct = round(all.filter(checked).length / all.length * 100)`（用 `aggKeys(data).all`）。
- 复用 `.item/.blk/.card/.bar` 样式：把旧 `build_web.py` HEAD 里 checklist 相关 CSS 平移进组件 `<style scoped>`（映射到 `--vp-c-*` 变量；四类型 badge 用 Global Constraints 的 `--ticket/--base/--premium/--convert`）。
- 递归块渲染示例（放在同文件 `<script>` 里用一个 `renderBlocks` 递归函数返回节点数组，或拆 `BlockNode.vue` 自引用 `name: 'BlockNode'`）。若拆 `BlockNode.vue`，其测试并入本文件。

- [ ] **Step 5: 运行确认通过** — Run: `npx vitest run docs/.vitepress/theme/components/__tests__/ChecklistBoard.test.ts` Expected: 3 PASS。

- [ ] **Step 6: 注册组件并替换占位页**

`docs/.vitepress/theme/index.ts` 的 `enhanceApp` 内追加注册 `ChecklistBoard`、`ProgressRing`；把 `docs/checklist.md` 的 `<ComingSoon/>` 改为 `<ChecklistBoard />`。

- [ ] **Step 7: 手动验证** — `npm run docs:dev` 打开 `/checklist`：勾选刷新不丢；搜索"MVCC"能过滤；类型 chip 生效。

- [ ] **Step 8: Commit**
```bash
git add docs/.vitepress/theme docs/checklist.md
git commit -m "feat(theme): render checklist as vue board with live progress"
```

### Task 6: `ScorePanel` 组件（打分 + 雷达 + 告警 + 下一步动作）

**Files:**
- Create: `docs/.vitepress/theme/components/ScorePanel.vue`
- Test: `docs/.vitepress/theme/components/__tests__/ScorePanel.test.ts`

**Interfaces:**
- Consumes: `data.scoring`、`data.evidence`、`useProgress`（scores/acts/checks）、`aggKeys`（门票/红旗告警）
- Produces: 组件 `ScorePanel`；导出的纯函数 `weightedTotal(rows, scores)`、`bandFor(score, scoredCount)`、`radarPoints(vals, cx, cy, R)`（供测试直接调用）

- [ ] **Step 1: 写失败测试**

Create `.../ScorePanel.test.ts`:
```ts
import { describe, expect, it, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import ScorePanel, { weightedTotal, bandFor, radarPoints } from "../ScorePanel.vue.js?vue&type=script";
```
> 若 `.vue` 具名导出取纯函数不便：把 `weightedTotal/bandFor/radarPoints` 放 `docs/.vitepress/theme/composables/score.ts`，ScorePanel 从那里 import，测试也 import 该 `score.ts`。**采用后者**（下方 Step 3 在 `score.ts` 定义）。

Create `.../composables/__tests__/score.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { weightedTotal, bandFor, radarPoints } from "../score";
const rows = [
  { k: "a", weight: 40, type: "门票" }, { k: "b", weight: 30, type: "溢价" }, { k: "c", weight: 30, type: "转化" },
];
describe("score math", () => {
  it("无打分返回 0 且 band 提示未打分", () => {
    expect(weightedTotal(rows, {})).toBe(0);
    expect(bandFor(0, 0)).toEqual(["nu", "还没打分"]);
  });
  it("加权总分按已评权重归一", () => {
    expect(weightedTotal(rows, { a: 3, b: 3, c: 3 })).toBeCloseTo(3);
    expect(weightedTotal(rows, { a: 2 })).toBeCloseTo(2);
  });
  it("band 阈值：>=2.4 hi / >=2 mid / else lo", () => {
    expect(bandFor(2.5, 3)[0]).toBe("b-hi");
    expect(bandFor(2.1, 3)[0]).toBe("b-mid");
    expect(bandFor(1.5, 3)[0]).toBe("b-lo");
  });
  it("radarPoints 把 0..3 夹到 0..R 且首点在正上方", () => {
    const pts = radarPoints([3, 0, 0, 0, 0, 0, 0], 100, 100, 90);
    expect(pts[0][1]).toBeCloseTo(10); // 100 - 90
  });
});
```

- [ ] **Step 2: 运行确认失败** — Run: `npx vitest run docs/.vitepress/theme/composables/__tests__/score.test.ts` Expected: FAIL（模块不存在）。

- [ ] **Step 3: 写 `score.ts`**

```ts
export interface Row { k: string; weight: number; type: string; layer?: string; axis?: string }
export const weightedTotal = (rows: Row[], scores: Record<string, number>) => {
  const scored = rows.filter(r => scores[r.k] !== undefined);
  if (!scored.length) return 0;
  const wsum = rows.reduce((a, r) => a + r.weight, 0);
  return rows.reduce((a, r) => a + (scores[r.k] || 0) * r.weight, 0) / wsum;
};
export const bandFor = (w: number, scoredCount: number): [string, string] =>
  !scoredCount ? ["nu", "还没打分"] :
  w >= 2.4 ? ["b-hi", "可以主动进攻好机会"] :
  w >= 2 ? ["b-mid", "边工作边补最弱两项"] :
  ["b-lo", "先进入 90 天计划，别急着海投"];
export const radarPoints = (vals: number[], cx: number, cy: number, R: number) => {
  const n = vals.length;
  return vals.map((v, i) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    const r = (Math.max(0, Math.min(3, v)) / 3) * R;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as [number, number];
  });
};
```

- [ ] **Step 4: 运行确认通过** — Expected: score.test.ts PASS。

- [ ] **Step 5: 写 `ScorePanel.vue`**

移植 `renderScore()` + `segHTML` + `refreshScore()` + `drawRadar`（动画部分按 `prefers-reduced-motion` 保留或简化为 CSS `transition`，**不加新依赖**）。绑定：分段按钮 `@click="setScore(r.k, v)"`、下一动作 `input @input="setAct(r.k, ...)"`、雷达 `<svg>` 用 `radarPoints` + `weightedTotal` + `bandFor` 计算，门票告警读 `aggKeys(data).byType["门票"]` 未勾数、红旗读 `.flags` 命中数。

- [ ] **Step 6: 注册 + 替换占位**

`theme/index.ts` 注册 `ScorePanel`；`docs/score.md` 改为 `<ScorePanel />`。

- [ ] **Step 7: 手动验证** — 打开 `/score`：打分→总分/band/雷达/告警实时变化；刷新不丢；"去看清单"跳 `/checklist`。

- [ ] **Step 8: Commit**
```bash
git add docs/.vitepress/theme docs/score.md
git commit -m "feat(theme): add score panel with radar and ticket alert"
```

### Task 7: 门槛/计划/红旗/来源页 + 导出导入与重置按钮

**Files:**
- Create: `docs/.vitepress/theme/components/{LevelsList,PlanTimeline,FlagsList,SourcesList}.vue`
- Create: `docs/.vitepress/theme/components/DataIO.vue`
- Create: `docs/{levels,plan,flags,sources}.md`

**Interfaces:**
- Consumes: `data.levels/plan/flags/sources/closing/usage`、`useProgress`
- Produces: 4 个静态派生视图组件（红旗可勾选、复用 ChecklistBoard 的 item 勾选样式）+ `DataIO`（导出下载 / 导入文件 / 重置）

- [ ] **Step 1: 写 `DataIO.vue`**

```vue
<script setup lang="ts">
import { useProgress } from "../composables/useProgress";
const p = useProgress();
function download() {
  const url = URL.createObjectURL(new Blob([p.exportJSON()], { type: "application/json" }));
  const a = document.createElement("a");
  a.href = url; a.download = `mj2027-progress-${new Date().toISOString().slice(0, 10)}.json`;
  a.click(); URL.revokeObjectURL(url);
}
function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]; if (!f) return;
  f.text().then(t => p.importJSON(t));
}
function doReset() { if (confirm("清空本机保存的勾选与打分？")) p.reset(); }
</script>
<template>
  <div class="data-io">
    <button @click="download">导出进度</button>
    <label class="import">导入<input type="file" accept="application/json" @change="onFile" hidden></label>
    <button @click="doReset">重置</button>
  </div>
</template>
<style scoped>
.data-io{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.data-io button,.data-io .import{font:inherit;font-size:13px;padding:6px 11px;border-radius:8px;border:1px solid var(--vp-c-divider);background:var(--vp-c-default-soft);cursor:pointer}
</style>
```
> 无 window 触达发生在事件回调内，首帧安全。

- [ ] **Step 2: 写 4 个视图组件**（各自 `import data from "../../data/checklist.json"`）
- `FlagsList.vue`：红旗 items 复用勾选逻辑（命中计数读 `state.checks`），根节点加 `danger` 配色。
- `LevelsList.vue`：移植 `renderLevels`（卡片 + `keyword`/`cutoff`）。
- `PlanTimeline.vue`：移植 `renderPlan`（phase 时间线）。
- `SourcesList.vue`：移植 `renderSources`（sources.items + revisions + closing quote + usage notes），**去掉旧页脚"由 build_web.py 生成"文案**，改为"由 Markdown 经 VitePress 产出"。

- [ ] **Step 3: 写 4 个页面 md**，各含标题 + 对应组件标签；`docs/score.md` 末尾追加 `<DataIO />`，`docs/checklist.md` 顶部追加 `<DataIO />`。

- [ ] **Step 4: 注册全部组件** — `theme/index.ts` 的 `enhanceApp` 注册 `DataIO/FlagsList/LevelsList/PlanTimeline/SourcesList`。

- [ ] **Step 5: 更新 nav** — `config.mts` 的 `themeConfig.nav` 增 `{ text:"门槛", link:"/levels" }`、`{text:"90天计划",link:"/plan"}`、`{text:"红旗",link:"/flags"}`、`{text:"来源",link:"/sources"}`。

- [ ] **Step 6: 对照旧 `index.html` 逐项手动验收**（设计文档第 7 节阶段 3 硬指标）
- [旧浏览器进度继承] 在旧 `index.html` 勾几条 + 打几分（写进 `mj2027-progress-v1`），打开新站 `/checklist`、`/score` 应立即看到同样勾选/分数。
- [导出导入] 导出 JSON → 清 localStorage → 导入 → 完全恢复。
- 其余视图行为与旧页一致。

- [ ] **Step 7: 全量测试 + 构建检查**

Run: `npx vitest run && npm run docs:build`
Expected: 测试全绿；`vitepress build` 无 SSR 报错（证明首帧不触 window）。

- [ ] **Step 8: Commit**
```bash
git add docs/.vitepress/theme docs/*.md
git commit -m "feat(theme): add levels/plan/flags/sources views and data io"
```

---

## 阶段 4：内容模型接线（frontmatter 回链 + 自动侧栏）

### Task 8: skill 页 frontmatter → `checklist.json` 回链 + skills 侧栏生成

**Files:**
- Modify: `tools/build-checklist.mjs`（`buildData` 之后新增 skill 扫描与合并）
- Test: `tools/__tests__/skills.test.mjs`
- Create: `docs/skills/context-engineering.md`（真实示例，替换阶段 1 的 welcome 或并存）

**Interfaces:**
- Consumes: `docs/skills/*.md` 的 frontmatter `checklist: [blockId...]`
- Produces:
  - `buildData(src, skillsDir?)` 增第二参；每个块节点新增可选字段 `link?: string`（指向 `/making-jobs/skills/<file>`）
  - 导出 `scanSkills(dir): {id:string, link:string, title:string}[]`
  - `checklist.json` 顶层新增 `skillSidebar`：按层归组的 `{ layer, items:[{text,link}] }[]`

- [ ] **Step 1: 写失败测试**

Create `tools/__tests__/skills.test.mjs`:
```js
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, expect } from "vitest";
import { scanSkills } from "../build-checklist.mjs";

test("scanSkills 读出 frontmatter 回链", () => {
  const d = mkdtempSync(join(tmpdir(), "sk-"));
  writeFileSync(join(d, "ctx.md"), "---\ntitle: 上下文工程\nchecklist: [\"3.1\",\"3.2\"]\n---\n# x\n");
  writeFileSync(join(d, "_template.md"), "跳过下划线开头\n");
  const got = scanSkills(d);
  expect(got.find(s => s.id === "3.1").link).toContain("/skills/ctx");
  expect(got.some(s => s.file === "_template")).toBe(false);
});
```

- [ ] **Step 2: 运行确认失败** — Expected: FAIL（`scanSkills` 未导出）。

- [ ] **Step 3: 实现 `scanSkills` 与合并**

`tools/build-checklist.mjs` 加：
```js
import matter from "gray-matter";
import { readdirSync } from "node:fs";
export function scanSkills(dir) {
  const out = [];
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".md") || f.startsWith("_")) continue;
    const { data } = matter(readFileSync(join(dir, f), "utf8"));
    const id = f.replace(/\.md$/, "");
    for (const blk of (data.checklist || []))
      out.push({ id: blk, file: id, link: `/making-jobs/skills/${id}`, title: data.title || id });
  }
  return out;
}
```
新增 `attachSkillLinks(views, skills)`：对每个块 id 找到匹配 skill，写 `block.link`；构建 `skillSidebar`（用 `LAYER` 把块 id 前缀数字归到该层，层内去重列 skill）。`buildData` 签名改：
```js
export function buildData(src, skillsDir = resolve(dirname(src), "../docs/skills")) {
  const v = refine(buildViews(parse(readFileSync(src, "utf8"))));
  if (existsSync(skillsDir)) { const s = scanSkills(skillsDir); attachSkillLinks(v, s); v.skillSidebar = buildSidebar(v, s); }
  return v;
}
```
main 调用处传第二参 `resolve(ROOT,"docs/skills")`。

- [ ] **Step 4: 运行确认通过** — Run: `npx vitest run tools/__tests__/skills.test.mjs` Expected: PASS。

- [ ] **Step 5: `ChecklistBoard.vue` 渲染回链**

块标题存在 `blk.link` 时渲染 `<a class="deep-link" :href="blk.link">📖 深入 →</a>`；否则不渲染（按需生长）。

- [ ] **Step 6: `config.mts` 侧栏合并 skillSidebar**

在 config 里 `import data from "../.vitepress/data/checklist.json"`（若构建顺序导致缺失，则改 `sidebar: { "/skills/": "auto" }` 并让 skills 页 `outline` 提供导航；两法择一，测试以"新建一页后侧栏出现"为准）。

- [ ] **Step 7: 写一个真实示例深入页**

Create `docs/skills/context-engineering.md`：frontmatter `checklist: ["3.1"]` + 三段正文。

- [ ] **Step 8: 零代码验证（阶段 4 硬指标）**

Run: `npm run build:data` 后 `npm run docs:dev`
Expected: `/checklist` 块 3.1 标题旁出现"📖 深入 →"，点击进 `/skills/context-engineering`；skills 侧栏自动列出该页。全程无改组件代码。

- [ ] **Step 9: Commit**
```bash
git add tools/build-checklist.mjs docs/skills docs/checklist.md tools/__tests__/skills.test.mjs
git commit -m "feat(content): link skills pages to checklist blocks via frontmatter"
```

---

## 阶段 5：部署与清理

### Task 9: GitHub Actions 部署 Pages

**Files:**
- Create: `.github/workflows/deploy.yml`

**Interfaces:**
- Produces: 每次 push `main` → 构建 VitePress → 发布 Pages（source = GitHub Actions）

- [ ] **Step 1: 写 workflow**

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy VitePress site to Pages
on:
  push: { branches: [main] }
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency: { group: pages, cancel-in-progress: false }
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npm run build:data
      - run: npm run test
      - run: npm run docs:build
      - uses: actions/upload-pages-artifact@v3
        with: { path: docs/.vitepress/dist }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: ${{ steps.out.outputs.page_url }} }
    steps:
      - id: out
        uses: actions/deploy-pages@v4
```
> 仓库需有 `package-lock.json`；若无：`npm install --package-lock-only` 生成并提交。

- [ ] **Step 2: 生成并提交 lockfile**

Run: `npm install --package-lock-only && git add package-lock.json && git commit -m "chore: commit npm lockfile for CI"`

- [ ] **Step 3: 切 Pages source（用户操作一次）**

提示用户：GitHub 仓库 → Settings → Pages → Build and deployment → Source 选 **"GitHub Actions"**。

- [ ] **Step 4: push 并观察 Actions**

Run: `git push -u origin feat/vitepress-site-migration` → 开 PR → 合并 main → Actions 绿 → 线上 `https://richeir.github.io/making-jobs/` 校验：首页/清单/打分/深入页可达、暗色与移动端正常、资源 base 路径 `/making-jobs/` 无 404。

### Task 10: 移除旧 Python 生成器与手维护 index.html

**Files:**
- Delete: `index.html`
- Delete: `tools/build_web.py`
- Modify: `.gitignore`（更新说明段为纯 Node 流程；移除已无意义的 Python 段可保留不动）

**Interfaces:**
- Consumes: 阶段 3、9 验收通过（新站线上正常、旧文件仅作对照已完成）
- Produces: 仓库无手工维护 HTML 生成物（设计文档成功标准 4）

- [ ] **Step 1: 确认对照完成**（设计文档第 7 节：删旧文件前，新站已在阶段 3 逐项通过对照、阶段 9 线上绿）。

- [ ] **Step 2: 删除旧文件**

Run: `git rm index.html tools/build_web.py`

- [ ] **Step 3: 更新 `.gitignore` 末尾说明段**

把「index.html 由 build_web.py 生成…python3 tools/build_web.py」整段替换为：
```
# index.html 与 build_web.py 已退役。站点由 content/*.md + docs/skills/*.md
# 经 VitePress 在 CI 构建部署，生成物（dist/、checklist.json）均不入库。
#   本地预览： npm run docs:dev      本地构建： npm run docs:build
```

- [ ] **Step 4: 本地全量回归**

Run: `npm run build:data && npm run test && npm run docs:build`
Expected: 全绿；`docs/.vitepress/dist/index.html` 生成。

- [ ] **Step 5: Commit + push**
```bash
git add -A
git commit -m "chore: retire python generator and hand-maintained index.html"
git push
```

---

## 自检记录（writing-plans Self-Review）

- **Spec 覆盖**：设计文档 §3 架构→Task1-3；§4 内容模型→Task8；§5 组件/状态→Task4-7；§6 部署→Task9；§7 阶段/验收→各阶段末闸门任务；§2 决策表逐条落地。无遗漏。
- **占位符扫描**：阶段 1 Step 2 的 `echo skip-data` 是**有意的临时态**，Task 3 Step 4 明确回收；无其他 TBD/TODO。
- **类型/命名一致性**：导出名统一 `parse/buildViews/refine/annotate/buildData/scanSkills`；store 统一 `useProgress/aggKeys/setCheck/setScore/setAct/exportJSON/importJSON/reset`；纯函数 `weightedTotal/bandFor/radarPoints` 定义与测试引用一致（置于 `composables/score.ts`）；块回链字段统一 `link`；`checklist.json` 顶层 `skillSidebar` 在 Task8 产、Task8/9 用。
- **旧 key 范围风险**：`aggKeys().all` 是否等于 178 取决于旧 `AGG["all"]` 是否含 levels/plan 的键——Task4 Step4 已内置回查指引（若不等则对齐旧去重范围）。
