import DefaultTheme from "vitepress/theme";
import ComingSoon from "./components/ComingSoon.vue";
import ChecklistBoard from "./components/ChecklistBoard.vue";
import ScorePanel from "./components/ScorePanel.vue";
import DataIO from "./components/DataIO.vue";
import LevelsList from "./components/LevelsList.vue";
import PlanTimeline from "./components/PlanTimeline.vue";
import FlagsList from "./components/FlagsList.vue";
import SourcesList from "./components/SourcesList.vue";
import ProgressRing from "./components/ProgressRing.vue";
import "./custom.css";

export default {
  extends: DefaultTheme,
  enhanceApp(ctx) {
    ctx.app.component("ComingSoon", ComingSoon);
    ctx.app.component("ChecklistBoard", ChecklistBoard);
    ctx.app.component("ScorePanel", ScorePanel);
    ctx.app.component("DataIO", DataIO);
    ctx.app.component("LevelsList", LevelsList);
    ctx.app.component("PlanTimeline", PlanTimeline);
    ctx.app.component("FlagsList", FlagsList);
    ctx.app.component("SourcesList", SourcesList);
    ctx.app.component("ProgressRing", ProgressRing);
  },
};
