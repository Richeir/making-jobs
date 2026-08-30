<script setup lang="ts">
import { computed, onMounted } from "vue";
import data from "../../data/checklist.json";
import { useProgress } from "../composables/useProgress";
import { collectKeys, plain } from "./board";
import ItemRow from "./ItemRow.vue";

const { state, load } = useProgress();
onMounted(() => load());
const lv = (data as any).levels;
const cards = computed(() =>
  lv.cards.map((c: any) => {
    const keys = collectKeys(c);
    return { ...c, keys, done: keys.filter((k) => state.checks[k]).length };
  }),
);
</script>
<template>
  <h2 class="sect">{{ plain(lv.title) }}</h2>
  <div v-if="lv.notes.length" class="notes"><p v-for="(n, i) in lv.notes" :key="i" v-html="n"></p></div>
  <div class="lv">
    <article v-for="c in cards" :key="c.id" class="card">
      <div class="lv-hd">
        <div class="yrs">{{ c.name }}</div>
        <div v-if="c.keyword" class="small muted">关键词：{{ c.keyword }}</div>
      </div>
      <div class="lv-bd">
        <span class="prog"><span class="bar"><i :style="{ width: (c.keys.length ? Math.round(c.done / c.keys.length * 100) : 0) + '%' }"></i></span><span class="pl">{{ c.done }}/{{ c.keys.length }}</span></span>
        <div class="items"><ItemRow v-for="it in c.items" :key="it.k" :it="it" /></div>
      </div>
      <div v-if="c.cutoff" class="cutoff"><b>⛔ 淘汰线</b>{{ c.cutoff }}</div>
    </article>
  </div>
</template>
<style scoped>
.sect { font-size: 13px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--vp-c-text-2); margin: 26px 0 10px; }
.lv { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; align-items: start; }
.card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 14px; overflow: hidden; }
.lv-hd { padding: 13px 15px; border-bottom: 1px solid var(--vp-c-divider); background: var(--vp-c-bg-alt); }
.yrs { font-size: 16px; font-weight: 650; }
.lv-bd { padding: 10px 14px 14px; display: grid; gap: 8px; }
.items { display: grid; gap: 1px; background: var(--vp-c-divider); border: 1px solid var(--vp-c-divider); border-radius: 10px; overflow: hidden; }
.prog { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--vp-c-text-2); }
.prog .bar { flex: 1; height: 6px; border-radius: 999px; background: var(--vp-c-divider); overflow: hidden; }
.prog .bar i { display: block; height: 100%; background: var(--vp-c-brand-1); transition: width 0.35s ease; }
.notes { margin: 0 0 10px; padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
.cutoff { margin: 0 14px 14px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--vp-c-danger-3); background: var(--vp-c-danger-soft); font-size: 13px; color: var(--vp-c-danger-1); }
.cutoff b { display: block; font-size: 12px; margin-bottom: 2px; }
.small { font-size: 12.5px; } .muted { color: var(--vp-c-text-2); }
</style>
