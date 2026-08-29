import { reactive } from "vue";

const KEY = "mj2027-progress-v1";

interface ProgressState {
  checks: Record<string, boolean>;
  scores: Record<string, number>;
  acts: Record<string, string>;
  view: string;
  side: string;
}

const blank = (): ProgressState => ({
  checks: {},
  scores: {},
  acts: {},
  view: "overview",
  side: "open",
});

let singleton: ProgressState | null = null;

/** test hook: drop the singleton so each test starts fresh */
export function __reset() {
  singleton = null;
}

export function useProgress() {
  if (!singleton) singleton = reactive(blank()) as ProgressState;
  const state = singleton;
  const save = () => {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch {
      /* private mode / sandboxed frame: keep working in memory */
    }
  };
  return {
    state,
    /** call from onMounted only — never during SSR pre-render */
    load() {
      try {
        const raw = localStorage.getItem(KEY);
        if (raw) Object.assign(state, JSON.parse(raw));
      } catch {
        /* corrupt payload: stay on blank state */
      }
    },
    setCheck(k: string, v: boolean) {
      state.checks[k] = v;
      save();
    },
    setScore(k: string, v: number) {
      state.scores[k] = v;
      save();
    },
    setAct(k: string, v: string) {
      state.acts[k] = v;
      save();
    },
    reset() {
      Object.assign(state, blank());
      save();
    },
    exportJSON() {
      return JSON.stringify(state, null, 2);
    },
    importJSON(text: string) {
      try {
        const o = JSON.parse(text);
        if (o && typeof o.checks === "object" && o.checks !== null) {
          Object.assign(state, blank(), o);
          save();
        }
      } catch {
        /* invalid file: ignore, keep current state */
      }
    },
  };
}

// --------------------------------------------------------------------------- //
// progress aggregation, mirroring the legacy page's AGG map exactly:
//  - blk:<id>   : one block + all of its nested subs (registered at render)
//  - card:<no>  : every blk of one capability card
//  - all        : union over blk:*/card:* (levels & plan cards self-register too),
//                 excludes flags and derived type:* buckets
//  - type:<t>   : union of blocks whose (own) type is <t> on any card
//  - flags      : red-flag items, counted separately
// --------------------------------------------------------------------------- //
interface Flat {
  items: { k: string }[];
  subs: Flat[];
}
const collect = <T extends Flat>(node: T, bucket: string[]) => {
  node.items.forEach((i) => bucket.push(i.k));
  node.subs.forEach((s) => collect(s, bucket));
  return bucket;
};

export interface Agg {
  all: string[];
  byType: Record<string, string[]>;
  blk: Record<string, string[]>;
  card: Record<string, string[]>;
  flags: string[];
  /** blk map incl. levels/plan self-registered ids (s8b0… / s9b0…), for progress bars */
}

export function aggKeys(data: any): Agg {
  const blk: Record<string, string[]> = {};
  const card: Record<string, string[]> = {};
  const allSet = new Set<string>();
  const typeSets: Record<string, Set<string>> = { 门票: new Set(), 基础: new Set(), 溢价: new Set(), 转化: new Set() };

  for (const c of data.cards) {
    const cardKeys: string[] = [];
    for (const b of c.blocks) {
      const keys = collect(b, []);
      blk[b.id] = keys;
      cardKeys.push(...keys);
      keys.forEach((k) => allSet.add(k));
      if (typeSets[b.type]) keys.forEach((k) => typeSets[b.type].add(k));
    }
    card["card:" + c.no] = cardKeys;
  }
  // levels cards & plan phases self-registered AGG["blk:"+id] on the legacy page
  for (const lv of data.levels.cards) blk[lv.id] = collect(lv, []);
  for (const ph of data.plan.phases) blk[ph.id] = collect(ph, []);
  [...Object.values(blk).flat(), ...allSet].forEach((k) => allSet.add(k));

  return {
    all: [...allSet],
    byType: Object.fromEntries(Object.entries(typeSets).map(([t, s]) => [t, [...s]])),
    blk,
    card,
    flags: data.flags.items.map((i: { k: string }) => i.k),
  };
}
