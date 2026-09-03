# 2027 程序员求职能力清单

> AI 时代可验证行为清单 · 可视化站点
> 在线：<https://richeir.github.io/making-jobs/>

一份面向 2027 年求职者的能力清单：178 条**可验证的行为**（不是技能标签），配五层能力模型、自评打分、门槛线、90 天计划与红旗清单。勾选与打分只保存在本机浏览器。

## 内容从哪来：一条稳定的产出管线

清单 Markdown 是**唯一事实源**。站点是构建产物，不手工维护。

```
content/2027-programmer-job-skills-checklist.md   ← 唯一事实源（人只改这里）
        │
        │  tools/build-checklist.mjs（构建期解析，含测试守护）
        ▼
docs/.vitepress/data/checklist.json               ← 生成物，不入库
        │
        │  VitePress + 自定义主题（Vue 组件消费 JSON）
        ▼
docs/.vitepress/dist/                             ← GitHub Pages 部署
```

- 深度内容（清单条目、门槛、计划、红旗、打分表、来源）全部改 `content/*.md`；
- 交互式视图（勾选、打分、雷达图、折叠）在 `docs/.vitepress/theme/`；
- 单项技能深入页在 `docs/skills/*.md`，frontmatter 的 `checklist: ["3.1"]` 会自动挂回清单对应块的「📖 深入 →」链接并生成侧边栏。

## 本地开发

```bash
npm install         # postinstall 自动应用已知上游补丁（见下）
npm run docs:dev    # 自动先跑 build:data，起 dev 服务器
npm test            # vitest：解析器 + 组件 + store + 内容完整性守护
npm run typecheck   # vue-tsc：主题组件 / 配置 / 类型定义
npm run docs:build  # 生产构建（先 build:data）
```

`predev` / `prebuild` 钩子会先重新生成 `checklist.json`，改完 md 直接刷新即可。

已知上游 bug 由 `tools/patch-upstream.mjs` 在 postinstall 时以幂等方式修补（当前 1 项：vitepress@1.6.4 的 `VPSidebar` watch 源码非法，Vue 3.5 下构建期告警且移动端侧栏滚动锁定失效）。上游修复后删掉补丁表项即可，脚本会在模式失配时给出提示。

## 部署

GitHub Actions（`.github/workflows/deploy.yml`）：push 到 `main` 时构建并部署到 GitHub Pages；PR 只构建验证。CI 顺序：`build:data → typecheck → test → docs:build`。生成物不入库。

## 目录速览

| 路径 | 作用 |
| --- | --- |
| `content/` | 清单源 md（唯一事实源） |
| `tools/build-checklist.mjs` | md → JSON 解析器 |
| `tools/__tests__/` | 解析器回归测试 |
| `docs/.vitepress/theme/` | 自定义主题：组件、composables、样式 |
| `docs/skills/` | 单项技能深入页（frontmatter 关联清单块） |
| `docs/superpowers/` | 内部设计与迁移计划文档（已排除，不进站点） |

## 许可

ISC
