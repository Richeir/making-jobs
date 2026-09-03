/** Pure helpers shared by board components (ported from the legacy page). */
import type { FlatNode, Item } from "../types";

export type { Item };

export type BlockNodeData = FlatNode;

export const plain = (s: string) => String(s).replace(/<[^>]+>/g, "");
export const stripGlyph = (s: string) => s.replace(/^[①②③④⑤]\s*/, "");

/** "名称： rest" -> head part bolded (legacy splitHead, threshold 34 chars) */
export function splitHead(t: string): string {
  const i = t.indexOf("：");
  if (i > 0 && i <= 34) return `<span class="head">${t.slice(0, i)}</span>${t.slice(i)}`;
  return t;
}

export function collectKeys(node: FlatNode): string[] {
  return [...node.items.map((i) => i.k), ...node.subs.flatMap(collectKeys)];
}

export interface Filters {
  q: string;
  st: "all" | "todo" | "done" | "";
  ty: string;
}

export function itemVisible(
  it: Item,
  type: string,
  f: Filters,
  checks: Record<string, boolean>,
): boolean {
  const done = !!checks[it.k];
  // lowercase BOTH sides: the placeholder advertises queries like "MVCC"
  // that only ever appear in differently-cased item text
  return (
    (!f.q || plain(it.t).toLowerCase().includes(f.q.toLowerCase())) &&
    (f.st === "all" || (f.st === "done") === done) &&
    (!f.ty || type === f.ty)
  );
}

export function blockVisible(
  node: FlatNode,
  inheritedType: string,
  f: Filters,
  checks: Record<string, boolean>,
): boolean {
  const type = node.type || inheritedType;
  return (
    node.items.some((i) => itemVisible(i, type, f, checks)) ||
    node.subs.some((s) => blockVisible(s, type, f, checks))
  );
}
