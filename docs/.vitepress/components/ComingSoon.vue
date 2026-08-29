<script setup lang="ts">
defineProps<{ name: string }>();
</script>
<template>
  <p class="muted">组件 <code>{{ name }}</code> 将在交互重写阶段接入。</p>
</template>
