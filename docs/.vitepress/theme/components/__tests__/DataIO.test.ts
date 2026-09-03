import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { __reset, useProgress } from "../../composables/useProgress";
import DataIO from "../DataIO.vue";

beforeEach(() => {
  localStorage.clear();
  __reset();
});
afterEach(() => {
  vi.unstubAllGlobals();
});

/** button order in the template: [0] 导出, [1] 重置（导入是 label 不是 button） */
describe("DataIO", () => {
  it("导出：生成带日期的 JSON 下载，内容含当前进度", async () => {
    const p = useProgress();
    p.setCheck("2.1#0:0", true);
    p.setScore("a0", 3);
    const blobs: Blob[] = [];
    vi.stubGlobal("URL", {
      createObjectURL: (b: Blob) => (blobs.push(b), "blob:fake"),
      revokeObjectURL: () => {},
    });
    const wrapper = mount(DataIO);
    const clicks: HTMLAnchorElement[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      clicks.push(this);
    });
    await wrapper.findAll("button")[0].trigger("click");
    expect(clicks.length).toBe(1);
    expect(clicks[0].download).toMatch(/^mj2027-progress-\d{4}-\d{2}-\d{2}\.json$/);
    const text = await blobs[0].text();
    expect(JSON.parse(text).checks["2.1#0:0"]).toBe(true);
    expect(JSON.parse(text).scores.a0).toBe(3);
  });

  it("导入：合法 JSON 还原勾选、打分与折叠", async () => {
    const wrapper = mount(DataIO);
    const payload = JSON.stringify({
      checks: { "2.1#0:0": true },
      scores: { a0: 2 },
      acts: { a0: "x" },
      collapsed: ["3.1"],
    });
    const inp = wrapper.find('input[type="file"]');
    Object.defineProperty(inp.element, "files", {
      value: [{ text: () => Promise.resolve(payload) }],
      configurable: true,
    });
    await inp.trigger("change");
    await flushPromises();
    const st = useProgress().state;
    expect(st.checks["2.1#0:0"]).toBe(true);
    expect(st.scores.a0).toBe(2);
    expect(st.collapsed).toEqual(["3.1"]);
  });

  it("导入：非法 JSON 静默忽略，保持当前状态", async () => {
    const p = useProgress();
    p.setCheck("keep:0", true);
    const wrapper = mount(DataIO);
    const inp = wrapper.find('input[type="file"]');
    Object.defineProperty(inp.element, "files", {
      value: [{ text: () => Promise.resolve("{broken") }],
      configurable: true,
    });
    await inp.trigger("change");
    await flushPromises();
    expect(p.state.checks["keep:0"]).toBe(true);
  });

  it("重置：确认后才清空并落盘", async () => {
    const p = useProgress();
    p.setCheck("2.1#0:0", true);
    vi.stubGlobal("confirm", () => false);
    let wrapper = mount(DataIO);
    await wrapper.findAll("button")[1].trigger("click"); // 取消
    expect(useProgress().state.checks["2.1#0:0"]).toBe(true);

    __reset();
    const q = useProgress();
    q.setCheck("2.1#0:0", true);
    vi.stubGlobal("confirm", () => true);
    wrapper = mount(DataIO);
    await wrapper.findAll("button")[1].trigger("click"); // 确认
    expect(Object.keys(q.state.checks).length).toBe(0);
    expect(JSON.parse(localStorage.getItem("mj2027-progress-v1")!).checks).toEqual({});
  });
});
