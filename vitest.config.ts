import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    setupFiles: ["docs/.vitepress/theme/composables/__tests__/setup.ts"],
    include: ["tools/__tests__/**/*.test.mjs", "docs/.vitepress/theme/**/__tests__/**/*.test.ts"],
  },
});
