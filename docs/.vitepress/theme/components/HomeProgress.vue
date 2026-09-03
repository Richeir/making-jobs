<script setup lang="ts">
import { computed, onMounted } from "vue";
import data from "../../data/checklist.json";
import { BASE } from "../../site.js";
import type { ChecklistData } from "../types";
import { aggKeys, useProgress } from "../composables/useProgress";
import ProgressRing from "./ProgressRing.vue";

/** Personal progress strip for the home page (layout: home custom slot). */
const { state, load } = useProgress();
onMounted(() => load());

const agg = aggKeys(data as ChecklistData);
const cards = (data as ChecklistData).cards;
const layerPct = (no: string) => {
  const keys = agg.card["card:" + no] ?? [];
  return keys.length ? Math.round((keys.filter((k) => state.checks[k]).length / keys.length) * 100) : 0;
};
const pct = computed(() =>
  agg.all.length ? Math.round((agg.all.filter((k) => state.checks[k]).length / agg.all.length) * 100) : 0,
);
const doneCount = computed(() => agg.all.filter((k) => state.checks[k]).length);
const startHint = computed(() => {
  if (!doneCount.value) return "还没开始？从 🎫 门票项（2.1 闭卷基本功）勾起到第一条为止。";
  const firstTodo = cards
    .map((c) => {
      const keys = agg.card["card:" + c.no] ?? [];
      return { c, todo: keys.filter((k) => !state.checks[k]).length, total: keys.length };
    })
    .find((x) => x.todo > 0);
  if (!firstTodo) return "全部勾完了 —— 去 📊 自评打分做一轮校准。";
  const t = Math.round((firstTodo.total - firstTodo.todo) / firstTodo.total * 100);
  return `下一站：${firstTodo.c.layer} ${firstTodo.c.layerName}（已完成 ${t}%），或去 📊 打分看看短板。`;
});
const started = computed(() => doneCount.value > 0);
</script>
<template>
  <div class="hp">
    <div class="hp-card">
      <ProgressRing :pct="pct" />
      <div class="hp-txt">
        <div class="hp-t">🧭 你的进度：{{ doneCount }} / {{ agg.all.length }} 项</div>
        <div class="hp-s">{{ startHint }}</div>
      </div>
      <a class="hp-go" :href="started ? `${BASE}checklist` : `${BASE}checklist#card-2`">
        {{ started ? "继续清单 →" : "🎫 从门票开始 →" }}
      </a>
    </div>
    <div class="hp-layers">
      <div v-for="c in cards" :key="c.no" class="hp-layer" :data-layer="c.no">
        <span class="hp-dot">{{ c.layer }}</span>
        <span class="hp-nm">{{ c.layerName }}</span>
        <span class="hp-bar"><i :style="{ width: layerPct(c.no) + '%' }"></i></span>
        <span class="hp-pl">{{ layerPct(c.no) }}%</span>
      </div>
    </div>
  </div>
</template>
<style scoped>
.hp { display: grid; gap: 10px; text-align: left; }
.hp-card { display: flex; align-items: center; gap: 14px; padding: 14px 18px; border-radius: 14px; background: var(--vp-c-bg-soft); border: 1px solid var(--vp-c-divider); flex-wrap: wrap; }
.hp-txt { flex: 1; min-width: 200px; }
.hp-t { font-size: 15px; font-weight: 650; }
.hp-s { font-size: 13px; color: var(--vp-c-text-2); margin-top: 2px; }
.hp-go { font-size: 13px; font-weight: 600; color: var(--vp-c-brand-1); text-decoration: none; white-space: nowrap; }
.hp-go:hover { text-decoration: underline; }
.hp-layers { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
.hp-layer { display: flex; align-items: center; gap: 8px; font-size: 12.5px; padding: 7px 10px; border: 1px solid var(--vp-c-divider); border-radius: 10px; background: var(--vp-c-bg); color: var(--vp-c-text-2); }
.hp-dot { font-weight: 650; color: var(--vp-c-text-1); }
.hp-nm { white-space: nowrap; }
.hp-bar { flex: 1; height: 5px; min-width: 24px; border-radius: 999px; background: var(--vp-c-divider); overflow: hidden; }
.hp-bar i { display: block; height: 100%; border-radius: inherit; background: var(--vp-c-brand-1); transition: width 0.35s ease; }
.hp-pl { font-variant-numeric: tabular-nums; }
</style>
