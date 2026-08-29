import DefaultTheme from "vitepress/theme";
import ComingSoon from "../components/ComingSoon.vue";
import "./custom.css";

export default {
  extends: DefaultTheme,
  enhanceApp(ctx) {
    ctx.app.component("ComingSoon", ComingSoon);
  },
};
