/**
 * Vitest setup: Node >=22.4 exposes an experimental global `localStorage`
 * accessor that is undefined without --localstorage-file, which also blocks
 * vitest from copying jsdom's implementation onto the global. Provide an
 * in-memory stand-in when unresolvable (API subset used by useProgress).
 */
const ls = (globalThis as any).localStorage;
const usable = ls && typeof ls.getItem === "function";
if (!usable) {
  const store = new Map<string, string>();
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
      key: (i: number) => [...store.keys()][i] ?? null,
      get length() {
        return store.size;
      },
    },
  });
}
