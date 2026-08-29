<script setup lang="ts">
import { computed, onMounted, provide, reactive } from "vue";
import data from "../../data/checklist.json";
import { useProgress, aggKeys } from "../composables/useProgress";
import { blockVisible, type Filters } from "./board";
import BlockNode from "./BlockNode.vue";
import ProgressRing from "./ProgressRing.vue";

const { state, load } = useProgress();
const agg = aggKeys(data as any);
const filters = reactive<Filters>({ q: "", st: "all", ty: "" });
provide("boardFilters", filters);

onMounted(() => load());

const cards = (data as any).cards;
const listTotal = cards.reduce((a: number, c: any) => a + agg.card["card:" + c.no].length, 0);
const TYPES = ["门票", "基础", "溢价", "转化"];
const badgeCls: Record<string, string> = { 门票: "tk", 基础: "bs", 溢价: "pm", 转化: "cv" };

const overallPct = computed(() =>
  agg.all.length ? Math.round((agg.all.filter((k) => state.checks[k]).length / agg.all.length) * 100) : 0,
);
const shownCount = computed(() => {
  let n = 0;
  for (const c of cards) for (const b of c.blocks) n += countVisible(b, b.type);
  return n;
});
function countVisible(node: any, type: string): number {
  const t = node.type || type;
  let n = node.items.filter((i: any) => visibleItem(i, t)).length;
  for (const s of node.subs) n += countVisible(s, t);
  return n;
}
function visibleItem(it: any, type: string) {
  const done = !!state.checks[it.k];
  return (
    (!filters.q || String(it.t).replace(/<[^>]+>/g, "").toLowerCase().includes(filters.q)) &&
    (filters.st === "all" || (filters.st === "done") === done) &&
    (!filters.ty || type === filters.ty)
  );
}
function cardVisible(c: any) {
  return c.blocks.some((b: any) => blockVisible(b, b.type, filters, state.checks));
}
function toggleSt(v: Filters["st"]) {
  filters.st = filters.st === v ? "all" : v;
}
function toggleTy(v: string) {
  filters.ty = filters.ty === v ? "" : v;
}
function cardDone(c: any) {
  const keys = agg.card["card:" + c.no] || [];
  return keys.length ? Math.round((keys.filter((k) => state.checks[k]).length / keys.length) * 100) : 0;
}
</script>
<template>
  <div class="board">
    <div class="toolbar">
      <div class="search">
        <input v-model.trim="filters.q" type="search" placeholder="搜索清单条目，如 上下文 / MVCC / 埋雷 / eval" aria-label="搜索清单条目">
      </div>
      <div class="chips">
        <button v-for="v in [['all', '全部'], ['todo', '未完成'], ['done', '已完成']]" :key="v[0]" class="chip" data-f="st" :data-v="v[0]" :aria-pressed="filters.st === v[0]" @click="toggleSt(v[0] as Filters['st'])">{{ v[1] }}</button>
      </div>
      <div class="chips">
        <button v-for="t in TYPES" :key="t" class="chip tp" data-f="ty" :data-v="t" :class="badgeCls[t]" :aria-pressed="filters.ty === t" @click="toggleTy(t)">{{ t }}</button>
      </div>
      <span class="small muted">
        <template v-if="filters.q || filters.st !== 'all' || filters.ty">显示 {{ shownCount }} / {{ listTotal }} 项</template>
        <template v-else>共 {{ listTotal }} 项 · 勾选状态自动保存在本机</template>
      </span>
      <ProgressRing :pct="overallPct" />
    </div>

    <template v-for="c in cards" :key="c.no">
      <article v-if="cardVisible(c)" class="card" :id="'card-' + c.no" :data-card="c.no">
      <div class="card-hd">
        <span class="dot">{{ c.layer }}</span>
        <h2>{{ c.layerName }} · {{ c.title.replace(/<[^>]+>/g, "").replace(/^[①②③④⑤★]\s*/, "") }}</h2>
        <span class="spacer" style="flex: 1"></span>
        <span v-for="b in c.blocks" :key="b.id" class="badge" :class="badgeCls[b.type]">{{ b.type }}</span>
        <span class="prog"><span class="bar"><i :style="{ width: cardDone(c) + '%' }"></i></span><span class="pl">{{ agg.card["card:" + c.no].filter((k) => state.checks[k]).length }}/{{ agg.card["card:" + c.no].length }}</span></span>
      </div>
      <div class="card-bd">
        <div v-if="(c.notes.length || c.prose.length)" class="notes">
          <p v-for="(n, i) in c.notes.concat(c.prose)" :key="i" v-html="n"></p>
        </div>
        <BlockNode v-for="b in c.blocks" :key="b.id" :node="b" :inherited-type="b.type" />
      </div>
      </article>
    </template>

    <p v-if="shownCount === 0" class="empty">没有匹配的条目</p>
  </div>
</template>
<style scoped>
.board { scroll-margin-top: 66px; }
.toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; padding: 10px 0; position: sticky; top: 0; z-index: 5; background: var(--vp-c-bg); }
.search { display: flex; align-items: center; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); border-radius: 10px; padding: 6px 10px; min-width: 230px; flex: 1; }
.search input { border: 0; outline: 0; background: none; color: inherit; font: inherit; flex: 1; min-width: 60px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { font: inherit; font-size: 12.5px; padding: 5px 10px; border-radius: 999px; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2); cursor: pointer; }
.chip:hover { border-color: var(--vp-c-brand-1); color: var(--vp-c-text-1); }
.chip[aria-pressed="true"] { background: var(--vp-c-text-1); border-color: var(--vp-c-text-1); color: var(--vp-c-bg); font-weight: 600; }
.card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 14px; margin-bottom: 14px; overflow: hidden; scroll-margin-top: 66px; }
.card-hd { display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; flex-wrap: wrap; }
.card-hd h2 { margin: 0; font-size: 16px; line-height: 1.4; }
.card-bd { padding: 2px 16px 14px; border-top: 1px solid var(--vp-c-divider); }
.dot { width: 26px; height: 26px; flex: none; border-radius: 8px; display: grid; place-items: center; font-size: 13px; font-weight: 650; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); }
.badge { display: inline-flex; font-size: 11.5px; font-weight: 600; padding: 2px 8px; border-radius: 999px; border: 1px solid; }
.badge.tk { color: var(--ticket); background: var(--ticket-bg); border-color: var(--ticket-line); }
.badge.bs { color: var(--base); background: var(--base-bg); border-color: var(--base-line); }
.badge.pm { color: var(--premium); background: var(--premium-bg); border-color: var(--premium-line); }
.badge.cv { color: var(--convert); background: var(--convert-bg); border-color: var(--convert-line); }
.prog { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--vp-c-text-2); min-width: 120px; }
.prog .bar { flex: 1; height: 6px; border-radius: 999px; background: var(--vp-c-divider); overflow: hidden; }
.prog .bar i { display: block; height: 100%; border-radius: inherit; background: var(--vp-c-brand-1); transition: width 0.35s ease; }
.notes { margin: 12px 0 0; padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
.empty { padding: 22px 14px; text-align: center; color: var(--vp-c-text-2); font-size: 13.5px; border: 1px dashed var(--vp-c-divider); border-radius: 12px; background: var(--vp-c-bg-alt); }
.small { font-size: 12.5px; }
.muted { color: var(--vp-c-text-2); }
</style>
