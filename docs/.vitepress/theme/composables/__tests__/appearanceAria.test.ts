import { describe, expect, it } from "vitest";
import { syncAppearanceSwitchAria } from "../appearanceAria";

/**
 * Regression coverage for the upstream vitepress@1.6.4 hydration quirk:
 * the SSR `aria-checked="false"` on the appearance switch must be brought
 * in line with the `.dark` class that the inline check-dark-mode script
 * applied before hydration (otherwise the switch reads one click behind).
 */
describe("syncAppearanceSwitchAria", () => {
  const html = document.documentElement;

  function mountSwitch(aria: string | null) {
    const el = document.createElement("button");
    el.className = "VPSwitchAppearance";
    el.setAttribute("role", "switch");
    if (aria !== null) el.setAttribute("aria-checked", aria);
    document.body.appendChild(el);
    return el;
  }

  it("fixes the stale false when html is dark (pre-hydration pass)", () => {
    html.classList.add("dark");
    const el = mountSwitch("false");
    syncAppearanceSwitchAria();
    expect(el.getAttribute("aria-checked")).toBe("true");
    el.remove();
    html.classList.remove("dark");
  });

  it("fixes the stale true when html is light", () => {
    const el = mountSwitch("true");
    syncAppearanceSwitchAria();
    expect(el.getAttribute("aria-checked")).toBe("false");
    el.remove();
  });

  it("leaves an already-correct switch untouched", () => {
    html.classList.add("dark");
    const el = mountSwitch("true");
    syncAppearanceSwitchAria();
    expect(el.getAttribute("aria-checked")).toBe("true");
    el.remove();
    html.classList.remove("dark");
  });

  it("ignores elements without an aria-checked attribute", () => {
    html.classList.add("dark");
    const el = mountSwitch(null);
    expect(() => syncAppearanceSwitchAria()).not.toThrow();
    expect(el.hasAttribute("aria-checked")).toBe(false);
    el.remove();
    html.classList.remove("dark");
  });
});
