<script setup lang="ts">
const props = defineProps<{ pct: number }>();
const offset = () => 151 - (151 * Math.min(100, Math.max(0, props.pct))) / 100;
</script>
<template>
  <div class="ring" role="img" :aria-label="`总体达成进度 ${pct}%`">
    <svg width="56" height="56" viewBox="0 0 56 56">
      <circle cx="28" cy="28" r="24" fill="none" stroke="var(--vp-c-divider)" stroke-width="6" />
      <circle
        cx="28" cy="28" r="24" fill="none" stroke="var(--vp-c-brand-1)" stroke-width="6"
        stroke-linecap="round" stroke-dasharray="151" :stroke-dashoffset="offset()"
        style="transition: stroke-dashoffset 0.4s ease"
      />
    </svg>
    <div class="ring-val">{{ pct }}%</div>
  </div>
</template>
<style scoped>
.ring { position: relative; width: 56px; height: 56px; }
.ring svg { transform: rotate(-90deg); display: block; }
.ring-val { position: absolute; inset: 0; display: grid; place-items: center; font-size: 13px; font-weight: 650; }
</style>
