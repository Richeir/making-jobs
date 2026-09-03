# 加强审计 · 2026-08-30

对 making-jobs（2027 求职清单站点）的一次全面体检：先列出"哪些可以加强"，再说明本轮已落地的部分。每条都附证据位置，按投入产出排序。

## 体检范围与方法

- 通读解析器（`tools/build-checklist.mjs`）、主题全部组件/composables、配置、CI、测试与内容源；
- 实跑 `npm test`（全绿）、`npm run docs:build`（发现真实缺陷）、数据形状抽查（`checklist.json` 逐字段核对）。

## 本轮已落地（全部经 test + typecheck + build 三重验证）

### 1. 修复：清单搜索大小写敏感（真实用户可见 bug）

`itemVisible` 对条目文本做了 `toLowerCase()` 但没做查询侧——搜索框占位符明明写着"如 MVCC"，输入 `MVCC` 却搜不到任何东西（内容里的 MVCC 条目至少 3 条，`content/*.md:96,215` 等）。同时 `ChecklistBoard.vue` 里还有一份手抄的相同过滤逻辑（已经和 `board.ts` 漂移的重复代码），一并合并掉，只保留 `board.ts` 一处。补了大小写回归测试（`ChecklistBoard.test.ts`）。

### 2. 消除构建期 13 条 Vue 警告 + 修复移动端侧栏失效（上游 bug）

`vitepress@1.6.4` 的 `VPSidebar.vue` 写了 `watch([props, navEl], …)`：Vue 3.5 下 props 代理在数组源里是非法 watch source——构建时每个页面 warn 一次（13 页 13 条），而且 watcher 从此只对 `navEl` 响应，**移动端打开侧栏不锁背景滚动、不移焦点**。上游 1.6.4 仍是最新稳定版，2.0 还在 alpha。

新增 `tools/patch-upstream.mjs`（零依赖、幂等、版本漂移时只警告不失败）在 `postinstall` 打补丁。构建输出现在是**零警告**。上游修好后删表项即可，脚本会主动提醒模式失配。

（同类已知问题 `VPSwitchAppearance` aria 滞后已有 `appearanceAria.ts` 运行时兜底，保留。）

### 3. 新门禁：`npm run typecheck`（vue-tsc + tsconfig）

项目此前**没有任何 TypeScript 配置**，组件里的 `data as ChecklistData` 断言全靠自觉。首跑就抓出 4 类真实漂移：

- `ChecklistData.levels.cards/plan.phases` 被标注为 `BlockNode`（含必填 `type`），但解析器的 `annotate()` 根本不给 levels/plan 写 `type` → 拆成 `FlatNode`（可选 type）与 `BlockNode`（卡片区专用）两个类型；
- `BlockNode.weight` 实际产出 `null` 而非缺省（`{门票:15,基础:15}[type] ?? null`），类型是 `number | undefined` → 修正；
- `overview.market` 缺 `notes` 字段；
- `ChecklistData.skillSidebar` 在无 skills 目录时不存在 → 可选；
- `config.mts` 的 `vite: { fs: ... }`——`fs` 在 vite 规范里挂在 `server.fs` 下，顶层写法会被静默忽略（已嵌套修正；数据 JSON 都在 docs/ 下所以行为不变）。

已加入 CI（`build:data → typecheck → test → docs:build`），并显式声明了此前作为幻影依赖使用的 `@vitejs/plugin-vue`。

### 4. 新守护：内容完整性测试（`tools/__tests__/integrity.test.mjs`，6 条）

此前解析器改动会破坏内容但**没有任何测试能发现**的静默数据丢失通道：

- skill 页 frontmatter 写错 `checklist:` id → `attachSkillLinks` 静默忽略、回链消失（现在构建即失败并指明哪个文件哪个 id）；
- 条目 key 冲突 → 两个条目共享同一个 localStorage 勾选；
- levels/plan 出现嵌套子块 → `LevelsList`/`PlanTimeline` 只渲染顶层 `items`，条目会从页面上消失但进度条分母还把它算进去；
- 打分表权重和必须恒等于 100，type/link 必须合法。

当前内容全部通过（说明今天是干净的，从此以后错不进门）。

### 5. 数据新鲜度守护（config 加载期）

`checklist.json` 是构建产物且被组件直接 import。绕过 npm 脚本直接跑 `vitepress build` 的后果原本是：文件缺失时报一个难懂的打包错误，或更糟——**静默发布旧版清单**。现在 config 加载期即检查"存在且不比 content/*.md 旧"，失败信息直接给出该跑的命令（已实测触发与恢复）。

