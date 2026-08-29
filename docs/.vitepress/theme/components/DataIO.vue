<script setup lang="ts">
import { useProgress } from "../composables/useProgress";
const p = useProgress();
function download() {
  const url = URL.createObjectURL(new Blob([p.exportJSON()], { type: "application/json" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `mj2027-progress-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0];
  if (!f) return;
  f.text().then((t) => p.importJSON(t));
  (e.target as HTMLInputElement).value = "";
}
function doReset() {
  if (confirm("清空本机保存的勾选与打分？")) p.reset();
}
</script>
<template>
  <div class="data-io">
    <button type="button" @click="download">导出进度</button>
    <label class="import">导入进度<input type="file" accept="application/json" @change="onFile" hidden></label>
    <button type="button" @click="doReset">重置</button>
  </div>
</template>
<style scoped>
.data-io { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.data-io button, .data-io .import { font: inherit; font-size: 13px; padding: 6px 11px; border-radius: 8px; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-1); cursor: pointer; }
.data-io button:hover, .data-io .import:hover { border-color: var(--vp-c-brand-1); }
</style>
