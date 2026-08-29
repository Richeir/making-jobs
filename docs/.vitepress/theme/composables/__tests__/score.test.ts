import { describe, expect, it } from "vitest";
import { weightedTotal, bandFor, radarPoints } from "../score";

const rows = [
  { k: "a", weight: 40, type: "门票" },
  { k: "b", weight: 30, type: "溢价" },
  { k: "c", weight: 30, type: "转化" },
];

describe("score math", () => {
  it("无打分返回 0 且 band 提示未打分", () => {
    expect(weightedTotal(rows, {})).toBe(0);
    expect(bandFor(0, 0)).toEqual(["nu", "还没打分"]);
  });

  it("加权总分按全部权重归一（与旧页公式一致）", () => {
    expect(weightedTotal(rows, { a: 3, b: 3, c: 3 })).toBeCloseTo(3);
    // 只评一项 2 分：2*40/100 = 0.8（旧公式除以全权重和，非已评权重和）
    expect(weightedTotal(rows, { a: 2 })).toBeCloseTo(0.8);
  });

  it("band 阈值：>=2.4 hi / >=2 mid / else lo", () => {
    expect(bandFor(2.5, 3)[0]).toBe("b-hi");
    expect(bandFor(2.4, 3)[0]).toBe("b-hi");
    expect(bandFor(2.1, 3)[0]).toBe("b-mid");
    expect(bandFor(2.0, 3)[0]).toBe("b-mid");
    expect(bandFor(1.5, 3)[0]).toBe("b-lo");
  });

  it("radarPoints 把 0..3 夹到 0..R 且首点在正上方", () => {
    const pts = radarPoints([3, 0, 0, 0, 0, 0, 0], 100, 100, 90);
    expect(pts[0][0]).toBeCloseTo(100);
    expect(pts[0][1]).toBeCloseTo(10); // 100 - 90
    const clamped = radarPoints([99, -5], 0, 0, 10);
    expect(clamped[0][1]).toBeCloseTo(-10); // 3 封顶 -> 满半径向上
    expect(clamped[1][1]).toBeCloseTo(0); // 负值夹 0 -> 圆心
  });
});