### 6. BASE 路径单一事实源

`/making-jobs/` 此前散落 6 处（config、`scanSkills` 硬编码链接、ScorePanel、HomeProgress、sitemap、og）。新增 `docs/.vitepress/site.js`（含 `.d.ts`）统一导出，其余全部改为 import/引用。已验证重构前后 `checklist.json` 逐字节一致。

### 7. 交互组件测试补齐（ScorePanel / DataIO，10 条）

纯函数层此前已有覆盖，但 DOM 行为没有：新增 `ScorePanel.test.ts`（打分点击入 store、加权总分计算展示、门票告警出现、下一动作持久化、雷达无障碍描述、已评计数）与 `DataIO.test.ts`（导出文件名/内容、导入还原三类状态、非法 JSON 静默忽略、重置需确认且落盘）。顺带给 ScorePanel 行与按钮加了 `data-k`/`data-s` 稳定钩子（测试与调试两用）。

### 8. 旧版保真基线找回并入库

`parse.test.mjs` 的"与旧 Python 基线逐字段一致"长期指向不存在的 `/tmp` 文件、永远 skip。本轮从 git 历史（`6b48e1f^:index.html` 的 `const DATA`）提取退役产物，存为仓库内 fixture（`.gitignore` 对应行移除，来源与再生成方法写进注释），并在测试里支持 `MJ_BASELINE` 覆盖。**实跑结果：Node 解析器与退役 Python 生成器逐字段深度相等——迁移期的保真契约首次被真正验证。**

### 9. 杂项

- 新增 `docs/public/robots.txt`（含 sitemap 声明）；
- README 同步：新脚本、上游补丁说明、CI 顺序。

## 待加强清单（未动，按优先级）

| 优先级 | 项 | 证据 / 说明 |
| --- | --- | --- |
| P1 | **深入页内容缺口**：五层模型里 ④判断力 / ⑤信任资本 / ★求职资产 没有任何深入页（`skillSidebar` 只有 layer 2/3/4），而 7.1–7.4 恰是转化动作最密集区。`docs/skills/_template.md` 已备好，纯内容工作 | `checklist.json.skillSidebar` |
| P2 | **lint/格式化**：代码风格目前靠人肉一致（如 `ScorePanel` 单行模板 vs `FlagsList` 多行）。建议 Biome（一个二进制、vue 支持渐熟）而非全家桶 ESLint | 全局 |
| P2 | **og:image 外链**：分享卡片用 `opengraph.githubassets.com/1/Richeir/making-jobs`，仓库改名/迁移即断，且卡片内容是 repo 封面不是站点。建议构建期生成一张定制卡图放 `docs/public/` | `config.mts` |
| P2 | **e2e 冒烟**：无浏览器级测试；hydration 后 localStorage 读回、暗色切换这类问题单测覆盖不到。Playwright 一条用例（勾选→刷新→仍在）即可兜底。成本中等（CI 装浏览器） | — |
| P2 | **CONTRIBUTING.md**：管线图在 README 有了，但"加一个条目/加一个深入页/加一块视图"的 checklist 式指南没有 | — |
| P3 | **schemaVersion 进 payload**：`useProgress` 的存储键已自带版本（`mj2027-progress-v1`），但 `checklist.json` 没有字段版本；组件与解析器各自演化时缺一个显式对撞点 | `types.ts` |
| P3 | **搜索增强**：清单搜索是子串匹配，同义词（如"死锁/deadlock"）命中不了；数据量小（129 项），可先不做分词，考虑在条目 md 里用隐藏 `<code>` 关键词的技巧或加轻量拼音别名 | `board.ts` |
| P3 | **升级路径**：关注 vitepress 2.x 正式版（Vite 6+/Vue 更严的 watch 规则），届时删除 `patch-upstream.mjs` 表项与 `appearanceAria.ts` 兜底 | — |

## 验证记录

- `npm test`：9 文件 / **49 通过 / 0 跳过**（起点为 31 通过 / 1 恒跳过；新增 18 条，且原恒跳过的保真对比已激活）；
- `npm run typecheck`：0 错误；
- `npm run docs:build`：成功、**零警告**（此前 13 条 Vue warn）；
- 守护实测：touch content md → 直接 build 被拒并给出指令；`build:data` 后恢复；
- 重构回归：BASE 收敛前后 `checklist.json` 深度相等；产物 HTML 中 base 链接抽查通过；Node 解析器 vs 退役 Python 产物：逐字段深度相等。
