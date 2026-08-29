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
    expect(useProgress().state.checks[box.attributes("data-k")]).toBe(true);
  });

  it("勾选状态从 store 回显", async () => {
    const p = useProgress();
    p.setCheck("2.2:0", true);
    const wrapper = w();
    expect(wrapper.find('input[data-k="2.2:0"]').element.checked).toBe(true);
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

  it("类型 chip 过滤到门票块", async () => {
    const wrapper = w();
    await wrapper.find('button[data-f="ty"][data-v="门票"]').trigger("click");
    const visible = wrapper.findAll('input[type="checkbox"][data-k]').filter((i) => i.isVisible());
    expect(visible.length).toBe(35);
  });
});
