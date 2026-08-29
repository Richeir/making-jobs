<script setup lang="ts">
import { computed, onMounted } from "vue";
import data from "../../data/checklist.json";
import { useProgress, aggKeys } from "../composables/useProgress";
import { weightedTotal, bandFor, radarPoints, pathOf, type Row } from "../composables/score";
import { plain } from "./board";

const { state, setScore, setAct, load } = useProgress();
onMounted(() => load());

const sc = (data as any).scoring as { title: string; rows: Row[]; prose: string[]; legend: string[]; notes: string[] };
const ev = (data as any).evidence;
const agg = aggKeys(data as any);
const rows = sc.rows;
const badgeCls: Record<string, string> = { 门票: "tk", 基础: "bs", 溢价: "pm", 转化: "cv" };

const scoredCount = computed(() => rows.filter((r) => state.scores[r.k] !== undefined).length);
const total = computed(() => weightedTotal(rows, state.scores));
const band = computed(() => bandFor(total.value, scoredCount.value));
const lowTicket = computed(() =>
  rows.filter((r) => r.type === "门票" && (state.scores[r.k] || 0) < 2),
);
const alertMsg = computed(() => {
  const pool = (sc.prose || []).concat(sc.notes || []).map(plain);
  const line = pool.find((t) => t.includes("门票优先"));
  return line ? line.replace(/^[\s\S]*?门票优先\s*[:：]\s*/, "") : "门票项低于 2 分时，先补它再谈整体优化。";
});
const advice = computed(() => {
  const adv: string[] = [];
  if (!scoredCount.value) adv.push("给各维度打一个分（0–3），加权总分、门票告警和能力形状才会出来。");
  else {
    const scored = rows.filter((r) => state.scores[r.k] !== undefined);
    const weak = scored.slice().sort((a, b) => (state.scores[a.k] || 0) - (state.scores[b.k] || 0)).slice(0, 2);
    adv.push(`最弱两项：<b>${weak.map((r) => plain(r.layer || "")).join("</b> 与 <b>")}</b>——到「90 天计划」里挑对应动作，写进上面的“下一动作”。`);
  }
  const tTodo = (agg.byType["门票"] || []).filter((k) => !state.checks[k]).length;
  if (tTodo) adv.push(`门票清单（2.1 节）还有 <b>${tTodo}</b> 项未打勾，纸笔轮最先出局的就是这里。`);
  const flags = agg.flags.filter((k) => state.checks[k]).length;
  if (flags) adv.push(`红旗清单命中 <b>${flags}</b> 条：出现任意一条，先修再投。`);
  return adv;
});

