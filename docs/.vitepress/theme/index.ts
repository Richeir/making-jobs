import DefaultTheme from "vitepress/theme";
import ComingSoon from "./components/ComingSoon.vue";
import ChecklistBoard from "./components/ChecklistBoard.vue";
import ProgressRing from "./components/ProgressRing.vue";
import "./custom.css";

export default {
  extends: DefaultTheme,
  enhanceApp(ctx) {
    ctx.app.component("ComingSoon", ComingSoon);
    ctx.app.component("ChecklistBoard", ChecklistBoard);
    ctx.app.component("ProgressRing", ProgressRing);
  },
};
