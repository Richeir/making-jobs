# 设计文档：清单仓库迁移到 VitePress 内容站点系统

日期：2026-08-29
状态：已与用户逐节确认，待最终审阅
前身讨论：Python `tools/build_web.py` → Node.js 的 1:1 移植请求，经 brainstorming 升级为
"多文档、可扩展的 MD→站点 稳定产出系统"（architectural 范围）。

## 1. 背景与目标

仓库现状：`2027-programmer-job-skills-checklist.md`（唯一事实源，178 个可勾选条目、
15 个 ### 小节、17 个 ## 章节）由 `tools/build_web.py` 生成单文件交互页 `index.html`，
提交在仓库根作为 GitHub Pages 入口。

目标：

1. 页面更好看、可持续扩展（不止一个清单页）；
2. 每个能力单项未来可写独立深入 md，系统稳定产出对应页面；
3. 保住并升级现有交互（勾选进度、自评打分、雷达图、搜索过滤）；
4. 构建工具链从 Python 迁到 Node.js。

## 2. 已确认的决策

| 决策点 | 结论 |
|---|---|
| 路线 | 采用现成静态站点生成器（SSG），不自研框架 |
| SSG 选型 | **VitePress**（Vue 生态；默认主题开箱好看；md 内可直接嵌 Vue 组件；中文资料多；产物纯静态） |
| 现有交互总览页 | **重写为框架内 Vue 组件**（非原样嵌入、非砍交互），全站风格与导航统一 |
| 进度存储 | **本地优先**：localStorage + 导出/导入 JSON 备份；云同步明确为后续可选增强，本期不做 |
| 部署 | GitHub Actions 自动构建部署 Pages，不再提交生成物 |
| base 路径 | `/making-jobs/`（project site，推断自 remote；若实际 URL 不同则改 config 一处） |
| 工作方式 | feature 分支 + PR，跟随仓库现有惯例 |

## 3. 总体架构与数据流

原则：清单 md 仍是唯一事实源；页面全部由 VitePress 统一产出。

```
清单源 md（checklist）──构建期──> tools/build-checklist.mjs ──> docs/.vitepress/data/checklist.json
                                                                      │
单项技能深入 md（docs/skills/*.md）──VitePress 编译──┐                  │
                                                     ▼                  ▼
                                    VitePress 站点（静态页 + <ChecklistBoard/> 等组件消费 JSON）
```

- 原 `build_web.py` 的 `parse()` / `build_views()` / `refine()` / `annotate()` 移植为
  Node 脚本，构建期运行一次，**只输出数据 JSON，不再输出整页 HTML**；渲染交给
  VitePress + Vue。
- 单项技能深入页走 VitePress 原生：一个 `skills/*.md` = 一个页面，默认 `doc` 布局。
- 浏览器端不做 md 解析（避免重复解析与脆弱性），数据统一在构建期固化。

### 目录结构

```
making-jobs/
├── content/2027-programmer-job-skills-checklist.md   # 清单源（迁移位置，仍是事实源）
├── docs/                              # VitePress srcDir
│   ├── .vitepress/
│   │   ├── config.mts                 # nav / sidebar / base / 搜索 / 暗色 / sitemap
│   │   ├── data/checklist.json        # 构建期产出（不入库，由脚本生成）
│   │   └── theme/                     # 自定义主题层：注册组件、少量样式覆盖
│   ├── index.md                       # 首页 = 速览 + 能力模型
│   ├── checklist.md                   # 178 项清单（<ChecklistBoard/>）
│   ├── score.md                       # 自评打分（雷达 + 总分 + 下一步行动）
│   ├── levels.md  plan.md  flags.md  sources.md
│   └── skills/                        # 单项技能深入页（用户新增区）
│       ├── _template.md               # 起手模板（不强制）
│       └── *.md
├── tools/build-checklist.mjs          # Node 版解析器（取代 build_web.py）
├── package.json                       # type: module；docs:dev / docs:build / docs:preview / build:data
└── .github/workflows/deploy.yml       # Actions 构建部署 Pages
```

`index.html` 与 `tools/build_web.py` 在阶段 3 对照验收通过后删除（git 历史保留）。

## 4. 内容模型与"清单 ↔ 深入页"关联

- 深入页挂在**能力块**粒度（### 小节 / 粗体伪标题块，约 15–30 个），一个块 = 一页；
  不给 178 个条目逐条建页。
- 回链用 **frontmatter 声明**（唯一新增约定，其余是普通 md）：

  ```yaml
  ---
  title: 上下文工程
  checklist: ["3.1", "3.2"]   # 该页覆盖的清单块 id
  ---
  ```

- 构建期脚本读取全部 skill 页 frontmatter，把链接合并进 `checklist.json`：
  - 清单页：对应块标题旁自动出现"深入 →"；无深入页的块不显示（按需生长，不造空页）；
  - 深入页：顶部自动渲染归属回链（属于哪一层 / 哪个块）。
- 外键沿用原解析器的稳定 id 体系（`2.1`、`3`、`7#0` 等）。约定：frontmatter 只引用
  **块级 id**，不引用条目级 key（`2.1:3` 这类含 `:i` 的会随条目增删漂移）。
- `skills/` 侧栏分组（按五层 ①–⑤+★）由构建脚本从 `checklist.json` + 已存在 skill 页
  自动生成，用户只写 md。

## 5. 交互组件与状态层

### 页面化

原单页 7 视图改为多页（URL 可分享、导航天然）：

```
/            速览 + 能力模型金字塔
/checklist   178 项清单（勾选、搜索、类型过滤、进度）
/score       自评打分（雷达图、总分、band、下一步行动）
/levels  /plan  /flags  /sources
/skills/…    深入页
```

