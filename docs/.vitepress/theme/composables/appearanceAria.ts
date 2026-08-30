/**
 * Workaround for an upstream quirk in vitepress@1.6.4's default theme.
 *
 * The inline `check-dark-mode` script applies `.dark` on <html> before
 * hydration, while `VPSwitchAppearance` is server-rendered with
 * `aria-checked="false"`. In production builds Vue does not patch the
 * mismatched attribute during hydration, so the switch's accessible state
 * stays one click behind reality until its component re-renders. This
 * reproduces on a bare VitePress site with no custom theme at all.
 *
 * Fix: keep `aria-checked` on every `.VPSwitchAppearance` in sync with the
 * <html> class — the source of truth for the theme — once before hydration
 * compares attributes, and afterwards whenever the class list changes.
 */

function syncOnce() {
  const dark = document.documentElement.classList.contains("dark");
  document
    .querySelectorAll<HTMLElement>(".VPSwitchAppearance[aria-checked]")
    .forEach((el) => {
      const want = String(dark);
      if (el.getAttribute("aria-checked") !== want) el.setAttribute("aria-checked", want);
    });
}

/** Idempotent, exported for tests: one synchronization pass. */
export const syncAppearanceSwitchAria = syncOnce;

/** Attach the sync pass now and on every <html> class mutation. */
export function installAppearanceAriaSync() {
  syncOnce();
  new MutationObserver(syncOnce).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
}
