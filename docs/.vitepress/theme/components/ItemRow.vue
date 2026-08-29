<script setup lang="ts">
import { useProgress } from "../composables/useProgress";
import { splitHead, type Item } from "./board";
const props = defineProps<{ it: Item; flag?: boolean }>();
const { state, setCheck } = useProgress();
</script>
<template>
  <label class="item" :class="{ done: !!state.checks[props.it.k] && !props.flag, hit: !!state.checks[props.it.k] && props.flag }" :data-k="props.it.k">
    <input type="checkbox" :data-k="props.it.k" :checked="!!state.checks[props.it.k]" @change="setCheck(props.it.k, ($event.target as HTMLInputElement).checked)">
    <span class="txt" v-html="splitHead(props.it.t)"></span>
  </label>
</template>
<style scoped>
.item { display: grid; grid-template-columns: 20px 1fr; gap: 10px; align-items: start; background: var(--vp-c-bg); padding: 9px 12px; cursor: pointer; }
.item:hover { background: var(--vp-c-bg-alt); }
.item input { appearance: none; margin: 3px 0 0; width: 16px; height: 16px; border: 1.5px solid var(--vp-c-divider); border-radius: 5px; background: var(--vp-c-bg); cursor: pointer; position: relative; flex: none; }
.item input:checked { background: var(--vp-c-brand-1); border-color: var(--vp-c-brand-1); }
.item input:checked::after { content: ""; position: absolute; left: 4.5px; top: 1.5px; width: 4px; height: 8px; border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(42deg); }
.item.done { background: var(--vp-c-default-soft); }
.item.done .txt { color: var(--vp-c-text-2); }
.item.hit { background: var(--vp-c-danger-soft); }
.item.hit input:checked { background: var(--vp-c-danger-1); border-color: var(--vp-c-danger-1); }
.item.hit .txt { color: var(--vp-c-danger-1); }
.txt :deep(.head) { font-weight: 600; }
</style>
