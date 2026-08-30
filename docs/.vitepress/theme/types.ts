/**
 * Hand-written types for the build-time payload (docs/.vitepress/data/checklist.json),
 * mirroring what tools/build-checklist.mjs emits. Components cast the JSON import
 * once (`data as ChecklistData`) so field access is checked against this module —
 * rename a field in the parser and these types are where the drift surfaces.
 * Keep in sync with build-checklist.mjs's `v` object.
 */

export interface Item {
  /** stable key persisted in localStorage, e.g. "2.1:0" */
  k: string;
  /** item text, may contain inline HTML (<b>…) */
  t: string;
}

export interface BlockNode {
  id: string;
  name: string;
  sub: string;
  notes: string[];
  cutoff: string;
  depth: number;
  items: Item[];
  subs: BlockNode[];
  type: string;
  weight?: number;
  /** deep-dive page link, attached by scanSkills/attachSkillLinks */
  link?: string;
}

export interface CapabilityCard {
  no: string;
  title: string;
  layer: string;
  layerName: string;
  notes: string[];
  prose: string[];
  blocks: BlockNode[];
  total: number;
}

export interface LevelCard extends BlockNode {
  keyword: string;
  years: string;
}

export interface PlanPhase extends BlockNode {
  week: string;
}

export interface ScoringRow {
  k: string;
  layer: string;
  axis: string;
  type: string;
  weight: number;
  link: string;
}

export interface SkillSidebarGroup {
  layer: string;
  items: { text: string; link: string }[];
}

export interface ChecklistData {
  docTitle: string;
  usage: string[];
  overview: {
    quick: string[];
    model: { code: string; name: string; desc: string }[];
    modelNote: string[];
    market: { title: string; rows: string[][] };
  };
  cards: CapabilityCard[];
  levels: { title: string; notes: string[]; cards: LevelCard[] };
  plan: { title: string; notes: string[]; phases: PlanPhase[] };
  flags: { title: string; notes: string[]; items: Item[] };
  scoring: { title: string; rows: ScoringRow[]; prose: string[]; legend: string[]; notes: string[] };
  evidence: { title: string; rows: [string, string][]; notes: string[] };
  sources: { title: string; items: string[]; revisions: string[] };
  closing: string;
  skillSidebar: SkillSidebarGroup[];
}
