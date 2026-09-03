import { mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach } from "vitest";
import { __reset, useProgress } from "../../composables/useProgress";
import ScorePanel from "../ScorePanel.vue";
import data from "../../../data/checklist.json";

beforeEach(() => {
  localStorage.clear();
  __reset();
});

describe("ScorePanel", () => {
  const w = () => mount(ScorePanel);
  const rows = (data as { scoring: { rows: { k: string }[] } }).scoring.rows;

  it("渲染全部打分行，每行 0–3 四档", () => {
    const wrapper = w();
    expect(wrapper.findAll(".score-row").length).toBe(rows.length);
    expect(wrapper.findAll(".seg button").length).toBe(rows.length * 4);
  });

  it("点击打分 → store 写入、加权总分上屏", async () => {
    const wrapper = w();
    await wrapper.find('.score-row[data-k="a0"] button[data-s="2"]').trigger("click"); // a0 = 2 分
    expect(useProgress().state.scores["a0"]).toBe(2);
    // 总分 = 2*15/100 = 0.30（其余按 0 计入分母）
    expect(wrapper.find(".total .v").text()).toBe("0.30");
  });

  it("门票项低于 2 分时出现告警", async () => {
    const wrapper = w();
    await wrapper.find('.score-row[data-k="a0"] button[data-s="0"]').trigger("click"); // a0（门票）打 0 分
    expect(wrapper.find(".alert").exists()).toBe(true);
    expect(wrapper.text()).toContain("门票告警");
  });

  it("下一动作输入即时持久化", async () => {
    const wrapper = w();
    const inp = wrapper.find('#act-a0');
    await inp.setValue("每天 45 分钟纸笔手撕");
    expect(useProgress().state.acts["a0"]).toBe("每天 45 分钟纸笔手撕");
  });

  it("雷达图无障碍描述含各轴得分", async () => {
    const wrapper = w();
    await wrapper.find('.score-row[data-k="a2"] button[data-s="3"]').trigger("click"); // a2 = 3
    expect(wrapper.find(".sr").text()).toContain("3 分");
  });

  it("已评计数随打分更新", async () => {
    const wrapper = w();
    expect(wrapper.text()).toContain(`已评 0 / ${rows.length} 项`);
    await wrapper.find('.score-row[data-k="a1"] button[data-s="0"]').trigger("click");
    expect(wrapper.text()).toContain(`已评 1 / ${rows.length} 项`);
  });
});
