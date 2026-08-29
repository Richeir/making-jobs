<script setup lang="ts">
import { computed, onMounted } from "vue";
import data from "../../data/checklist.json";
import { useProgress } from "../composables/useProgress";
import { collectKeys, plain } from "./board";
import ItemRow from "./ItemRow.vue";

const { state, load } = useProgress();
onMounted(() => load());
const pl = (data as any).plan;
const phases = computed(() =>
  pl.phases.map((p: any) => {
    const keys = collectKeys(p);
    return { ...p, keys, done: keys.filter((k) => state.checks[k]).length };
  }),
);
</script>
<template>
  <h2 class="sect">{{ plain(pl.title) }}</h2>
  <div v-if="pl.notes.length" class="notes"><p v-for="(n, i) in pl.notes" :key="i" v-html="n"></p></div>
  <div class="card"><div class="plan">
    <div v-for="p in phases" :key="p.id" class="phase">
      <div class="when">
        <div class="w">{{ p.week }}</div>
        <div class="t">{{ p.name }}</div>
        <span class="prog"><span class="bar"><i :style="{ width: (p.keys.length ? Math.round(p.done / p.keys.length * 100) : 0) + '%' }"></i></span><span class="pl">{{ p.done }}/{{ p.keys.length }}</span></span>
      </div>
      <div>
        <div class="items"><ItemRow v-for="it in p.items" :key="it.k" :it="it" /></div>
        <div v-if="p.notes.length" class="notes" style="margin-top: 8px"><p v-for="(n, i) in p.notes" :key="i" v-html="n"></p></div>
      </div>
    </div>
  </div></div>
</template>
<style scoped>
.sect { font-size: 13px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--vp-c-text-2); margin: 26px 0 10px; }
.card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 14px; }
.plan { padding: 6px 16px 14px; }
.phase { display: grid; grid-template-columns: 150px minmax(0, 1fr); gap: 14px; padding: 14px 0; border-top: 1px solid var(--vp-c-divider); }
.phase:first-child { border-top: 0; }
@media (max-width: 640px) { .phase { grid-template-columns: 1fr; } }
.when { position: relative; padding-right: 14px; display: grid; gap: 4px; }
.when .w { font-size: 12px; color: var(--vp-c-text-2); letter-spacing: 0.04em; }
.when .t { font-size: 14.5px; font-weight: 650; }
.when::after { content: ""; position: absolute; right: -8px; top: 10px; width: 9px; height: 9px; border-radius: 50%; background: var(--vp-c-brand-1); box-shadow: 0 0 0 4px var(--vp-c-bg); }
.items { display: grid; gap: 1px; background: var(--vp-c-divider); border: 1px solid var(--vp-c-divider); border-radius: 10px; overflow: hidden; }
.prog { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--vp-c-text-2); }
.prog .bar { flex: 1; height: 6px; border-radius: 999px; background: var(--vp-c-divider); overflow: hidden; }
.prog .bar i { display: block; height: 100%; background: var(--vp-c-brand-1); transition: width 0.35s ease; }
.notes { padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
</style>
