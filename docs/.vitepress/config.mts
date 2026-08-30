import { defineConfig } from "vitepress";

// A NODE_ENV=production inherited from the shell pollutes vite dev mode:
// the dev server then injects import.meta.env.DEV=false into client code
// and the dev HTML (which lacks the production theme scripts) misbehaves,
// e.g. the dark/light toggle only applying after a full reload. Builds are
// unaffected either way (vite re-derives NODE_ENV from the mode).
if (process.env.NODE_ENV === "production") delete process.env.NODE_ENV;

export default defineConfig({
  base: "/making-jobs/",
  srcExclude: ["skills/_*.md"],
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
      { text: "🏠 速览", link: "/" },
      { text: "✅ 能力清单", link: "/checklist" },
      { text: "📊 自评打分", link: "/score" },
      { text: "🎯 门槛", link: "/levels" },
      { text: "🗓️ 90天计划", link: "/plan" },
      { text: "🚩 红旗", link: "/flags" },
      { text: "📚 来源", link: "/sources" },
    ],
    sidebar: "auto",
    search: { provider: "local" },
    // 注意：`outline: true` 在 VitePress 1.6.4 会击穿 useLocalNav（布尔值被当数组解构，
    // 挂载时抛 "is not iterable"，连带主题开关 aria-checked 滞后一拍）。
    // [2, 3] 即默认值；需要调整层级时再显式写。
    editLink: undefined,
    footer: {
      message: "勾选与打分只保存在本机浏览器。",
      copyright: "由 Markdown 稳定产出 · VitePress",
    },
  },
});
