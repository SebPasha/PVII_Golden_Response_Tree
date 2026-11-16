"""Write tree_v4_world_viewer.html: mother tree v4 with every country of the earlier run on it.

    cd tree/v4/poc && python3 viewer.py <folder with strategies.csv and plans.csv from reshape.py> [out.html]

Tab 1 is the mother tree for all countries or one region; tab 2 is one country, plan by plan.
Reads ../tree_v4.json and viewer_template.html here. No model calls.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "tree_v4_world_viewer.html")
csv.field_size_limit(10 ** 9)

tree = json.load(open(os.path.join(HERE, "..", "tree_v4.json"), encoding="utf-8"))
MERGED = tree["meta"].get("merged_pathways", {})
DROPPED = {d["lever_id"]: d for d in tree["meta"].get("dropped_levers", [])}
PW_LEVER = {p["pathway_id"]: p["lever_id"] or ("%s (dropped)" % p["dropped_lever"] if p.get("dropped_lever") else p["pathway_id"])
            for p in tree["pathways"]}


def lever_ids(text):
    """A test that names pathways (L3-xxx) names the levers that hold them instead."""
    out = re.sub(r"\bL3-\d{3}\b", lambda m: PW_LEVER.get(MERGED.get(m.group(0), m.group(0)), m.group(0)), text or "")
    prev = None
    while prev != out:
        prev = out
        out = re.sub(r"\b(LV-\d{3})((?:,\s*|\s+and\s+|\s+or\s+))\1\b", r"\1", out)
    return out


def lever_row(lv):
    row = {k: lv.get(k) for k in ("lever_id", "lever", "lever_full", "family_id", "joins_when", "joins_not", "risks",
                                  "intervention_evidence", "evidence_finding", "evidence_strength", "evidence_design",
                                  "evidence_fit", "evidence_url", "framework_source", "framework_says",
                                  "backing_score", "backing_grade", "framework_status", "theory_n")}
    own = re.escape(lv["lever_id"])
    for k in ("joins_when", "joins_not"):
        t = lever_ids(row[k])
        t = re.sub(r"\s*\(%s\)" % own, "", t)
        row[k] = re.sub(r",\s*%s\b|\b%s,\s*" % (own, own), "", t)
    return row


data = {
    "built": tree["meta"].get("built", ""),
    "pillars": tree["pillars"], "subpillars": tree["subpillars"], "holding": tree["holding"], "risks": tree["risks"],
    "assets": {},
    "groups": [{k: g[k] for k in ("group_id", "group", "subpillar_code", "basis", "definition", "family_ids",
                                   "sdg_targets", "risks")} for g in tree["groups"]],
    "families": [{k: f.get(k) for k in ("family_id", "family", "group_id", "subpillar_code", "definition", "examples",
                                         "lever_ids", "sdg_targets", "risks")} | {
        "conditional_risks": [{k: c[k] for k in c if k != "pathway_id"} if isinstance(c, dict) else c
                              for c in f.get("conditional_risks") or []]} for f in tree["families"]],
    "levers": [lever_row(lv) for lv in tree["levers"]],
    "dropped": [{k: d.get(k) for k in ("lever_id", "lever", "family_id")} for d in DROPPED.values()],
}

plans = list(csv.DictReader(open(os.path.join(SRC, "plans.csv"), encoding="utf-8")))
rows = list(csv.DictReader(open(os.path.join(SRC, "strategies.csv"), encoding="utf-8")))
REG_ORDER = ["South-East Asia", "South Asia", "East Asia", "Pacific", "Europe and Central Asia", "Arab States",
             "Africa", "Latin America and the Caribbean"]
countries, cidx = [], {}
for p in sorted(plans, key=lambda p: (REG_ORDER.index(p["region"]), p["country"])):
    if p["slug"] not in cidx:
        cidx[p["slug"]] = len(countries)
        countries.append({"name": p["country"], "slug": p["slug"], "region": p["region"]})
plans.sort(key=lambda p: (cidx[p["slug"]], p["doc_type"] != "ndp", int(p["period_start"]), int(p["period_end"])))
pidx = {p["plan_id"]: i for i, p in enumerate(plans)}


class Dict:
    """Strings stored once and referred to by position."""
    def __init__(self):
        self.items, self.pos = [""], {"": 0}

    def __call__(self, s):
        s = s or ""
        if s not in self.pos:
            self.pos[s] = len(self.items)
            self.items.append(s)
        return self.pos[s]


sectors, objs, targets, instruments, sids = Dict(), Dict(), Dict(), Dict(), Dict()
RISK = {r: i for i, r in enumerate(tree["risks"])}
CODE = {"L3": "LV", "L2": "L2", "L1": "GRP", "STD": "STD", "GOAL": "GOAL"}
out = []
for r in rows:
    code = CODE.get(r["level"], "NEW")
    # [plan, name, objective, level, family, lever, group, sector, orientation, risks, objective label, target,
    #  instrument, passages, source strategy]
    out.append([pidx[r["plan_id"]], r["name"], r["objective"], code, r["family_id"], r["lever_id"], r["group_id"],
                sectors(r["sector"]), r["response_orientation"],
                [RISK[x] for x in json.loads(r["related_risks"] or "[]") if x in RISK],
                objs(r["tree_objective"]), targets(r["target_label"] or r["target_group"]),
                instruments(r["instrument_label"] or r["instrument"]), int(r["n_mentions"] or 0),
                sids(r["source_strategy_key"])])
data["set"] = {
    "regions": [x for x in REG_ORDER if any(c["region"] == x for c in countries)],
    "countries": countries,
    "plans": [{"id": p["plan_id"], "c": cidx[p["slug"]], "doc_type": p["doc_type"], "edition": p["edition"],
               "title": p["plan_title"], "start": int(p["period_start"]), "end": int(p["period_end"]),
               "src": p["period_source"]} for p in plans],
    "sectors": sectors.items, "objs": objs.items, "targets": targets.items, "instruments": instruments.items,
    "rows": out, "n_source": len(sids.items) - 1,
}

template = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = template.replace("/*TREE_DATA*/null", blob)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote %s: %d countries, %d plans, %d rows, %d on a lever, %.0f KB" % (
    os.path.basename(OUT), len(countries), len(plans), len(out), sum(1 for r in out if r[5]), len(html) / 1024))