进度跨页共享（同一状态源）。

### 状态层：单个 composable，不引状态库

`useProgress()`（模块级单例）封装：

- **兼容性**：沿用现有 localStorage key `mj2027-progress-v1` 与原数据形状
  （`checks` / `scores` / `acts` / `view`），用户旧进度升级后直接继承；
- **SSR/SSG 安全**：构建预渲染时不可触达 `window`。首帧统一渲染空进度
  （服务端/客户端一致、无 hydration 闪烁），`onMounted` 后恢复本地数据；
- 派生层：块/卡进度（原 `AGG` 聚合）改为对 `checklist.json` 的 computed；
- **导出 / 导入 / 重置**：
  - 导出：state 序列化为 JSON，Blob 触发下载（文件名含日期），零网络；
  - 导入：文件选择 → 校验形状 → 合并 → 提示恢复条数；
  - 重置：二次确认后清空。
  - 这组接口即未来云同步的 seam：后端只需同 shape 的 save/load，前端换 transport。

### 组件清单

| 组件 | 职责 |
|---|---|
| `ChecklistBoard.vue` | 清单主体：cards/blocks/items 渲染、搜索、状态/类型过滤、块内进度 |
| `ScorePanel.vue` | 打分表 + 自绘 SVG 雷达（零图表库）+ 总分 + band + 下一步行动输入 |
| `ProgressRing.vue` | 侧栏总进度环 |

样式策略：VitePress 默认主题打底，自定义主题层做少量覆盖——四类型配色语义
（门票/基础/溢价/转化）、暗色跟随系统、打印样式（清单友好）尽量平移现有 CSS 变量。

## 6. 部署（GitHub Pages）

```
push main → GitHub Actions（Node 22、npm ci、build:data、vitepress build、deploy-pages）→ Pages
```

- 官方 `actions/deploy-pages` workflow（`.github/workflows/deploy.yml`），无 gh-pages 分支；
- `.gitignore` 追加 `docs/.vitepress/dist/`、`docs/.vitepress/cache/`、
  `docs/.vitepress/data/`（生成物不入库）；
- `config.mts`：`base: '/making-jobs/'`（若实际访问 URL 是 user site 域名则改 `'/'`），
  sitemap、lastUpdated、OG 分享卡片用 VitePress 内置项；
- 仓库 Settings → Pages 的 source 需切换为 "GitHub Actions"（用户手动操作一次）；
  切换前先确认 Actions 首次构建为绿，避免部署空窗；
- 本地：`npm run docs:dev`（写 md 热更新预览）、`docs:build` + `docs:preview` 验证产物。

## 7. 实施阶段与验收标准

| 阶段 | 内容 | 验收（硬指标） |
|---|---|---|
| 1 脚手架 | package.json、VitePress、目录结构、config、占位首页 + 示例深入页 | `docs:dev` 可访问；视觉满意度在此关卡决断（不行即止损重构） |
| 2 生成器移植 | `build_web.py` → `tools/build-checklist.mjs` | 同日分别运行两版，Node 输出 JSON 与 Python `build_views+refine+annotate` 结果归一化后 **diff 为空**；178 条目与 id 体系一致 |
| 3 交互重写 | `useProgress` + 三组件 + 6 页面 | 对照旧 `index.html` 逐项通过：旧勾写在 v1 key 中、新站打开直接继承；导出→清站点数据→导入→完全恢复；搜索/过滤/打分/雷达行为与旧页一致 |
| 4 内容模型接线 | frontmatter 回链、自动侧栏、`_template.md` | 零代码验证：新建 skill md + 两行 frontmatter → 清单块出现"深入→"、侧栏自动出现该条目 |
| 5 部署与清理 | Actions workflow、线上验证、删旧文件 | push 后 Actions 绿；线上 `/making-jobs/` 下资源路径正确、主要页面可达无 404；删除 `index.html`、`build_web.py` 后文档/注释同步更新 |

## 8. 风险与缓解

| 风险 | 缓解 |
|---|---|
| Python↔Node 正则 / JSON 序列化差异导致视图模型不一致 | 阶段 2 用机器 diff（非肉眼）作为移植正确性闸门 |
| 旧 localStorage 形状假设出错，用户进度"看起来丢了" | 原 key、原 shape 原样读；阶段 3 用真实旧浏览器数据实测继承 |
| SSR 预渲染触达 `window` 导致构建崩溃或 hydration 闪烁 | 统一"首帧空态 + onMounted 恢复"模式；构建期在 CI 跑 build 验证 |
| 部署源切换期间 Pages 404 | Actions 首绿之后才切 source、才删旧 `index.html` |
| VitePress 视觉不满意 | 阶段 1 停靠点就是视觉评审；不满足则本设计在最小成本处重构 |
| 178 条一次性渲染性能 | 量级很小（旧页同等渲染无压力）；如有需要按块折叠/懒渲染，非本期 |

## 9. 非目标（本期明确不做）

- 云同步 / 账号体系（存储 seam 已预留）；
- 自动生成空的 skill 占位页；
- 多语言 i18n、评论系统、访问统计；
- 对清单 md 书写约定的扩展（解析规则保持等价，不新增语法）。

## 10. 成功标准

1. 用户日常流：`docs/skills/` 下新建 md → commit → push → 线上自动出现新页面，
   且与清单一处定义处处关联；
2. 原 `index.html` 全部功能在新站等价存在且风格统一；
3. 旧浏览器进度无缝继承；导出文件可在另一设备导入恢复；
4. 仓库中不存在手工维护的 HTML 生成物。
