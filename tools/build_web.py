#!/usr/bin/env python3
"""Generate index.html (interactive visual version) from the checklist markdown.

Usage:  python3 tools/build_web.py [input.md] [output.html]
The markdown file stays the source of truth; re-run this after editing it.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "2027-programmer-job-skills-checklist.md"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "index.html"


# --------------------------------------------------------------------------- #
# inline markdown -> safe html
# --------------------------------------------------------------------------- #
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    s = esc(s.strip())
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def sec_no(title: str):
    """'3. ② AI 协作力：...' -> ('3', rest) ; '附录 A：...' -> ('A', rest)."""
    m = re.match(r"^(\d+)\.\s*(.*)$", title)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"^附录\s*([A-Z])[:：]\s*(.*)$", title)
    if m:
        return m.group(1), m.group(2)
    return None, title


# --------------------------------------------------------------------------- #
# parse the document into a small tree: section -> block -> (nested block, items)
# --------------------------------------------------------------------------- #
def new_block(name: str, sub: str = "", level: int = 3):
    return {"level": level, "name": name, "sub": sub, "notes": [], "items": [],
            "cutoff": "", "blocks": []}


def parse(text: str):
    doc = {"title": "", "usage": [], "sections": []}
    holder = doc                              # object we are currently appending to
    stack: list = []                          # active block stack inside a section
    in_code = False
    table_buf: list[list[str]] = []

    def deepest():
        return stack[-1] if stack else holder

    def close_table():
        nonlocal table_buf
        if table_buf and isinstance(holder, dict) and "table" in holder:
            holder["table"] = table_buf
        table_buf = []

    for raw in text.splitlines():
        s = raw.strip()

        if in_code:
            if s.startswith("```"):
                in_code = False
            elif isinstance(holder, dict) and "code" in holder:
                holder["code"].append(raw.rstrip())
            continue
        if s.startswith("```"):
            in_code = True
            continue

        if table_buf and not s.startswith("|"):
            close_table()
        if s.startswith("|"):
            cells = [inline(c) for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells):
                table_buf.append(cells)
            continue
        if not s or s == "---":
            continue

        # ---- headings -------------------------------------------------------
        if s.startswith("## "):
            close_table()
            title = s[3:].strip()
            no, rest = sec_no(title)
            holder = {"no": no, "raw": title, "title": rest, "notes": [], "prose": [],
                      "ordered": [], "bullets": [], "table": [], "code": [], "blocks": []}
            doc["sections"].append(holder)
            stack = []
            continue
        if s.startswith("### "):
            name = re.sub(r"^\s*\d+\.\d+\s*", "", s[4:].strip())
            blk = new_block(name, level=3)
            holder["blocks"].append(blk)
            stack = [blk]                      # a ### heading always starts a new branch
            continue
        if s.startswith("# "):
            if not doc["title"]:
                doc["title"] = s[2:].strip()
            continue

        if holder is doc:                      # front matter, before the first ##
            if s.startswith(">"):
                doc["usage"].append(inline(s.lstrip("> ")))
            continue

        # ---- checklist items ------------------------------------------------
        if s.startswith("- [ ]") or s.startswith("- [x]"):
            txt = inline(re.sub(r"^-\s+\[[ xX]\]\s*", "", s))
            target = deepest()
            if isinstance(target, dict) and "items" in target:
                target["items"].append(txt)
            else:
                blk = new_block("", level=3)
                holder["blocks"].append(blk)
                stack = [blk]
                blk["items"].append(txt)
            continue

        # ---- blockquotes / notes --------------------------------------------
        if s.startswith(">"):
            note = inline(s.lstrip("> "))
            target = deepest()
            (target["notes"] if isinstance(target, dict) and "notes" in target
             else holder["notes"]).append(note)
            continue

        # ---- bold pseudo headings -------------------------------------------
        m = re.match(r"^\*\*(.+?)\*\*\s*[:：]?\s*(.*)$", s)
        if m:
            name, rest = m.group(1).strip(), m.group(2).strip()
            if len(name) <= 22 and len(rest) <= 60:
                while stack and stack[-1]["level"] >= 4:      # bold blocks are siblings
                    stack.pop()
                parent = deepest()
                blk = new_block(name, rest, level=4 if stack else 3)
                if isinstance(parent, dict) and "blocks" in parent and parent is not holder:
                    parent["blocks"].append(blk)
                    stack = stack + [blk]
                else:
                    holder["blocks"].append(blk)
                    stack = [blk]
            else:
                holder["prose"].append(inline(s))
            continue

        # ---- ordered / plain bullets ----------------------------------------
        if re.match(r"^\d+\.\s+", s):
            holder["ordered"].append(inline(re.sub(r"^\d+\.\s+", "", s)))
            continue
        if s.startswith("- "):
            body = inline(s[2:])
            mb = re.match(r"^<b>淘汰线</b>\s*[:：]?\s*(.*)$", body)
            if mb:
                deepest()["cutoff"] = mb.group(1)
            else:
                holder["bullets"].append(body)
            continue

        holder["prose"].append(inline(s))

    close_table()
    return doc


# --------------------------------------------------------------------------- #
# assemble the view model (types, layers, weights, stable item keys)
# --------------------------------------------------------------------------- #
TYPE_BY_BLOCK = {"2.1": "门票", "2.2": "基础"}
LAYER = {
    "2": ("①", "工程底座"), "3": ("②", "AI 协作力"), "4": ("③", "AI 构建力"),
    "5": ("④", "判断力 / 业务"), "6": ("⑤", "信任资本"), "7": ("★", "求职资产"),
}
ORDER = ["2", "3", "4", "5", "6", "7"]


def block_id(sec_no_v: str, idx: int, total: int) -> str:
    return f"{sec_no_v}.{idx + 1}" if total > 1 else sec_no_v


def flatten(blk, prefix, depth=0):
    """Turn a parsed block (plus its nested bold sub-blocks) into view data."""
    node = {
        "id": prefix,
        "name": blk["name"],
        "sub": blk["sub"],
        "notes": blk["notes"],
        "cutoff": blk["cutoff"],
        "depth": depth,
        "items": [{"k": f"{prefix}:{i}", "t": t} for i, t in enumerate(blk["items"])],
        "subs": [flatten(child, f"{prefix}#{i}", depth + 1)
                 for i, child in enumerate(blk["blocks"])],
    }
    return node


def build_views(doc):
    secs = {sec["raw"]: sec for sec in doc["sections"]}
    by_no = {sec["no"]: sec for sec in doc["sections"] if sec["no"]}

    # ---------------- overview ----------------
    quick = next((s for s in doc["sections"] if s["raw"].startswith("30 秒速览")), None)
    model_sec = by_no.get("1")
    market_sec = by_no.get("0")
    model = []
    for line in (model_sec or {}).get("code", []):
        m = re.match(r"^\s*([①②③④⑤])\s+(.+?)\s{2,}(.*)$", line)
        if m:
            model.append({"code": m.group(1), "name": m.group(2), "desc": m.group(3)})
    # keep document order: ⑤ on top of the pyramid, ① as its base

    overview = {
        "quick": (quick or {}).get("ordered", []),
        "model": model,
        "modelNote": (model_sec or {}).get("prose", []) + (model_sec or {}).get("notes", []),
        "market": {
            "title": (market_sec or {}).get("title", ""),
            "rows": (market_sec or {}).get("table", []),
            "notes": (market_sec or {}).get("notes", []) + (market_sec or {}).get("prose", []),
        },
    }

    # ---------------- capability checklist ----------------
    cards = []
    for no in ORDER:
        sec = by_no.get(no)
        if not sec:
            continue
        blocks = sec["blocks"]
        cards.append({
            "no": no,
            "title": sec["title"],
            "layer": LAYER.get(no, ("", ""))[0],
            "layerName": LAYER.get(no, ("", ""))[1],
            "notes": sec["notes"],
            "prose": sec["prose"],
            "blocks": [flatten(b, block_id(no, i, len(blocks)))
                       for i, b in enumerate(blocks)],
        })
    for card in cards:
        bid = card["blocks"][0]["id"] if len(card["blocks"]) == 1 else None
        for blk in card["blocks"]:
            blk["type"] = TYPE_BY_BLOCK.get(blk["id"], "溢价")
            blk["weight"] = {"门票": 15, "基础": 15}.get(blk["type"], None)

    # ---------------- levels / plan / flags ----------------
    def simple_sections(nos):
        out = []
        for no in nos:
            sec = by_no.get(no)
            if not sec:
                continue
            for i, b in enumerate(sec["blocks"]):
                node = flatten(b, f"s{no}b{i}")
                out.append(node)
        return out

    levels_sec = by_no.get("8")
    levels = {"title": (levels_sec or {}).get("title", ""),
              "notes": (levels_sec or {}).get("prose", []) + (levels_sec or {}).get("notes", []),
              "cards": simple_sections(["8"])}
    plan_sec = by_no.get("9")
    plan = {"title": (plan_sec or {}).get("title", ""),
            "notes": (plan_sec or {}).get("prose", []) + (plan_sec or {}).get("notes", []),
            "phases": simple_sections(["9"])}
    flags_sec = by_no.get("10")
    flags = {"title": (flags_sec or {}).get("title", ""),
             "notes": (flags_sec or {}).get("prose", []) + (flags_sec or {}).get("notes", []),
             "items": [{"k": f"f{i}", "t": t} for i, t in enumerate(
                 [t for b in (flags_sec or {}).get("blocks", []) for t in b["items"]])]}

    # ---------------- appendix A: score sheet ----------------
    appA = by_no.get("A")
    rows = [r for r in (appA or {}).get("table", []) if r and "合计" not in r[0]]
    header = rows[0] if rows else []
    score_rows = []
    for r in rows[1:]:
        if len(r) < 3:
            continue
        w = re.search(r"(\d+)\s*%", r[2])
        score_rows.append({
            "k": f"a{len(score_rows)}",
            "layer": r[0],
            "axis": re.sub(r"<[^>]+>", "", r[0]).split("（")[0].strip(),
            "type": re.sub(r"<[^>]+>", "", r[1]),
            "weight": int(w.group(1)) if w else 0,
        })
    scoring = {
        "title": (appA or {}).get("title", ""),
        "rows": score_rows,
        "prose": (appA or {}).get("prose", []),
        "legend": (appA or {}).get("bullets", []),
        "notes": (appA or {}).get("notes", []),
    }

    # ---------------- appendix B: evidence ----------------
    appB = by_no.get("B")
    brows = [r for r in (appB or {}).get("table", [])]
    evidence = {"title": (appB or {}).get("title", ""),
                "rows": brows[1:] if len(brows) > 1 else [],
                "notes": (appB or {}).get("prose", []) + (appB or {}).get("notes", [])}

    # ---------------- appendix C: sources ----------------
    appC = by_no.get("C")
    cnotes = (appC or {}).get("notes", [])
    revisions = [n for n in cnotes if n.startswith("修订说明")]
    closing = next((n for n in cnotes if not n.startswith("修订说明")), "")
    sources = {"title": (appC or {}).get("title", ""),
               "items": (appC or {}).get("bullets", []),
               "revisions": revisions}

    return {
        "docTitle": doc["title"],
        "usage": doc["usage"],
        "overview": overview,
        "cards": cards,
        "levels": levels,
        "plan": plan,
        "flags": flags,
        "scoring": scoring,
        "evidence": evidence,
        "sources": sources,
        "closing": closing,
    }


def annotate(v):
    """Give every (nested) block its type, and total its items for progress bars."""
    order = {"门票": 0, "基础": 1, "溢价": 2, "转化": 3}

    def rec(node, t):
        node["type"] = node.get("type") or t
        for c in node["subs"]:
            rec(c, t)

    for card in v["cards"]:
        for blk in card["blocks"]:
            blk["type"] = TYPE_BY_BLOCK.get(blk["id"], SECTION_TYPE.get(card["no"], "溢价"))
            rec(blk, blk["type"])
        card["total"] = sum(len(b["items"]) + block_count(b) for b in card["blocks"])
    return v


def block_count(node):
    return sum(len(c["items"]) + block_count(c) for c in node["subs"])


SECTION_TYPE = {"2": "溢价", "3": "溢价", "4": "溢价", "5": "溢价", "6": "溢价", "7": "转化"}


def refine(v):
    """Small display-only cleanups: split headings, cross-link the score sheet."""
    for card in v["levels"]["cards"]:
        name, _, kw = card["name"].partition("（关键词")
        card["name"] = name.strip()
        card["keyword"] = kw.rstrip("）").strip("：: ").strip() if kw else ""
        card["years"] = re.split(r"（", card["name"])[0].strip()
    for ph in v["plan"]["phases"]:
        week, _, rest = ph["name"].partition("：")
        ph["week"] = week.strip()
        ph["name"] = rest.strip() or week.strip()
    link = {"①a": "2.1", "①b": "2.2", "②": "3.1", "③": "4", "④": "5", "⑤": "6"}
    for row in v["scoring"]["rows"]:
        row["link"] = link.get(row["axis"].split()[0] if row["axis"] else "", "7.1")
    annotate(v)
    return v


# --------------------------------------------------------------------------- #
# page template
# --------------------------------------------------------------------------- #
HEAD = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2027 程序员求职必要能力清单 · 可视化</title>
<style>
:root{
  --bg:#f6f7f9; --surface:#fff; --surface2:#fbfbfc; --text:#15171c; --muted:#6b7280;
  --line:#e5e7eb; --line-strong:#d4d7dd; --accent:#3056c9; --accent-bg:#eef2ff;
  --ticket:#a4570b; --ticket-bg:#fff5e9; --ticket-line:#f0d3ac;
  --base:#1c56b8; --base-bg:#eef4ff; --base-line:#c9dbf7;
  --premium:#6a2fb0; --premium-bg:#f6f1fd; --premium-line:#ddcbf3;
  --convert:#0f7264; --convert-bg:#eafaf5; --convert-line:#b7e3d7;
  --danger:#b42318; --danger-bg:#fff2f0; --danger-line:#f7c9c3;
  --ok:#0f7a3d; --shadow:0 1px 2px rgba(16,20,28,.05),0 8px 24px -18px rgba(16,20,28,.25);
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#0f1114; --surface:#171a1f; --surface2:#1c2026; --text:#e8eaee; --muted:#98a1ae;
    --line:#272c34; --line-strong:#343a44; --accent:#8ba6f5; --accent-bg:#18223c;
    --ticket:#e8a95c; --ticket-bg:#2a1f13; --ticket-line:#4a371f;
    --base:#82b1f5; --base-bg:#131f33; --base-line:#26405f;
    --premium:#bfa0ee; --premium-bg:#211830; --premium-line:#3c2b56;
    --convert:#5fd3b7; --convert-bg:#10241f; --convert-line:#1f4339;
    --danger:#f0857a; --danger-bg:#2c1614; --danger-line:#53251f;
    --ok:#5ec97f; --shadow:0 1px 2px rgba(0,0,0,.4);
    color-scheme:dark;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);
  font:15px/1.65 -apple-system,BlinkMacSystemFont,"SF Pro SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  font-variant-numeric:tabular-nums}
b{font-weight:650}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em;background:var(--surface2);
  border:1px solid var(--line);border-radius:4px;padding:.05em .3em}
.wrap{max-width:1120px;margin:0 auto;padding:0 18px 72px}
.muted{color:var(--muted)}
.small{font-size:12.5px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}

/* ---------- header ---------- */
header.top{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:saturate(1.6) blur(12px);border-bottom:1px solid var(--line)}
.top-in{max-width:1120px;margin:0 auto;padding:14px 18px 0}
.top-row{display:flex;gap:20px;align-items:flex-end;flex-wrap:wrap;justify-content:space-between}
.kicker{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{margin:2px 0 4px;font-size:22px;line-height:1.25;letter-spacing:-.01em}
.lead{margin:0;font-size:13px;color:var(--muted);max-width:62ch}
.gauge{display:flex;align-items:center;gap:14px}
.gauge .ring{position:relative;width:56px;height:56px;flex:none}
.gauge svg{display:block;transform:rotate(-90deg)}
.gauge .ring-val{position:absolute;inset:0;display:grid;place-items:center;font-size:13px;font-weight:650}
.gauge .ctrls{display:grid;gap:6px;justify-items:end}
.gauge .legend{display:grid;gap:2px;font-size:12px;color:var(--muted)}
.gauge .btns{display:flex;gap:6px}
.gauge .btn{font-size:11.5px;padding:3px 8px}
.gauge .legend b{color:var(--text)}
.tabs{display:flex;gap:2px;margin-top:12px;overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{appearance:none;border:0;border-bottom:2px solid transparent;background:none;color:var(--muted);
  font:inherit;font-size:14px;padding:9px 12px;cursor:pointer;white-space:nowrap;display:flex;gap:7px;align-items:center}
.tab:hover{color:var(--text)}
.tab[aria-selected=true]{color:var(--text);border-bottom-color:var(--accent);font-weight:600}
.tab .cnt{font-size:11px;color:var(--muted);background:var(--surface2);border:1px solid var(--line);
  border-radius:999px;padding:0 6px}
.tab .cnt.warn{color:var(--danger);border-color:var(--danger-line);background:var(--danger-bg)}
main{padding-top:22px}
section.view{display:none}
section.view.on{display:block;animation:fade .18s ease-out}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

/* ---------- cards ---------- */
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);
  margin-bottom:14px;overflow:hidden}
.card-hd{display:flex;gap:12px;align-items:flex-start;padding:14px 16px;flex-wrap:wrap}
.card-hd h2,.card-hd h3{margin:0;font-size:16px;line-height:1.4}
.card-hd .spacer{flex:1}
.card-bd{padding:2px 16px 14px;border-top:1px solid var(--line)}
.dot{width:26px;height:26px;flex:none;border-radius:8px;display:grid;place-items:center;font-size:13px;
  font-weight:650;background:var(--surface2);border:1px solid var(--line)}
.badge{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:600;letter-spacing:.02em;
  padding:2px 8px;border-radius:999px;border:1px solid}
.badge.tk{color:var(--ticket);background:var(--ticket-bg);border-color:var(--ticket-line)}
.badge.bs{color:var(--base);background:var(--base-bg);border-color:var(--base-line)}
.badge.pm{color:var(--premium);background:var(--premium-bg);border-color:var(--premium-line)}
.badge.cv{color:var(--convert);background:var(--convert-bg);border-color:var(--convert-line)}
.badge.nu{color:var(--muted);background:var(--surface2);border-color:var(--line)}
.bar{height:6px;border-radius:999px;background:var(--line);overflow:hidden;min-width:64px}
.bar i{display:block;height:100%;border-radius:inherit;background:var(--accent);transition:width .35s ease}
.bar.tl i.tk{background:var(--ticket)} .bar.tl i.bs{background:var(--base)}
.bar.tl i.pm{background:var(--premium)} .bar.tl i.cv{background:var(--convert)}
.bar.tl.multi{display:flex;background:var(--line)}
.prog{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);min-width:130px}
.prog .bar{flex:1}
.notes{margin:0 0 10px;padding:10px 12px;border-radius:10px;background:var(--surface2);border:1px solid var(--line);
  font-size:13px;color:var(--muted);display:grid;gap:6px}
.notes p{margin:0}

/* ---------- checklist items ---------- */
.blk{margin-top:14px}
.blk-hd{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
.blk-hd h4{margin:0;font-size:14px}
.blk-hd .sub{font-size:12.5px;color:var(--muted)}
.blk.lvl4{margin-top:12px}
.items{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.item{display:grid;grid-template-columns:20px 1fr;gap:10px;align-items:start;background:var(--surface);
  padding:9px 12px;cursor:pointer;transition:background .12s}
.item:hover{background:var(--surface2)}
.item input{appearance:none;margin:3px 0 0;width:16px;height:16px;border:1.5px solid var(--line-strong);
  border-radius:5px;background:var(--surface);cursor:pointer;position:relative;flex:none;transition:.12s}
.item input:hover{border-color:var(--accent)}
.item input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.item input:checked{background:var(--accent);border-color:var(--accent)}
.item input:checked::after{content:"";position:absolute;left:4.5px;top:1.5px;width:4px;height:8px;
  border:solid #fff;border-width:0 2px 2px 0;transform:rotate(42deg)}
.item .txt{font-size:14px}
.item .txt .head{font-weight:600}
.item.done{background:color-mix(in srgb,var(--surface) 60%,var(--accent-bg))}
.item.done .txt{color:var(--muted)}
.item.done input:checked{background:var(--ok);border-color:var(--ok)}
.item.hit{background:var(--danger-bg)}
.item.hit input:checked{background:var(--danger);border-color:var(--danger)}
.item.hit .txt{color:var(--danger)}
.blk.done-all .items{border-color:color-mix(in srgb,var(--ok) 45%,var(--line))}
.empty{padding:22px 14px;text-align:center;color:var(--muted);font-size:13.5px;border:1px dashed var(--line-strong);
  border-radius:12px;background:var(--surface2)}

/* ---------- toolbar ---------- */
.toolbar{position:sticky;top:var(--stick,112px);z-index:10;display:flex;gap:8px;align-items:center;flex-wrap:wrap;
  padding:10px 0;background:var(--bg)}
.search{display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--line);
  border-radius:10px;padding:6px 10px;min-width:230px;flex:1}
.search input{border:0;outline:0;background:none;color:inherit;font:inherit;flex:1;min-width:60px}
.search svg{flex:none;opacity:.55}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{font:inherit;font-size:12.5px;padding:5px 10px;border-radius:999px;border:1px solid var(--line-strong);
  background:var(--surface);color:var(--muted);cursor:pointer}
.chip:hover{border-color:var(--accent);color:var(--text)}
.chip[aria-pressed=true]{background:var(--text);border-color:var(--text);color:var(--surface);font-weight:600}
.chip.tp[aria-pressed=true]{background:var(--c);border-color:var(--c);color:#fff}
.btn{font:inherit;font-size:12.5px;padding:6px 11px;border-radius:9px;border:1px solid var(--line-strong);
  background:var(--surface);color:var(--text);cursor:pointer}
.btn:hover{border-color:var(--accent)}

/* ---------- overview ---------- */
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.qcard{padding:13px 15px;border-radius:12px;background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow)}
.qcard .n{font-size:11.5px;color:var(--muted);font-weight:650;letter-spacing:.06em}
.qcard p{margin:3px 0 0;font-size:14px}
h2.sect{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:26px 0 10px}
h2.sect:first-child{margin-top:0}
.pyr{display:grid;gap:6px;justify-items:center;margin-top:4px}
.layer{width:100%;border:1px solid var(--line);border-radius:12px;background:var(--surface);box-shadow:var(--shadow);
  padding:11px 14px;cursor:pointer;text-align:left;font:inherit;color:inherit;display:grid;gap:6px}
.layer:hover{border-color:var(--accent)}
.layer:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.layer .row{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.layer .code{font-size:12px;color:var(--muted);width:20px;flex:none}
.layer .nm{font-weight:650;font-size:15px}
.layer .ds{font-size:12.5px;color:var(--muted);flex:1;min-width:180px}
.layer .prog{min-width:120px;flex:none;width:150px}
.layer .split{display:flex;gap:6px;flex-wrap:wrap}
.layer .split span{font-size:12px;padding:3px 8px;border-radius:8px;border:1px solid}
.layer.l1{border-left:3px solid var(--ticket)}
.layer.l2{border-left:3px solid var(--base)}
.layer.l3,.layer.l4,.layer.l5{border-left:3px solid var(--premium)}
.tracks{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.track{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--surface)}
.track .t{font-size:13px;font-weight:650;display:flex;align-items:center;gap:7px}
.track .d{font-size:12.5px;color:var(--muted);margin-top:3px}
.track.a{border-top:3px solid var(--ticket)} .track.b{border-top:3px solid var(--premium)}
.mkt{display:grid;gap:10px}
.mkt .r{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:11px 14px;box-shadow:var(--shadow)}
.mkt .k{font-weight:650;font-size:14px}
.mkt .now{font-size:13px;color:var(--muted);margin-top:2px}
.mkt .next{font-size:13px;margin-top:5px;padding-top:5px;border-top:1px dashed var(--line)}
.mkt .next::before{content:"→ 2027 ";font-size:11px;color:var(--accent);font-weight:650;letter-spacing:.04em}
'''

CSS2 = r'''
/* ---------- score view ---------- */
.score-wrap{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:14px;align-items:start}
.score-wrap .col{min-width:0}
.score-row .btn{padding:1px 8px;font-size:11.5px}
.score-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px 12px;align-items:center;
  padding:11px 0;border-bottom:1px solid var(--line)}
.score-row:last-of-type{border-bottom:0}
.score-row .nm{font-size:14px;font-weight:600;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.score-row .meta{font-size:12px;color:var(--muted);margin-top:2px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.seg{display:flex;gap:3px;background:var(--surface2);border:1px solid var(--line);border-radius:9px;padding:3px}
.seg button{font:inherit;font-size:12.5px;width:30px;height:28px;border:0;border-radius:6px;background:none;
  color:var(--muted);cursor:pointer}
.seg button:hover{background:var(--surface);color:var(--text)}
.seg button[aria-pressed=true]{background:var(--text);color:var(--surface);font-weight:650}
.seg.s0 button[aria-pressed=true]{background:var(--danger)}
.seg.s1 button[aria-pressed=true]{background:var(--ticket);color:#fff}
.seg.s2 button[aria-pressed=true]{background:var(--base);color:#fff}
.seg.s3 button[aria-pressed=true]{background:var(--ok);color:#fff}
.next-act{grid-column:1/-1;display:flex;gap:8px;align-items:center}
.next-act label{font-size:12px;color:var(--muted);flex:none}
.next-act input{flex:1;font:inherit;font-size:13px;padding:5px 9px;border:1px solid var(--line);border-radius:8px;
  background:var(--surface2);color:inherit;min-width:0}
.next-act input:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
.total{display:flex;align-items:baseline;gap:12px;padding:14px 16px;border-radius:12px;background:var(--surface);
  border:1px solid var(--line);box-shadow:var(--shadow);flex-wrap:wrap}
.total .v{font-size:34px;font-weight:700;letter-spacing:-.02em}
.total .band{font-size:12px;font-weight:650;padding:3px 9px;border-radius:999px;border:1px solid}
.band.b-hi{color:var(--ok);background:color-mix(in srgb,var(--ok) 12%,transparent);border-color:var(--ok)}
.band.b-mid{color:var(--base);background:var(--base-bg);border-color:var(--base-line)}
.band.b-lo{color:var(--danger);background:var(--danger-bg);border-color:var(--danger-line)}
.alert{display:flex;gap:10px;align-items:flex-start;padding:11px 14px;border-radius:12px;font-size:13.5px;
  border:1px solid var(--danger-line);background:var(--danger-bg);color:var(--danger);margin-bottom:12px}
.alert.hide{display:none}
.alert svg{flex:none;margin-top:2px}
.radar{width:100%;height:auto;display:block}
.radar .grid{fill:none;stroke:var(--line);stroke-width:1}
.radar .spoke{stroke:var(--line-strong);stroke-width:1}
.radar .shape{fill:color-mix(in srgb,var(--accent) 18%,transparent);stroke:var(--accent);stroke-width:2;
  stroke-linejoin:round;transition:d .3s ease}
.radar text.ax{font-size:11px;fill:var(--muted)}
.radar text.ax.strong{fill:var(--text);font-weight:600}
.radar text.val{font-size:10.5px;fill:var(--accent);font-weight:650}
.scale{display:flex;gap:6px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.scale span{padding:2px 7px;border:1px solid var(--line);border-radius:7px;background:var(--surface2)}
/* ---------- levels ---------- */
.lv{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;align-items:start}
.lv .card{margin:0}
.lv-hd{padding:13px 15px;border-bottom:1px solid var(--line);background:var(--surface2)}
.lv-hd .yrs{font-size:16px;font-weight:650}
.cutoff{margin:12px 14px 14px;padding:10px 12px;border-radius:10px;border:1px solid var(--danger-line);
  background:var(--danger-bg);font-size:13px;color:var(--danger)}
.cutoff b{display:block;font-size:12px;letter-spacing:.04em;margin-bottom:2px}
/* ---------- plan ---------- */
.plan{display:grid;gap:0}
.phase{display:grid;grid-template-columns:120px minmax(0,1fr);gap:14px;padding:14px 0;border-top:1px solid var(--line)}
.phase:first-child{border-top:0}
.phase .when{position:relative;padding-right:10px}
.phase .when .w{font-size:12px;color:var(--muted);letter-spacing:.04em}
.phase .when .t{font-size:14.5px;font-weight:650;margin-top:2px}
.phase .when::after{content:"";position:absolute;right:-8px;top:6px;width:9px;height:9px;border-radius:50%;
  background:var(--accent);box-shadow:0 0 0 4px var(--bg)}
/* ---------- flags ---------- */
.flags .items{border-color:var(--danger-line)}
.flags .item .txt{color:var(--text)}
.flags .card{border-color:var(--danger-line)}
.flags .item input{border-color:var(--danger-line)}
.flags .item{grid-template-columns:20px 1fr}
.count-line{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-bottom:10px}
.count-line b{color:var(--danger);font-size:15px}
/* ---------- sources ---------- */
.src{display:grid;gap:7px;font-size:13px;color:var(--muted)}
.src li{margin-left:18px}
.rev{font-size:13px;color:var(--muted);border-left:2px solid var(--line-strong);padding-left:12px;margin:8px 0}
.quote{margin:18px 0 0;padding:16px 18px;border-radius:14px;background:var(--surface);border:1px solid var(--line);
  box-shadow:var(--shadow);font-size:15.5px;line-height:1.7}
/* ---------- footer ---------- */
footer{margin-top:28px;padding-top:14px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);
  display:flex;gap:12px;flex-wrap:wrap;justify-content:space-between}
footer a{color:var(--accent);text-decoration:none}
footer a:hover{text-decoration:underline}
/* ---------- responsive ---------- */
@media (max-width:860px){
  .pyr .layer{width:100%!important}
  .score-wrap{grid-template-columns:minmax(0,1fr)}
  .tracks{grid-template-columns:1fr}
  .phase{grid-template-columns:1fr;gap:8px}
  .phase .when::after{display:none}
  .gauge{width:100%}
}
@media (max-width:560px){
  h1{font-size:19px}
  .toolbar{position:static}
  .item{grid-template-columns:18px 1fr;gap:8px;padding:9px 10px}
}
@media print{
  header.top{position:static}
  .toolbar,.tabs,.btn{display:none!important}
  section.view{display:block!important;page-break-inside:avoid}
  .card{box-shadow:none}
  body{background:#fff}
}
'''

BODY = r'''</style>
</head>
<body>
<a class="sr" href="#main">跳到主要内容</a>
<header class="top">
  <div class="top-in">
    <div class="top-row">
      <div>
        <div class="kicker" id="kicker"></div>
        <h1 id="docTitle"></h1>
        <p class="lead" id="lead"></p>
      </div>
      <div class="gauge">
        <div class="ctrls">
        <div class="ring" id="ring" role="img" aria-label="总体达成进度">
          <svg width="56" height="56" viewBox="0 0 56 56" aria-hidden="true">
            <circle cx="28" cy="28" r="24" fill="none" stroke="var(--line)" stroke-width="6"></circle>
            <circle id="ringArc" cx="28" cy="28" r="24" fill="none" stroke="var(--accent)" stroke-width="6"
                    stroke-linecap="round" stroke-dasharray="151" stroke-dashoffset="151"
                    style="transition:stroke-dashoffset .4s ease"></circle>
          </svg>
          <div class="ring-val" id="ringVal">0%</div>
        </div>
          <div class="legend" id="legend"></div>
          <div class="btns"><button class="btn" id="printBtn" type="button">打印 / 存 PDF</button>
          <button class="btn" id="resetBtn" type="button">重置进度</button></div>
        </div>
      </div>
    </div>
    <nav class="tabs" id="tabs" role="tablist" aria-label="视图切换"></nav>
  </div>
</header>

<div class="wrap">
<main id="main">
  <section class="view" id="view-overview" role="tabpanel" aria-label="速览"></section>
  <section class="view" id="view-list" role="tabpanel" aria-label="能力清单"></section>
  <section class="view" id="view-score" role="tabpanel" aria-label="自评打分"></section>
  <section class="view" id="view-levels" role="tabpanel" aria-label="分级门槛线"></section>
  <section class="view" id="view-plan" role="tabpanel" aria-label="90 天行动计划"></section>
  <section class="view" id="view-flags" role="tabpanel" aria-label="红旗清单"></section>
  <section class="view" id="view-src" role="tabpanel" aria-label="来源与修订"></section>
</main>
<footer>
  <span id="footNote"></span>
  <span id="footMeta"></span>
</footer>
</div>

<script>
const DATA = __DATA__;
'''

JS = r'''
"use strict";
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.prototype.slice.call((r || document).querySelectorAll(s));
const TC = { 门票: "tk", 基础: "bs", 溢价: "pm", 转化: "cv" };
const LS = "mj2027-progress-v1";
const AGG = {};              // agg id -> [item keys]
let state = { checks: {}, scores: {}, acts: {}, view: "overview" };

(function load() {
  try {
    const raw = window.localStorage.getItem(LS);
    if (raw) state = Object.assign(state, JSON.parse(raw));
  } catch (e) { /* private mode / sandboxed frame: keep working in memory */ }
})();
function save() {
  try { window.localStorage.setItem(LS, JSON.stringify(state)); } catch (e) {}
}

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const attr = s => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const plain = s => String(s).replace(/<[^>]+>/g, "");
const stripGlyph = s => s.replace(/^[①②③④⑤]\s*/, "");
const isRTL = matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ----------------------------- item + block markup ----------------------------- */
function splitHead(t) {
  const i = t.indexOf("：");
  if (i > 0 && i <= 34) return '<span class="head">' + t.slice(0, i) + "</span>" + t.slice(i);
  return t;
}
function itemHTML(it, flag) {
  const p = attr(plain(it.t).toLowerCase());
  return '<label class="item' + (flag ? " flag" : "") + '" data-k="' + it.k + '" data-s="' + p + '">' +
    '<input type="checkbox" data-k="' + it.k + '"' + (state.checks[it.k] ? " checked" : "") + ">" +
    '<span class="txt">' + splitHead(it.t) + "</span></label>";
}
function itemsHTML(list, flag) {
  return '<div class="items">' + list.map(it => itemHTML(it, flag)).join("") + "</div>";
}
function collect(node, bucket) {
  node.items.forEach(it => bucket.push(it.k));
  node.subs.forEach(s => collect(s, bucket));
  return bucket;
}
function blockHTML(b, typeOverride) {
  const type = typeOverride || b.type || "溢价";
  const keys = collect(b, []);
  AGG["blk:" + b.id] = keys;
  let h = '<div class="blk lvl' + (b.depth ? 4 : 3) + '" data-blk="' + b.id + '" data-type="' + type + '">';
  if (b.name) {
    h += '<div class="blk-hd"><h4>' + b.name + "</h4>" +
      (b.sub ? '<span class="sub">' + b.sub + "</span>" : "") +
      '<span class="spacer" style="flex:1"></span>' +
      '<span class="badge ' + TC[type] + '">' + type + "</span>" +
      progHTML("blk:" + b.id) + "</div>";
  }
  if (b.notes && b.notes.length) h += '<div class="notes">' + b.notes.map(n => "<p>" + n + "</p>").join("") + "</div>";
  if (b.items.length) h += itemsHTML(b.items, false);
  if (b.cutoff) h += '<div class="cutoff"><b>淘汰线</b>' + b.cutoff + "</div>";
  h += (b.subs || []).map(s => blockHTML(s, type)).join("");
  return h + "</div>";
}
function progHTML(id, wide) {
  return '<span class="prog" data-agg="' + id + '" role="progressbar" aria-valuemin="0" aria-valuemax="100" ' +
    'aria-valuenow="0" style="' + (wide ? "width:150px" : "") + '"><span class="bar tl"><i></i></span>' +
    '<span class="pl"></span></span>';
}

/* ----------------------------- overview ----------------------------- */
const MODEL_CARD = { "①": "2", "②": "3", "③": "4", "④": "5", "⑤": "6" };
function renderOverview() {
  const o = DATA.overview;
  const cardBy = {};
  DATA.cards.forEach(c => { cardBy[c.no] = c; });
  let h = "";

  h += '<h2 class="sect">30 秒速览：2027 和 2023 的差别在哪</h2><div class="grid2">' +
    o.quick.map((q, i) => '<div class="qcard"><div class="n">' + String(i + 1).padStart(2, "0") +
      "</div><p>" + q + "</p></div>").join("") + "</div>";

  h += '<h2 class="sect">能力模型：五层</h2>';
  const legend = DATA.scoring.legend;
  if (legend.length) {
    h += '<div class="grid2" style="margin-bottom:12px">' + legend.map(l =>
      '<div class="qcard" style="padding:10px 13px"><p style="font-size:13px">' + l + "</p></div>").join("") + "</div>";
  }
  h += '<div class="pyr">' + o.model.map(m => {
    const card = cardBy[MODEL_CARD[m.code]];
    const idx = "①②③④⑤".indexOf(m.code) + 1;
    let inner = '<div class="row"><span class="code">' + m.code + '</span><span class="nm">' + m.name +
      "</span><span class='ds muted'>" + m.desc + "</span>" +
      (card ? progHTML("card:" + card.no, true) : "") + "</div>";
    if (card && card.blocks.length > 1) {
      inner += '<div class="split">' + card.blocks.map(b =>
        '<span class="badge ' + TC[b.type] + '">' + esc(b.name.split("：")[0]) + " · " + b.type + "</span>").join("") + "</div>";
    }
    const w = 100 - (idx - 1) * 8;   // ① widest (base) → ⑤ narrowest (top)
    return '<button class="layer l' + idx + '" type="button" style="width:' + w + '%" data-goto="' +
      (card ? "card-" + card.no : "") + '">' + inner + "</button>";
  }).join("");
  const job = cardBy["7"];
  if (job) {
    h += '<button class="layer l5" type="button" data-goto="card-7" style="border-left:3px solid var(--convert)">' +
      '<div class="row"><span class="code">★</span><span class="nm">求职资产（转化层）</span>' +
      "<span class='ds muted'>" + esc(plain(job.title)) + "</span>" + progHTML("card:7", true) + "</div></button>";
  }
  h += "</div>";
  if (o.modelNote.length) h += '<div class="notes" style="margin-top:12px">' + o.modelNote.map(p => "<p>" + p + "</p>").join("") + "</div>";

  const q4 = o.quick.length >= 4 ? plain(o.quick[3]) : "";
  h += '<h2 class="sect">双轨面试：两条线都得准备好</h2><div class="tracks">' +
    '<div class="track a"><div class="t"><span class="badge tk">门票</span>不发电脑、只给纸笔：笔试 + 手撕代码</div>' +
    '<div class="d">决定你有没有机会开口 · 见第 2.1 节</div></div>' +
    '<div class="track b"><div class="t"><span class="badge pm">溢价</span>允许用 AI 的项目型 + 深度追问</div>' +
    '<div class="d">决定你能拿多高 · 见第 3–6 节</div></div></div>' +
    (q4 ? '<div class="notes" style="margin-top:10px"><p>' + esc(q4) + "</p></div>" : "");

  h += '<h2 class="sect">' + esc(plain(o.market.title || "市场底噪")) + "</h2>";
  if (o.market.notes.length) h += '<div class="notes">' + o.market.notes.map(p => "<p>" + p + "</p>").join("") + "</div>";
  h += '<div class="mkt">' + o.market.rows.slice(1).map(r =>
    '<div class="r"><div class="k">' + r[0] + '</div><div class="now">' + r[1] + '</div><div class="next">' + r[2] + "</div></div>"
  ).join("") + "</div>";

  $("#view-overview").innerHTML = h;
}

/* ----------------------------- checklist ----------------------------- */
function renderList() {
  let h = '<div class="toolbar">' +
    '<div class="search"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
    '<input id="q" type="search" placeholder="搜索清单条目，如 上下文 / MVCC / 埋雷 / eval" aria-label="搜索清单条目"></div>' +
    '<div class="chips" id="st"></div><div class="chips" id="ty"></div>' +
    '<span class="small muted" id="matchCount"></span></div>';
  DATA.cards.forEach(c => {
    AGG["card:" + c.no] = c.blocks.reduce((a, b) => collect(b, a), []);
    h += '<article class="card" id="card-' + c.no + '">' +
      '<div class="card-hd"><span class="dot">' + c.layer + "</span><h2>" + esc(stripGlyph(plain(c.title))) + "</h2>" +
      '<span class="spacer"></span>' + c.blocks.map(b => '<span class="badge ' + TC[b.type] + '">' + b.type + "</span>").join("") +
      progHTML("card:" + c.no) + "</div>";
    const notes = (c.notes || []).concat(c.prose || []);
    h += '<div class="card-bd">' + (notes.length ? '<div class="notes" style="margin-top:12px">' +
      notes.map(n => "<p>" + n + "</p>").join("") + "</div>" : "") +
      c.blocks.map(b => blockHTML(b)).join("") + "</div></article>";
  });
  h += '<div class="empty" id="noMatch" hidden>没有匹配的条目</div>';
  $("#view-list").innerHTML = h;
  wireFilters();
}
function allItems() { return $$("#view-list .item"); }
const filters = { q: "", st: "all", ty: "" };
function wireFilters() {
  $("#st").innerHTML = [["all", "全部"], ["todo", "未完成"], ["done", "已完成"]].map(v =>
    '<button class="chip" type="button" data-f="st" data-v="' + v[0] + '" aria-pressed="' +
    (filters.st === v[0]) + '">' + v[1] + "</button>").join("");
  const types = ["门票", "基础", "溢价", "转化"];
  $("#ty").innerHTML = types.map(t =>
    '<button class="chip tp" type="button" data-f="ty" data-v="' + t + '" style="--c:var(--' + TC[t] +
    ')" aria-pressed="' + (filters.ty === t) + '">' + t + "</button>").join("") +
    '<button class="chip tp" type="button" data-f="ty" data-v="" style="--c:var(--muted)" aria-pressed="' +
    (filters.ty === "") + '">全部类型</button>';
  $("#q").addEventListener("input", e => { filters.q = e.target.value.trim().toLowerCase(); applyFilters(); });
  $$(".chip", $("#view-list")).forEach(b => b.addEventListener("click", () => {
    const kind = b.dataset.f, v = b.dataset.v;
    filters[kind] = (filters[kind] === v) ? (kind === "st" ? "all" : "") : v;
    $$('.chip[data-f="' + kind + '"]').forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    applyFilters();
  }));
  applyFilters();
}
function applyFilters() {
  $$("#view-list .item").forEach(it => {
    const done = $("input", it).checked;
    const blk = it.closest(".blk");
    const ok = (!filters.q || it.dataset.s.indexOf(filters.q) >= 0) &&
      (filters.st === "all" || (filters.st === "done") === done) &&
      (!filters.ty || (blk && blk.dataset.type === filters.ty));
    it.hidden = !ok;
  });
  $$("#view-list .blk").forEach(b => {
    b.hidden = $$(".item", b).every(it => it.hidden);
  });
  let shown = 0;
  $$("#view-list .card").forEach(card => {
    const vis = $$(".item", card).filter(it => !it.hidden).length;
    card.hidden = vis === 0;
    shown += vis;
  });
  $("#noMatch").hidden = shown > 0;
  const total = allItems().length;
  $("#matchCount").textContent = (filters.q || filters.st !== "all" || filters.ty)
    ? "显示 " + shown + " / " + total + " 项" : "共 " + total + " 项 · 勾选状态自动保存在本机";
}

/* ----------------------------- self assessment ----------------------------- */
function renderScore() {
  const sc = DATA.scoring;
  let h = '<h2 class="sect">' + esc(plain(sc.title)) + "</h2>";
  const prose = (sc.prose || []).concat(sc.notes || []);
  if (prose.length) h += '<div class="notes">' + prose.map(p => "<p>" + p + "</p>").join("") + "</div>";
  h += '<div class="score-wrap"><div class="card"><div class="card-bd">' + sc.rows.map(r =>
    '<div class="score-row" data-row="' + r.k + '"><div><div class="nm">' + r.layer +
      '<span class="badge ' + TC[r.type] + '">' + r.type + "</span></div>" +
      '<div class="meta"><span>权重 ' + r.weight + '%</span><span>加权 <b data-w="' + r.k + '">0.00</b></span>' +
      '<button class="btn" type="button" data-gotoblk="' + r.link + '">去看清单</button></div></div>' +
      segHTML(r) +
      '<div class="next-act"><label for="act-' + r.k + '">下一动作</label>' +
      '<input id="act-' + r.k + '" data-act="' + r.k + '" type="text" placeholder="一句话：下一步具体做什么" value="' +
      attr(state.acts[r.k] || "") + '"></div></div>').join("") +
    '<div class="scale">' + [["0", "没概念"], ["1", "用过说不清"], ["2", "能独立完成并解释取舍"], ["3", "有证据且能教别人"]]
      .map(v => "<span>" + v[0] + " · " + v[1] + "</span>").join("") + "</div></div></div>" +
    '<div class="col"><div class="total" id="total"></div><div id="alertBox"></div>' +
    '<div class="card" style="margin-top:12px"><div class="card-bd">' +
    '<div class="sr" id="radarSR"></div><div id="radarBox"></div><div id="advice"></div>' +
    "</div></div></div></div>";

  const ev = DATA.evidence;
  h += '<h2 class="sect">' + esc(plain(ev.title)) + "</h2>";
  if ((ev.notes || []).length) h += '<div class="notes">' + ev.notes.map(n => "<p>" + n + "</p>").join("") + "</div>";
  h += '<div class="grid2">' + ev.rows.map(r => '<div class="qcard"><div class="n">' + r[0] + "</div><p>" + r[1] + "</p></div>").join("") + "</div>";
  $("#view-score").innerHTML = h;
  $$("[data-sc]").forEach(b => b.addEventListener("click", () => {
    state.scores[b.dataset.sc] = Number(b.dataset.v); save(); renderSeg(b.dataset.sc); refreshScore();
  }));
  $$("[data-act]").forEach(i => i.addEventListener("input", () => { state.acts[i.dataset.act] = i.value; save(); }));
  sc.rows.forEach(r => renderSeg(r.k));
}
function segHTML(r) {
  return '<div class="seg" data-seg="' + r.k + '" role="group" aria-label="' + attr(plain(r.layer)) + ' 自评得分">' +
    [0, 1, 2, 3].map(v => '<button type="button" data-sc="' + r.k + '" data-v="' + v + '" aria-label="' + v + ' 分">' + v + "</button>").join("") + "</div>";
}
function renderSeg(k) {
  const seg = $('[data-seg="' + k + '"]'); if (!seg) return;
  const v = state.scores[k];
  seg.className = "seg" + (v === undefined ? "" : " s" + v);
  $$("button", seg).forEach(b => b.setAttribute("aria-pressed", String(v === Number(b.dataset.v))));
}
function scoredRows() { return DATA.scoring.rows.filter(r => state.scores[r.k] !== undefined); }
function refreshScore() {
  const rows = DATA.scoring.rows;
  const scored = scoredRows();
  rows.forEach(r => {
    const el = $('[data-w="' + r.k + '"]');
    if (el) el.textContent = ((state.scores[r.k] || 0) * r.weight / 100).toFixed(2);
  });
  const w = scored.length ? rows.reduce((a, r) => a + (state.scores[r.k] || 0) * r.weight, 0) /
    rows.reduce((a, r) => a + r.weight, 0) : 0;
  const band = !scored.length ? ["nu", "还没打分"] :
    (w >= 2.4 ? ["b-hi", "可以主动进攻好机会"] : (w >= 2 ? ["b-mid", "边工作边补最弱两项"] : ["b-lo", "先进入 90 天计划，别急着海投"]));
  $("#total").innerHTML = '<span class="small muted">加权总分（0–3）</span><span class="v">' +
    (scored.length ? w.toFixed(2) : "—") + '</span><span class="band ' + (band[0] === "nu" ? "" : band[0]) +
    '" style="' + (band[0] === "nu" ? "color:var(--muted);border-color:var(--line);background:var(--surface2)" : "") + '">' +
    band[1] + '</span><span class="spacer" style="flex:1"></span><span class="small muted">已评 ' +
    scored.length + " / " + rows.length + " 项</span>";

  const pool = (DATA.scoring.prose || []).concat(DATA.scoring.notes || []).map(plain);
  const line = pool.filter(t => t.indexOf("门票优先") >= 0)[0];
  const alertMsg = line ? esc(line.replace(/^[\s\S]*?门票优先\s*[:：]\s*/, "")) : "门票项低于 2 分时，先补它再谈整体优化。";
  const lowTicket = rows.filter(r => r.type === "门票" && (state.scores[r.k] || 0) < 2);
  $("#alertBox").innerHTML = (!scored.length || !lowTicket.length) ? "" :
    '<div class="alert" style="margin-top:12px"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>' +
    "<div><b>门票告警</b><div>" + alertMsg + "</div></div></div>";

  const adv = [];
  if (!scored.length) adv.push("给 7 个维度各打一个分（0–3），加权总分、门票告警和能力形状才会出来。");
  else {
    const weak = scored.slice().sort((a, b) => (state.scores[a.k] || 0) - (state.scores[b.k] || 0)).slice(0, 2);
    adv.push("最弱两项：<b>" + weak.map(r => esc(plain(r.layer))).join("</b> 与 <b>") +
      "</b>——到「90 天计划」里挑对应动作，写进上面的“下一动作”。");
  }
  const tKeys = AGG["type:门票"] || [];
  const tTodo = tKeys.filter(k => !state.checks[k]).length;
  if (tTodo) adv.push("门票清单（2.1 节）还有 <b>" + tTodo + "</b> 项未打勾，纸笔轮最先出局的就是这里。");
  const flags = (AGG["flags"] || []).filter(k => state.checks[k]).length;
  if (flags) adv.push("红旗清单命中 <b>" + flags + "</b> 条：出现任意一条，先修再投。");
  $("#advice").innerHTML = adv.length ? '<div class="notes" style="margin-top:12px">' +
    adv.map(a => "<p>· " + a + "</p>").join("") + "</div>" : "";
  drawRadar(rows.map(r => state.scores[r.k] || 0), scored.length > 0);
}
/* radar -------------------------------------------------------------- */
let radarPrev = null, radarRAF = 0;
function radarPoints(vals, cx, cy, R) {
  const n = vals.length;
  return vals.map((v, i) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    const r = (Math.max(0, Math.min(3, v)) / 3) * R;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
}
function pathOf(pts) {
  return pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ") + "Z";
}
function drawRadar(vals, has) {
  const box = $("#radarBox"); if (!box) return;
  const W = 400, H = 330, cx = W / 2, cy = H / 2 + 2, R = 96;
  const rows = DATA.scoring.rows, n = rows.length;
  const at = i => -Math.PI / 2 + (i * 2 * Math.PI) / n;
  let g = "";
  [1, 2, 3].forEach(lv => {
    g += '<polygon class="grid" points="' + radarPoints(rows.map(() => lv), cx, cy, R)
      .map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ") + '"/>';
  });
  rows.forEach((r, i) => {
    g += '<line class="spoke" x1="' + cx + '" y1="' + cy + '" x2="' + (cx + R * Math.cos(at(i))).toFixed(1) +
      '" y2="' + (cy + R * Math.sin(at(i))).toFixed(1) + '"/>';
  });
  const labels = rows.map((r, i) => {
    const a = at(i), cos = Math.cos(a), sin = Math.sin(a);
    const lx = cx + (R + 14) * cos, ly = cy + (R + 14) * sin + 4;
    const anchor = Math.abs(cos) < .35 ? "middle" : (cos > 0 ? "start" : "end");
    return '<text class="ax' + (r.type === "门票" ? " strong" : "") + '" x="' + lx.toFixed(1) + '" y="' + ly.toFixed(1) +
      '" text-anchor="' + anchor + '">' + esc(r.axis) + "</text>" +
      (has ? '<text class="val" x="' + lx.toFixed(1) + '" y="' + (ly + 12).toFixed(1) + '" text-anchor="' + anchor +
        '">' + (state.scores[r.k] || 0) + "/3</text>" : "");
  }).join("");
  box.innerHTML = '<svg class="radar" viewBox="0 0 ' + W + " " + H + '" role="img" aria-labelledby="radarSR">' +
    g + '<path class="shape" id="radarPath" d="' + pathOf(radarPoints(vals, cx, cy, R)) + '"/>' + labels +
    (has ? "" : '<text class="ax" x="' + cx + '" y="' + cy + '" text-anchor="middle">打分后显示能力形状</text>') + "</svg>";
  $("#radarSR").textContent = "能力自评雷达图：" + rows.map((r, i) => r.axis + " " + vals[i] + " 分").join("，");
  if (isRTL || !has) { radarPrev = vals.slice(); return; }
  const from = (radarPrev || vals.map(() => 0)).slice();
  const t0 = performance.now(), dur = 320;
  cancelAnimationFrame(radarRAF);
  const step = now => {
    const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    const p = $("#radarPath"); if (!p) return;
    p.setAttribute("d", pathOf(radarPoints(vals.map((v, i) => from[i] + (v - from[i]) * e), cx, cy, R)));
    if (k < 1) radarRAF = requestAnimationFrame(step); else radarPrev = vals.slice();
  };
  radarRAF = requestAnimationFrame(step);
}

/* ----------------------------- levels / plan / flags / sources ----------------------------- */
function renderLevels() {
  const lv = DATA.levels;
  let h = '<h2 class="sect">' + esc(plain(lv.title)) + "</h2>";
  if (lv.notes.length) h += '<div class="notes">' + lv.notes.map(n => "<p>" + n + "</p>").join("") + "</div>";
  h += '<div class="lv">' + lv.cards.map(c => {
    AGG["blk:" + c.id] = collect(c, []);
    let inner = '<div class="lv-hd"><div class="yrs">' + esc(c.name) + "</div>" +
      (c.keyword ? '<div class="small muted">关键词：' + esc(c.keyword) + "</div>" : "") + "</div>" +
      '<div class="card-bd" style="padding-top:10px">' + progHTML("blk:" + c.id) + itemsHTML(c.items, false) + "</div>";
    if (c.cutoff) inner += '<div class="cutoff"><b>淘汰线</b>' + c.cutoff + "</div>";
    return '<article class="card">' + inner + "</article>";
  }).join("") + "</div>";
  $("#view-levels").innerHTML = h;
}
function renderPlan() {
  const pl = DATA.plan;
  let h = '<h2 class="sect">' + esc(plain(pl.title)) + "</h2>";
  if (pl.notes.length) h += '<div class="notes">' + pl.notes.map(n => "<p>" + n + "</p>").join("") + "</div>";
  h += '<div class="card"><div class="card-bd plan">' + pl.phases.map(ph => {
    AGG["blk:" + ph.id] = collect(ph, []);
    return '<div class="phase"><div class="when"><div class="w">' + esc(ph.week) + '</div><div class="t">' +
      esc(ph.name) + "</div>" + progHTML("blk:" + ph.id) + "</div><div>" + itemsHTML(ph.items, false) +
      (ph.notes.length ? '<div class="notes" style="margin-top:8px">' + ph.notes.map(n => "<p>" + n + "</p>").join("") + "</div>" : "") +
      "</div></div>";
  }).join("") + "</div></div>";
  $("#view-plan").innerHTML = h;
}
function renderFlags() {
  const f = DATA.flags;
  AGG["flags"] = f.items.map(i => i.k);
  $("#view-flags").innerHTML = '<h2 class="sect">' + esc(plain(f.title)) + "</h2>" +
    '<div class="count-line" id="flagCount"></div>' +
    '<div class="card flags"><div class="card-bd">' +
    (f.notes.length ? '<div class="notes" style="margin-top:12px">' + f.notes.map(n => "<p>" + n + "</p>").join("") + "</div>" : "") +
    '<div class="items">' + f.items.map(it => itemHTML(it, true)).join("") + "</div></div></div>";
}
function renderSources() {
  const s = DATA.sources;
  let h = '<h2 class="sect">' + esc(plain(s.title)) + "</h2><ul class='src'>" + s.items.map(i => "<li>" + i + "</li>").join("") + "</ul>";
  h += s.revisions.map(r => '<div class="rev">' + r + "</div>").join("");
  if (DATA.closing) h += '<div class="quote">' + DATA.closing + "</div>";
  h += '<div class="notes" style="margin-top:14px">' + DATA.usage.map(u => "<p>" + u + "</p>").join("") + "</div>";
  $("#view-src").innerHTML = h;
}

/* ----------------------------- shell: tabs, progress, wiring ----------------------------- */
const VIEWS = [
  ["overview", "速览"], ["list", "能力清单"], ["score", "自评打分"], ["levels", "分级门槛线"],
  ["plan", "90 天计划"], ["flags", "红旗清单"], ["src", "来源与修订"]
];
function renderTabs() {
  $("#tabs").innerHTML = VIEWS.map(v => '<button class="tab" role="tab" type="button" data-view="' + v[0] +
    '" aria-selected="false" aria-controls="view-' + v[0] + '">' + v[1] + '<span class="cnt" data-cnt="' + v[0] + '" hidden></span></button>').join("");
  $$(".tab").forEach(b => b.addEventListener("click", () => show(b.dataset.view)));
  $("#tabs").addEventListener("keydown", e => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const i = VIEWS.findIndex(v => v[0] === state.view);
    show(VIEWS[(i + (e.key === "ArrowRight" ? 1 : VIEWS.length - 1)) % VIEWS.length][0]);
    e.preventDefault();
  });
}
function show(v, keepHash) {
  state.view = v; save();
  if (location.hash.slice(1) !== v) { try { history.replaceState(null, "", "#" + v); } catch (e) {} }
  $$(".view").forEach(s => s.classList.toggle("on", s.id === "view-" + v));
  $$(".tab").forEach(b => b.setAttribute("aria-selected", String(b.dataset.view === v)));
  window.scrollTo({ top: 0, behavior: isRTL ? "auto" : "smooth" });
}
function gotoCard(id) {
  show("list");
  const el = document.getElementById(id) || $('[data-blk="' + id + '"]');
  if (!el) return;
  el.scrollIntoView({ block: "start", behavior: isRTL ? "auto" : "smooth" });
  el.style.transition = "box-shadow .2s"; el.style.boxShadow = "0 0 0 3px var(--accent)";
  setTimeout(() => { el.style.boxShadow = ""; }, 900);
}
function progressOf(id) {
  const keys = AGG[id] || [];
  return { done: keys.filter(k => state.checks[k]).length, total: keys.length };
}
function refresh() {
  Object.keys(AGG).forEach(id => {
    $$('[data-agg="' + id + '"]').forEach(box => {
      const { done, total } = progressOf(id);
      const pct = total ? Math.round((done / total) * 100) : 0;
      const bar = $(".bar i", box); if (bar) { bar.className = ""; bar.style.width = pct + "%"; }
      const pl = $(".pl", box); if (pl) pl.textContent = done + "/" + total;
      box.setAttribute("aria-valuenow", String(pct));
      box.setAttribute("aria-label", "已完成 " + done + " / " + total);
    });
  });
  $$("[data-blk]").forEach(b => {
    const keys = AGG["blk:" + b.dataset.blk] || [];
    b.classList.toggle("done-all", keys.length > 0 && keys.every(k => state.checks[k]));
  });
  const all = AGG["all"] || [];
  const done = all.filter(k => state.checks[k]).length;
  const pct = all.length ? Math.round((done / all.length) * 100) : 0;
  $("#ringArc").setAttribute("stroke-dashoffset", String(151 - (151 * pct) / 100));
  $("#ringVal").textContent = pct + "%";
  $("#ring").setAttribute("aria-label", "总体达成进度 " + pct + "%（已勾选 " + done + " / " + all.length + " 项）");
  const types = {};
  ["门票", "基础", "溢价", "转化"].forEach(t => {
    const keys = AGG["type:" + t] || [];
    types[t] = keys.filter(k => state.checks[k]).length + "/" + keys.length;
  });
  $("#legend").innerHTML = ["门票", "基础", "溢价", "转化"].map(t =>
    '<span><b>' + types[t] + "</b> · " + t + "</span>").join("") +
    '<span style="color:var(--danger)"><b>' + (AGG["flags"] || []).filter(k => state.checks[k]).length +
    "</b> · 红旗命中</span>";
  const lc = $('[data-cnt="list"]'); if (lc) { lc.hidden = false; lc.textContent = done + "/" + all.length; }
  const fc = $('[data-cnt="flags"]');
  if (fc) { const n = (AGG["flags"] || []).filter(k => state.checks[k]).length; fc.hidden = false; fc.textContent = n; fc.classList.toggle("warn", n > 0); }
  const cl = $("#flagCount");
  if (cl) {
    const n = (AGG["flags"] || []).filter(k => state.checks[k]).length;
    cl.innerHTML = "命中 <b>" + n + "</b> / " + (AGG["flags"] || []).length + " 条" +
      (n ? " · 按第 10 节标题的口径：出现任意一条，先修再投" : " · 勾掉你确实命中的那条");
  }
  refreshScore();
  if (filters.q || filters.st !== "all" || filters.ty) applyFilters();
}
function init() {
  $("#kicker").textContent = "可验证的行为清单 · 每季自评 · " + DATA.cards.reduce((a, c) => a + c.blocks.length, 0) + " 个能力块";
  $("#docTitle").textContent = plain(DATA.docTitle);
  $("#lead").textContent = DATA.usage.length ? plain(DATA.usage[0]) : "";
  renderTabs(); renderOverview(); renderList(); renderScore(); renderLevels(); renderPlan(); renderFlags(); renderSources();
  const uniq = {};
  Object.keys(AGG).forEach(id => {
    if (id === "flags" || id === "all" || id.indexOf("type:") === 0) return;
    AGG[id].forEach(k => { uniq[k] = 1; });
  });
  AGG["all"] = Object.keys(uniq);
  ["门票", "基础", "溢价", "转化"].forEach(t => {
    const seen = {};
    DATA.cards.forEach(c => c.blocks.filter(b => b.type === t).forEach(b => collect(b, []).forEach(k => { seen[k] = 1; })));
    AGG["type:" + t] = Object.keys(seen);
  });
  document.addEventListener("change", e => {
    const el = e.target;
    if (!el.matches || !el.matches("input[type=checkbox][data-k]")) return;
    state.checks[el.dataset.k] = el.checked;
    const item = el.closest(".item");
    if (item) item.classList.toggle(item.classList.contains("flag") ? "hit" : "done", el.checked);
    save(); refresh();
  });
  document.addEventListener("click", e => {
    const g = e.target.closest("[data-goto]");
    if (g && g.dataset.goto) { gotoCard(g.dataset.goto); return; }
    const gb = e.target.closest("[data-gotoblk]");
    if (gb) { gotoCard("card-" + gb.dataset.gotoblk.split(".")[0]); }
  });
  const reset = $("#resetBtn");
  if (reset) reset.addEventListener("click", () => {
    if (!window.confirm("清空本机保存的勾选与打分？")) return;
    state.checks = {}; state.scores = {}; state.acts = {}; save();
    $$("input[type=checkbox][data-k]").forEach(i => { i.checked = false; });
    $$(".item").forEach(i => i.classList.remove("done", "hit"));
    $$("[data-act]").forEach(i => { i.value = ""; });
    DATA.scoring.rows.forEach(r => renderSeg(r.k));
    refresh();
  });
  const pr = $("#printBtn"); if (pr) pr.addEventListener("click", () => window.print());
  $("#footNote").innerHTML = "源文件：<code>" + attr(SRCFILE) + "</code> · 本页由 <code>tools/build_web.py</code> 生成，勾选与打分只存在这台设备的浏览器里。";
  $("#footMeta").innerHTML = DATA.closing ? "版本 " + (DATA.sources.revisions.length ? "v2.1" : "v2") + " · " + BUILDSTAMP : "";
  $$(".item").forEach(i => i.classList.toggle(i.classList.contains("flag") ? "hit" : "done", $("input", i).checked));
  const hash = location.hash.slice(1);
  if (VIEWS.some(v => v[0] === hash)) state.view = hash;
  show(state.view || "overview", true);
  window.addEventListener("hashchange", () => {
    const h = location.hash.slice(1);
    if (VIEWS.some(v => v[0] === h)) show(h, true);
  });
  refresh();
}
init();
'''

TAIL = '''
</script>
</body>
</html>
'''

SRCFILE_JS = 'const SRCFILE = "%s";\nconst BUILDSTAMP = "%s";\n'


def main():
    from datetime import date

    doc = parse(SRC.read_text(encoding="utf-8"))
    views = refine(build_views(doc))
    payload = json.dumps(views, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    stamp = "生成于 " + date.today().isoformat()
    page = (HEAD + CSS2 + BODY.replace("__DATA__", payload)
            + (SRCFILE_JS % (SRC.name, stamp)) + JS + TAIL)
    DST.write_text(page, encoding="utf-8")
    n = sum(len(b["items"]) + block_count(b) for c in views["cards"] for b in c["blocks"])
    print(f"wrote {DST.name}: {len(page)/1024:.0f} KB · {n} checklist items · "
          f"{len(views['levels']['cards'])} levels · {len(views['plan']['phases'])} phases · "
          f"{len(views['flags']['items'])} flags")


if __name__ == "__main__":
    main()
