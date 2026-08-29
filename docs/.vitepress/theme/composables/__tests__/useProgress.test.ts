import { beforeEach, describe, expect, it } from "vitest";
import { __reset, useProgress, aggKeys } from "../useProgress";
import data from "../../../data/checklist.json";

beforeEach(() => {
  localStorage.clear();
  __reset();
});

describe("useProgress", () => {
  it("默认读旧 key mj2027-progress-v1", () => {
    localStorage.setItem(
      "mj2027-progress-v1",
      JSON.stringify({ checks: { "2.1:0": true }, scores: {}, acts: {} }),
    );
    const p = useProgress();
    p.load();
    expect(p.state.checks["2.1:0"]).toBe(true);
  });

  it("坏 JSON 静默降级为空态", () => {
    localStorage.setItem("mj2027-progress-v1", "{not json");
    const p = useProgress();
    expect(() => p.load()).not.toThrow();
    expect(Object.keys(p.state.checks).length).toBe(0);
  });

  it("导出可被导入还原", () => {
    const p = useProgress();
    p.setCheck("9:0", true);
    p.setScore("a0", 2);
    p.setAct("a0", "补 MVCC");
    const blob = p.exportJSON();
    localStorage.clear();
    __reset();
    const q = useProgress();
    q.importJSON(blob);
    expect(q.state.checks["9:0"]).toBe(true);
    expect(q.state.scores.a0).toBe(2);
    expect(q.state.acts.a0).toBe("补 MVCC");
  });

  it("重置清空全部进度", () => {
    const p = useProgress();
    p.setCheck("2.2:1", true);
    p.reset();
    expect(Object.keys(p.state.checks).length).toBe(0);
  });

  it("aggKeys 覆盖 all/type/blk/flags，口径与旧页一致", () => {
    const a = aggKeys(data);
    expect(a.all.length).toBe(165); // 清单129 + 门槛17 + 计划19（红旗另计），同旧 AGG["all"] 排除 flags
    expect(a.byType["门票"].length).toBe(35);
    expect(a.byType["基础"].length).toBe(12);
    expect(a.flags.length).toBe(13);
    expect(a.blk["2.1"].length).toBeGreaterThan(0);
    expect(a.card["card:2"].length).toBeGreaterThan(0);
  });
});
