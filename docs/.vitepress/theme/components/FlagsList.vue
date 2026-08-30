<script setup lang="ts">
import { computed, onMounted } from "vue";
import data from "../../data/checklist.json";
import { useProgress } from "../composables/useProgress";
import { plain } from "./board";
import type { ChecklistData } from "../types";
import ItemRow from "./ItemRow.vue";

const { state, load } = useProgress();
onMounted(() => load());
const f = (data as ChecklistData).flags;
const hit = computed(() => f.items.filter((i) => state.checks[i.k]).length);
</script>
<template>
  <h2 class="sect">{{ plain(f.title) }}</h2>
  <div class="count-line">🚩 命中 <b>{{ hit }}</b> / {{ f.items.length }} 条<span class="muted">{{ hit ? " · ⚠️ 出现任意一条，先修再投" : " · ✅ 勾掉你确实命中的那条" }}</span></div>
  <div class="card"><div class="card-bd">
    <div v-if="f.notes.length" class="notes" style="margin-top: 12px"><p v-for="(n, i) in f.notes" :key="i" v-html="n"></p></div>
    <div class="items"><ItemRow v-for="it in f.items" :key="it.k" :it="it" flag /></div>
  </div></div>
</template>
<style scoped>
.sect { font-size: 13px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--vp-c-text-2); margin: 26px 0 10px; }
.count-line { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 13px; color: var(--vp-c-text-2); margin-bottom: 10px; }
.count-line b { color: var(--vp-c-danger-1); font-size: 15px; }
.card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-danger-3); border-radius: 14px; }
.card-bd { padding: 2px 16px 14px; }
.items { display: grid; gap: 1px; background: var(--vp-c-danger-3); border: 1px solid var(--vp-c-danger-3); border-radius: 10px; overflow: hidden; }
.notes { padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
.muted { color: var(--vp-c-text-2); }
</style>
