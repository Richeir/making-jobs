import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

// A NODE_ENV=production inherited from the shell flips vite's resolution
// under the jsdom test environment and stubs out node builtins (e.g.
// `resolve` from node:path becomes undefined), breaking tools/__tests__.
// Tests always run in real Node, so drop the lying marker here.
if (process.env.NODE_ENV === "production") delete process.env.NODE_ENV;

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    setupFiles: ["docs/.vitepress/theme/composables/__tests__/setup.ts"],
    include: ["tools/__tests__/**/*.test.mjs", "docs/.vitepress/theme/**/__tests__/**/*.test.ts"],
  },
});
