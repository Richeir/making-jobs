import DefaultTheme from "vitepress/theme";
import { inBrowser, type Theme } from "vitepress";
import ChecklistBoard from "./components/ChecklistBoard.vue";
import ScorePanel from "./components/ScorePanel.vue";
import DataIO from "./components/DataIO.vue";
import LevelsList from "./components/LevelsList.vue";
import PlanTimeline from "./components/PlanTimeline.vue";
import FlagsList from "./components/FlagsList.vue";
import SourcesList from "./components/SourcesList.vue";
import ProgressRing from "./components/ProgressRing.vue";
import HomeProgress from "./components/HomeProgress.vue";
import { installAppearanceAriaSync } from "./composables/appearanceAria";
import "./custom.css";

const theme: Theme = {
  extends: DefaultTheme,
  enhanceApp(ctx) {
    ctx.app.component("ChecklistBoard", ChecklistBoard);
    ctx.app.component("ScorePanel", ScorePanel);
    ctx.app.component("DataIO", DataIO);
    ctx.app.component("LevelsList", LevelsList);
    ctx.app.component("PlanTimeline", PlanTimeline);
    ctx.app.component("FlagsList", FlagsList);
    ctx.app.component("SourcesList", SourcesList);
    ctx.app.component("ProgressRing", ProgressRing);
    ctx.app.component("HomeProgress", HomeProgress);
    // Keep the appearance switch's aria-checked in sync with <html class>
    // (upstream vitepress@1.6.4 hydrates it stale; see appearanceAria.ts).
    if (inBrowser) installAppearanceAriaSync();
  },
};

export default theme;