/* radar geometry — same constants as the legacy page */
const W = 400, H = 330, cx = W / 2, cy = H / 2 + 2, R = 96;
const at = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / rows.length;
const gridPolys = computed(() =>
  [1, 2, 3].map((lv) =>
    radarPoints(rows.map(() => lv), cx, cy, R).map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" "),
  ),
);
const spokes = computed(() =>
  rows.map((_, i) => ({ x2: cx + R * Math.cos(at(i)), y2: cy + R * Math.sin(at(i)) })),
);
const shapeD = computed(() => pathOf(radarPoints(rows.map((r) => state.scores[r.k] || 0), cx, cy, R)));
const labels = computed(() =>
  rows.map((r, i) => {
    const a = at(i), cos = Math.cos(a), sin = Math.sin(a);
    return {
      x: cx + (R + 14) * cos, y: cy + (R + 14) * sin + 4,
      anchor: Math.abs(cos) < 0.35 ? "middle" : cos > 0 ? "start" : "end",
      axis: r.axis || "", strong: r.type === "门票", val: state.scores[r.k] ?? 0,
    };
  }),
);
const radarSR = computed(() => "能力自评雷达图：" + rows.map((r) => `${r.axis} ${state.scores[r.k] || 0} 分`).join("，"));
const perRow = (r: Row) => (((state.scores[r.k] || 0) * r.weight) / 100).toFixed(2);
const SCALE = ["0 · 没概念", "1 · 用过说不清", "2 · 能独立完成并解释取舍", "3 · 有证据且能教别人"];
</script>
<template>
  <div class="score">
    <h2 class="sect">{{ plain(sc.title) }}</h2>
    <div v-if="(sc.prose || []).concat(sc.notes || []).length" class="notes">
      <p v-for="(p, i) in sc.prose.concat(sc.notes)" :key="i" v-html="p"></p>
    </div>
    <div class="score-wrap">
      <div class="col">
        <div class="card"><div class="card-bd">
          <div v-for="r in rows" :key="r.k" class="score-row">
            <div>
              <div class="nm"><span v-html="r.layer"></span><span class="badge" :class="badgeCls[r.type]">{{ r.type }}</span></div>
              <div class="meta"><span>权重 {{ r.weight }}%</span><span>加权 <b>{{ perRow(r) }}</b></span>
                <a class="btn" :href="`/making-jobs/checklist#card-${String((r as any).link || '7.1').split('.')[0]}`">去看清单</a></div>
            </div>
            <div class="seg" :class="state.scores[r.k] !== undefined ? 's' + state.scores[r.k] : ''" role="group" :aria-label="plain(r.layer || '') + ' 自评得分'">
              <button v-for="v in [0, 1, 2, 3]" :key="v" type="button" :aria-pressed="state.scores[r.k] === v" :aria-label="v + ' 分'" @click="setScore(r.k, v)">{{ v }}</button>
            </div>
            <div class="next-act"><label :for="'act-' + r.k">下一动作</label>
              <input :id="'act-' + r.k" type="text" placeholder="一句话：下一步具体做什么" :value="state.acts[r.k] || ''" @input="setAct(r.k, ($event.target as HTMLInputElement).value)"></div>
          </div>
          <div class="scale"><span v-for="l in SCALE" :key="l">{{ l }}</span></div>
        </div></div>
      </div>
      <div class="col">
        <div class="total">
          <span class="small muted">加权总分（0–3）</span>
          <span class="v">{{ scoredCount ? total.toFixed(2) : "—" }}</span>
          <span class="band" :class="band[0] === 'nu' ? '' : band[0]">{{ band[1] }}</span>
          <span class="spacer" style="flex: 1"></span>
          <span class="small muted">已评 {{ scoredCount }} / {{ rows.length }} 项</span>
        </div>
        <div v-if="scoredCount && lowTicket.length" class="alert">
          <div><b>门票告警</b><div>{{ alertMsg }}</div></div>
        </div>
        <div class="card" style="margin-top: 12px"><div class="card-bd">
          <div class="sr" aria-live="polite">{{ radarSR }}</div>
          <svg class="radar" :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="能力自评雷达图">
            <polygon v-for="(g, i) in gridPolys" :key="i" class="grid" :points="g" />
            <line v-for="(s, i) in spokes" :key="i" class="spoke" :x1="cx" :y1="cy" :x2="s.x2" :y2="s.y2" />
            <path class="shape" :d="shapeD" />
            <template v-for="(l, i) in labels" :key="i">
              <text class="ax" :class="{ strong: l.strong }" :x="l.x" :y="l.y" :text-anchor="l.anchor">{{ l.axis }}</text>
              <text v-if="scoredCount" class="val" :x="l.x" :y="l.y + 12" :text-anchor="l.anchor">{{ l.val }}/3</text>
            </template>
            <text v-if="!scoredCount" class="ax" :x="cx" :y="cy" text-anchor="middle">打分后显示能力形状</text>
          </svg>
          <div v-if="advice.length" class="notes" style="margin-top: 12px"><p v-for="(a, i) in advice" :key="i" v-html="'· ' + a"></p></div>
        </div></div>
      </div>
    </div>
    <h2 class="sect">{{ plain(ev.title) }}</h2>
    <div v-if="(ev.notes || []).length" class="notes"><p v-for="(n, i) in ev.notes" :key="i" v-html="n"></p></div>
    <div class="grid2">
      <div v-for="(r, i) in ev.rows" :key="i" class="qcard"><div class="n">{{ r[0] }}</div><p v-html="r[1]"></p></div>
    </div>
  </div>
