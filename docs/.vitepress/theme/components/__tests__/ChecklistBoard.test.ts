import { mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach } from "vitest";
import { __reset, useProgress } from "../../composables/useProgress";
import ChecklistBoard from "../ChecklistBoard.vue";

beforeEach(() => {
  localStorage.clear();
  __reset();
});

describe("ChecklistBoard", () => {
  const w = () => mount(ChecklistBoard);

  it("渲染 6 张能力卡", () => {
    const wrapper = w();
    expect(wrapper.findAll("[data-card]").length).toBe(6);
  });

  it("渲染 129 个清单条目", () => {
    const wrapper = w();
    expect(wrapper.findAll('input[type="checkbox"][data-k]').length).toBe(129);
  });

  it("点击勾选写入 store", async () => {
    const wrapper = w();
    const box = wrapper.find('input[type="checkbox"][data-k]');
    await box.setValue(true);
    expect(useProgress().state.checks[box.attributes("data-k")!]).toBe(true);
  });

  it("勾选状态从 store 回显", async () => {
    const p = useProgress();
    p.setCheck("2.2:0", true);
    const wrapper = w();
    expect((wrapper.find('input[data-k="2.2:0"]').element as HTMLInputElement).checked).toBe(true);
  });

  it("搜索过滤隐藏无匹配项并显示空态", async () => {
    const wrapper = w();
    await wrapper.find('input[type="search"]').setValue("不存在的词zzz");
    expect(wrapper.text()).toContain("没有匹配的条目");
    expect(wrapper.findAll('input[type="checkbox"][data-k]').filter((i) => i.isVisible()).length).toBe(0);
  });

  it("搜索命中的词只留匹配条目", async () => {
    const wrapper = w();
    await wrapper.find('input[type="search"]').setValue("mvcc");
    const visible = wrapper.findAll('input[type="checkbox"][data-k]').filter((i) => i.isVisible());
    expect(visible.length).toBeGreaterThan(0);
    expect(wrapper.findAll("[data-card]").length).toBe(2); // 实据：mvcc 命中 §2（原理）与 §7（简历写法）
  });

  it("搜索大小写不敏感（占位符示例 MVCC 必须能搜到）", async () => {
    const lower = w();
    await lower.find('input[type="search"]').setValue("mvcc");
    const upper = w();
    await upper.find('input[type="search"]').setValue("MVCC");
    const n = (x: typeof lower) =>
      x.findAll('input[type="checkbox"][data-k]').filter((i) => i.isVisible()).length;
    expect(n(upper)).toBeGreaterThan(0);
    expect(n(upper)).toBe(n(lower));
  });

  it("类型 chip 过滤到门票块", async () => {
    const wrapper = w();
    await wrapper.find('button[data-f="ty"][data-v="门票"]').trigger("click");
    const visible = wrapper.findAll('input[type="checkbox"][data-k]').filter((i) => i.isVisible());
    expect(visible.length).toBe(35);
  });

  it("渲染五层导航，含每张卡的跳转锚点", () => {
    const wrapper = w();
    const layers = wrapper.findAll("[data-layer]");
    expect(layers.length).toBe(6); // 六张能力卡（①②③④⑤ + ★求职资产）
    expect(wrapper.find('#card-2').exists()).toBe(true);
  });

  it("折叠某块后其条目不可见，状态写回 store", async () => {
    const wrapper = w();
    await wrapper.find('[data-blk="2.1"] .chev').trigger("click");
    expect(useProgress().state.collapsed).toContain("2.1");
    expect(wrapper.findAll('input[data-k^="2.1#"]').filter((i) => i.isVisible()).length).toBe(0);
  });

  it("折叠状态从 store 回显", async () => {
    useProgress().setCollapsed(["2.1"], true);
    const wrapper = w();
    expect(wrapper.find('[data-blk="2.1"] .chev').attributes("aria-expanded")).toBe("false");
  });

  it("全部折叠 / 全部展开切换顶层块", async () => {
    const wrapper = w();
    const btn = wrapper.find("[data-collapse-all]");
    await btn.trigger("click");
    expect(useProgress().state.collapsed.length).toBeGreaterThan(0);
    await btn.trigger("click");
    expect(useProgress().state.collapsed.length).toBe(0);
  });

  it("搜索时忽略折叠，命中项始终展开", async () => {
    const wrapper = w();
    await wrapper.find('[data-blk="2.1"] .chev').trigger("click"); // 先折叠 2.1
    await wrapper.find('input[type="search"]').setValue("mvcc");
    expect(wrapper.findAll('input[type="checkbox"][data-k]').filter((i) => i.isVisible()).length).toBeGreaterThan(0);
  });
});
