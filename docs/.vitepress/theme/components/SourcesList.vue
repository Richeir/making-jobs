<script setup lang="ts">
import data from "../../data/checklist.json";
import type { ChecklistData } from "../types";
const s = (data as ChecklistData).sources;
const usage = (data as ChecklistData).usage;
const closing = (data as ChecklistData).closing;
</script>
<template>
  <h2 class="sect">{{ s.title }}</h2>
  <ul class="src"><li v-for="(i, n) in s.items" :key="n" v-html="i"></li></ul>
  <div v-for="(r, i) in s.revisions" :key="i" class="rev">{{ r }}</div>
  <div v-if="closing" class="quote" v-html="closing"></div>
  <div class="notes" style="margin-top: 14px"><p v-for="(u, i) in usage" :key="i" v-html="u"></p></div>
</template>
<style scoped>
.sect { font-size: 13px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--vp-c-text-2); margin: 26px 0 10px; }
.src { display: grid; gap: 7px; font-size: 13px; color: var(--vp-c-text-2); }
.src li { margin-left: 18px; }
.rev { font-size: 13px; color: var(--vp-c-text-2); border-left: 2px solid var(--vp-c-divider); padding-left: 12px; margin: 8px 0; }
.quote { margin: 18px 0 0; padding: 16px 18px; border-radius: 14px; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); font-size: 15.5px; line-height: 1.7; }
.notes { padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
</style>