</template>
<style scoped>
.sect { font-size: 13px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--vp-c-text-2); margin: 26px 0 10px; }
.score-wrap { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 14px; align-items: start; }
@media (max-width: 860px) { .score-wrap { grid-template-columns: minmax(0, 1fr); } }
.card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 14px; }
.card-bd { padding: 2px 16px 14px; }
.score-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px 12px; align-items: center; padding: 11px 0; border-bottom: 1px solid var(--vp-c-divider); }
.score-row:last-of-type { border-bottom: 0; }
.nm { font-size: 14px; font-weight: 600; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.meta { font-size: 12px; color: var(--vp-c-text-2); margin-top: 2px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.btn { padding: 1px 8px; font-size: 11.5px; border: 1px solid var(--vp-c-divider); border-radius: 8px; }
.seg { display: flex; gap: 3px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); border-radius: 9px; padding: 3px; }
.seg button { font: inherit; font-size: 12.5px; width: 30px; height: 28px; border: 0; border-radius: 6px; background: none; color: var(--vp-c-text-2); cursor: pointer; }
.seg button:hover { background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.seg button[aria-pressed="true"] { background: var(--vp-c-text-1); color: var(--vp-c-bg); font-weight: 650; }
.seg.s0 button[aria-pressed="true"] { background: var(--vp-c-danger-1); color: #fff; }
.seg.s1 button[aria-pressed="true"] { background: var(--ticket); color: #fff; }
.seg.s2 button[aria-pressed="true"] { background: var(--base); color: #fff; }
.seg.s3 button[aria-pressed="true"] { background: var(--vp-c-success-1); color: #fff; }
.next-act { grid-column: 1 / -1; display: flex; gap: 8px; align-items: center; }
.next-act label { font-size: 12px; color: var(--vp-c-text-2); flex: none; }
.next-act input { flex: 1; font: inherit; font-size: 13px; padding: 5px 9px; border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg-alt); color: inherit; min-width: 0; }
.total { display: flex; align-items: baseline; gap: 12px; padding: 14px 16px; border-radius: 12px; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); flex-wrap: wrap; }
.total .v { font-size: 34px; font-weight: 700; letter-spacing: -0.02em; }
.band { font-size: 12px; font-weight: 650; padding: 3px 9px; border-radius: 999px; border: 1px solid; }
.band.b-hi { color: var(--vp-c-success-1); border-color: var(--vp-c-success-1); }
.band.b-mid { color: var(--base); border-color: var(--base); }
.band.b-lo { color: var(--vp-c-danger-1); border-color: var(--vp-c-danger-1); }
.alert { display: flex; gap: 10px; align-items: flex-start; padding: 11px 14px; border-radius: 12px; font-size: 13.5px; border: 1px solid var(--vp-c-danger-3); background: var(--vp-c-danger-soft); color: var(--vp-c-danger-1); margin-top: 12px; }
.radar { width: 100%; height: auto; display: block; }
.radar .grid { fill: none; stroke: var(--vp-c-divider); stroke-width: 1; }
.radar .spoke { stroke: var(--vp-c-divider); stroke-width: 1; }
.radar .shape { fill: rgba(48, 86, 201, 0.18); stroke: var(--vp-c-brand-1); stroke-width: 2; stroke-linejoin: round; transition: d 0.3s ease; }
.radar text.ax { font-size: 11px; fill: var(--vp-c-text-2); }
.radar text.ax.strong { fill: var(--vp-c-text-1); font-weight: 600; }
.radar text.val { font-size: 10.5px; fill: var(--vp-c-brand-1); font-weight: 650; }
.scale { display: flex; gap: 6px; flex-wrap: wrap; font-size: 12px; color: var(--vp-c-text-2); margin-top: 8px; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }
.qcard { padding: 13px 15px; border-radius: 12px; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); }
.qcard .n { font-size: 11.5px; color: var(--vp-c-text-2); font-weight: 650; }
.qcard p { margin: 3px 0 0; font-size: 14px; }
.notes { margin: 0 0 10px; padding: 10px 12px; border-radius: 10px; background: var(--vp-c-bg-alt); border: 1px solid var(--vp-c-divider); font-size: 13px; color: var(--vp-c-text-2); display: grid; gap: 6px; }
.notes p { margin: 0; }
.small { font-size: 12.5px; }
.muted { color: var(--vp-c-text-2); }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.badge { display: inline-flex; font-size: 11.5px; font-weight: 600; padding: 2px 8px; border-radius: 999px; border: 1px solid; }
.badge.tk { color: var(--ticket); background: var(--ticket-bg); border-color: var(--ticket-line); }
.badge.bs { color: var(--base); background: var(--base-bg); border-color: var(--base-line); }
.badge.pm { color: var(--premium); background: var(--premium-bg); border-color: var(--premium-line); }
.badge.cv { color: var(--convert); background: var(--convert-bg); border-color: var(--convert-line); }
</style>
