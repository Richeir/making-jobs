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
