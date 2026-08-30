import { defineConfig } from "vitepress";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const SITE = "https://richeir.github.io";
const BASE = "/making-jobs/";
const TITLE = "2027 程序员求职能力清单";
const DESC = "AI 时代可验证行为清单 · 可视化";

// Skills sidebar, derived at config-load time from the generated payload
// (predev/prebuild/CI all run `npm run build:data` before vitepress starts).
// Links there carry the full base prefix; vitepress sidebar links are
// base-relative, so strip it. Falls back to an empty list when the payload
// is missing (e.g. vitepress invoked directly on a fresh clone).
interface SkillGroup {
  layer: string;
  items: { text: string; link: string }[];
}
let skillSidebar: SkillGroup[] = [];
const dataPath = fileURLToPath(new URL("./data/checklist.json", import.meta.url));
if (existsSync(dataPath)) {
  const LAYER_NAMES: Record<string, string> = {
    "2": "① 工程底座",
    "3": "② AI 协作力",
    "4": "③ AI 构建力",
    "5": "④ 判断力",
    "6": "⑤ 信任资本",
    "7": "★ 求职资产",
  };
  const data = JSON.parse(readFileSync(dataPath, "utf8")) as { skillSidebar?: SkillGroup[] };
  skillSidebar = (data.skillSidebar || [])
    .sort((a, b) => a.layer.localeCompare(b.layer))
    .map((g) => ({
      text: LAYER_NAMES[g.layer] ? `📖 深入 · ${LAYER_NAMES[g.layer]}` : "📖 深入页",
      items: g.items.map((i) => ({ text: i.text, link: i.link.slice(BASE.length - 1) })),
    }));
}

// A NODE_ENV=production inherited from the shell pollutes vite dev mode:
// the dev server then injects import.meta.env.DEV=false into client code
// and the dev HTML (which lacks the production theme scripts) misbehaves,
// e.g. the dark/light toggle only applying after a full reload. Builds are
// unaffected either way (vite re-derives NODE_ENV from the mode).
if (process.env.NODE_ENV === "production") delete process.env.NODE_ENV;

export default defineConfig({
  base: BASE,
  srcExclude: ["skills/_*.md", "superpowers/**"],
  cleanUrls: true,
  lastUpdated: true,
  title: TITLE,
  description: DESC,
  sitemap: { hostname: SITE + BASE },
  head: [["link", { rel: "icon", href: BASE + "favicon.svg" }]],
  // Per-page OpenGraph / Twitter cards (vitepress injects none by default).
  // Without og:image, links shared in chat apps render as bare text.
  transformHead({ pageData }) {
    const isHome = pageData.relativePath === "index.md";
    const title = isHome ? TITLE : `${pageData.title} · ${TITLE}`;
    const desc = pageData.description || DESC;
    const url =
      SITE + BASE + pageData.relativePath.replace(/index\.md$/, "").replace(/\.md$/, "");
    const image = `https://opengraph.githubassets.com/1/Richeir/making-jobs`;
    return [
      ["meta", { property: "og:type", content: "website" }],
      ["meta", { property: "og:site_name", content: TITLE }],
      ["meta", { property: "og:title", content: title }],
      ["meta", { property: "og:description", content: desc }],
      ["meta", { property: "og:url", content: url }],
      ["meta", { property: "og:image", content: image }],
      ["meta", { name: "twitter:card", content: "summary_large_image" }],
      ["meta", { name: "twitter:title", content: title }],
      ["meta", { name: "twitter:description", content: desc }],
      ["meta", { name: "twitter:image", content: image }],
    ];
  },
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
    // Note: "auto" is NOT a recognized Sidebar value in vitepress@1.6.4 —
    // getSidebar() treats an unknown object as SidebarMulti and every page
    // silently gets an empty sidebar. Use an explicit multi-sidebar map.
    // Only skill pages get a left nav; single-purpose board pages (checklist,
    // score, …) stay sidebar-less — the top nav already covers them.
    sidebar: {
      "/skills/": [
        { text: "ℹ️ 关于深入页", link: "/skills/welcome" },
        ...skillSidebar,
      ],
    },
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
