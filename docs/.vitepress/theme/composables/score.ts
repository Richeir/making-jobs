export interface Row {
  k: string;
  weight: number;
  type: string;
  layer?: string;
  axis?: string;
}

/** Legacy parity: numerator counts unscored rows as 0, denominator is the FULL weight sum. */
export const weightedTotal = (rows: Row[], scores: Record<string, number>) => {
  const scored = rows.filter((r) => scores[r.k] !== undefined);
  if (!scored.length) return 0;
  const wsum = rows.reduce((a, r) => a + r.weight, 0);
  return rows.reduce((a, r) => a + (scores[r.k] || 0) * r.weight, 0) / wsum;
};

export const bandFor = (w: number, scoredCount: number): [string, string] =>
  !scoredCount
    ? ["nu", "还没打分"]
    : w >= 2.4
      ? ["b-hi", "可以主动进攻好机会"]
      : w >= 2
        ? ["b-mid", "边工作边补最弱两项"]
        : ["b-lo", "先进入 90 天计划，别急着海投"];

export const radarPoints = (vals: number[], cx: number, cy: number, R: number) => {
  const n = vals.length;
  return vals.map((v, i) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    const r = (Math.max(0, Math.min(3, v)) / 3) * R;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as [number, number];
  });
};

export const pathOf = (pts: [number, number][]) =>
  pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ") + "Z";
