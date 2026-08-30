<script setup lang="ts">
import { computed, inject } from "vue";
import { collectKeys, itemVisible, blockVisible, splitHead, type BlockNodeData, type Filters } from "./board";
import { useProgress } from "../composables/useProgress";

const props = defineProps<{
  node: BlockNodeData;
  inheritedType: string;
  /** when true (a filter is active), collapse state is ignored and the block is forced open */
  overrideOpen?: boolean;
}>();
const filters = inject<Filters>("boardFilters")!;
const { state, setCheck, toggleCollapsed } = useProgress();

const type = computed(() => props.node.type || props.inheritedType);
const keys = computed(() => collectKeys(props.node));
const done = computed(() => keys.value.filter((k) => state.checks[k]).length);
const pct = computed(() => (keys.value.length ? Math.round((done.value / keys.value.length) * 100) : 0));
const visibleSelf = computed(() => blockVisible(props.node, props.inheritedType, filters, state.checks));
const collapsible = computed(() => !!props.node.name && !props.overrideOpen);
const collapsed = computed(() => !!collapsible.value && state.collapsed.includes(props.node.id));
const visItems = computed(() => props.node.items.filter((i) => itemVisible(i, type.value, filters, state.checks)));
const badgeCls: Record<string, string> = { 门票: "tk", 基础: "bs", 溢价: "pm", 转化: "cv" };
</script>
<template>
  <div v-if="visibleSelf" class="blk" :class="{ 'lvl4': node.depth > 0, 'done-all': keys.length > 0 && done === keys.length, closed: collapsed }" :data-blk="node.id" :data-type="type">
    <div v-if="node.name" class="blk-hd" :class="{ clickable: collapsible }" @click="collapsible && toggleCollapsed(node.id)">
      <button v-if="collapsible" type="button" class="chev" :aria-expanded="!collapsed" :aria-label="(collapsed ? '展开 ' : '收起 ') + node.name" @click.stop="toggleCollapsed(node.id)">
        <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M5 3l6 5-6 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <h4>{{ node.name }}</h4>
      <span v-if="node.sub" class="sub">{{ node.sub }}</span>
      <span v-if="node.link" class="deep"><a :href="node.link" @click.stop>📖 深入 →</a></span>
      <span class="spacer" style="flex: 1"></span>
      <span class="badge" :class="badgeCls[type]">{{ type }}</span>
      <span class="prog"><span class="bar"><i :class="badgeCls[type]" :style="{ width: pct + '%' }"></i></span><span class="pl">{{ done }}/{{ keys.length }}</span></span>
    </div>
    <!-- v-show (not v-if) so print CSS can force collapsed blocks open -->
    <div v-show="!collapsed" class="blk-body">
      <div v-if="node.notes.length" class="notes"><p v-for="(n, i) in node.notes" :key="i" v-html="n"></p></div>
      <div v-if="visItems.length" class="items">
        <label
          v-for="it in visItems" :key="it.k" class="item"
          :class="{ done: !!state.checks[it.k] }"
          :data-k="it.k" :data-s="it.t.replace(/<[^>]+>/g, '').toLowerCase()"
        >
          <input
            type="checkbox" :data-k="it.k" :checked="!!state.checks[it.k]"
            @change="setCheck(it.k, ($event.target as HTMLInputElement).checked)"
          >
          <span class="txt" v-html="splitHead(it.t)"></span>
        </label>
      </div>
      <div v-if="node.cutoff" class="cutoff"><b>淘汰线</b>{{ node.cutoff }}</div>
      <BlockNode v-for="s in node.subs" :key="s.id" :node="s" :inherited-type="type" :override-open="overrideOpen" />
    </div>
  </div>
</template>
<style scoped>
.blk { margin-top: 14px; }
.blk.lvl4 { margin-top: 12px; padding-left: 10px; border-left: 2px solid var(--vp-c-divider); }
.blk-hd { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 6px; }
.blk-hd.clickable { cursor: pointer; user-select: none; }
.blk.closed > .blk-hd { margin-bottom: 0; }
.chev { display: inline-grid; place-items: center; width: 20px; height: 20px; flex: none; padding: 0; border: 0; border-radius: 6px; background: none; color: var(--vp-c-text-2); cursor: pointer; transition: transform 0.2s ease, background 0.2s ease; }
.chev:hover { background: var(--vp-c-bg-alt); color: var(--vp-c-text-1); }
.blk.closed > .blk-hd .chev, .chev[aria-expanded="false"] { transform: rotate(0deg); }
.chev[aria-expanded="true"] { transform: rotate(90deg); }
.blk-hd h4 { margin: 0; font-size: 14.5px; }
.blk-hd .sub { font-size: 12.5px; color: var(--vp-c-text-2); }
.deep a { font-size: 12.5px; }
.items { display: grid; gap: 1px; background: var(--vp-c-divider); border: 1px solid var(--vp-c-divider); border-radius: 10px; overflow: hidden; }
.item { display: grid; grid-template-columns: 20px 1fr; gap: 10px; align-items: start; background: var(--vp-c-bg); padding: 9px 12px; cursor: pointer; }
.item:hover { background: var(--vp-c-bg-alt); }
.item input { appearance: none; margin: 3px 0 0; width: 16px; height: 16px; border: 1.5px solid var(--vp-c-divider); border-radius: 5px; background: var(--vp-c-bg); cursor: pointer; position: relative; flex: none; }
.item input:checked { background: var(--vp-c-brand-1); border-color: var(--vp-c-brand-1); }
.item input:checked::after { content: ""; position: absolute; left: 4.5px; top: 1.5px; width: 4px; height: 8px; border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(42deg); }
.item.done { background: var(--vp-c-default-soft); }
.item.done .txt { color: var(--vp-c-text-2); }
.item .txt :deep(.head) { font-weight: 600; }
.blk.done-all > .items { border-color: var(--vp-c-success-3); }
.badge { display: inline-flex; font-size: 11.5px; font-weight: 600; padding: 2px 8px; border-radius: 999px; border: 1px solid; }
.badge.tk { color: var(--ticket); background: var(--ticket-bg); border-color: var(--ticket-line); }
.badge.bs { color: var(--base); background: var(--base-bg); border-color: var(--base-line); }
.badge.pm { color: var(--premium); background: var(--premium-bg); border-color: var(--premium-line); }
.badge.cv { color: var(--convert); background: var(--convert-bg); border-color: var(--convert-line); }
.prog { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--vp-c-text-2); min-width: 120px; }
.prog .bar { flex: 1; height: 6px; border-radius: 999px; background: var(--vp-c-divider); overflow: hidden; }
.prog .bar i { display: block; height: 100%; border-radius: inherit; background: var(--vp-c-brand-1); transition: width 0.35s ease; }
.prog .bar i.tk { background: var(--ticket); } .prog .bar i.bs { background: var(--base); }
.prog .bar i.pm { background: var(--premium); } .prog .bar i.cv { background: var(--convert); }
.notes { margin: 0 0 10px; padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
.cutoff { margin: 12px 0 0; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--vp-c-danger-3); background: var(--vp-c-danger-soft); font-size: 13px; color: var(--vp-c-danger-1); }
.cutoff b { display: block; font-size: 12px; margin-bottom: 2px; }
</style>
