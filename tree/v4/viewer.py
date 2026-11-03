"""Write tree_v4_viewer.html, a standalone page for browsing mother tree v4 (group > family > lever).

    cd tree/v4 && python3 viewer.py [strategies.csv ...]

Reads tree_v4.json and viewer_template.html. The country layer comes from one or more strategies CSVs
in the v4 output schema (lever_id, lever, pathway_id, reason, depth_basis, ...). With no arguments it
uses thailand/strategies*.csv here if present, else lifts the v3 Thai stack (../v3/thailand/strategies.csv)
onto the v4 levers through each pathway's lever_id and marks the page provisional. A CSV without a
lever_id column is always lifted that way. Plans come from plans.csv beside the CSV when there is one,
else from the plan columns of the strategy rows. No model calls.
"""
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(10 ** 9)

tree = json.load(open(os.path.join(HERE, "tree_v4.json"), encoding="utf-8"))
MERGED = tree["meta"].get("merged_pathways", {})
PW_LEVER = {p["pathway_id"]: p["lever_id"] for p in tree["pathways"]}
LEVER_FAM = {lv["lever_id"]: lv["family_id"] for lv in tree["levers"]}
FAM_GROUP = {f["family_id"]: f["group_id"] for f in tree["families"]}

data = {
    "built": tree["meta"].get("built", ""),
    "pillars": tree["pillars"],
    "subpillars": tree["subpillars"],
    "holding": tree["holding"],
    "risks": tree["risks"],
    "assets": {a["asset_id"]: a["asset"] for a in tree["assets"]},
    "groups": [{k: g[k] for k in ("group_id", "group", "subpillar_code", "basis", "definition",
                                   "family_ids", "sdg_targets", "risks")} for g in tree["groups"]],
    "families": [{k: f.get(k) for k in ("family_id", "family", "group_id", "subpillar_code", "definition",
                                         "examples", "lever_ids", "pathway_ids", "sdg_targets", "risks",
                                         "conditional_risks", "assets")} for f in tree["families"]],
    "levers": [{k: lv.get(k) for k in ("lever_id", "lever", "lever_full", "family_id", "joins_when", "joins_not",
                                        "pathway_ids", "risks", "entry_points", "intervention_evidence",
                                        "evidence_finding", "evidence_strength", "evidence_design", "evidence_fit",
                                        "evidence_basis", "evidence_checked", "evidence_verified", "evidence_url",
                                        "framework_source", "framework_where", "framework_says", "framework_refs")}
               for lv in tree["levers"]],
    "pathways": [{k: p.get(k, "") for k in ("pathway_id", "pathway", "family_id", "lever_id", "causal_input",
                                             "transmission", "outcome", "conditions", "distinction", "evidence",
                                             "risks", "conditional_risks", "added_in", "revised")}
                 for p in tree["pathways"]],
    "merged": MERGED,
}


def placement(r, lifted):
    """(level, family_id, lever_id, pathway_id, group_id) for one row, on tree v4."""
    level = (r.get("level") or "").strip()
    pw = (r.get("pathway_id") or "").strip()
    pw = MERGED.get(pw, pw)
    fam = (r.get("family_id") or "").strip()
    grp = (r.get("group_id") or "").strip()
    if lifted:
        lev = PW_LEVER.get(pw, "") if level == "L3" else ""
    else:
        lev = (r.get("lever_id") or "").strip()
        node = (r.get("node_id") or "").strip()
        if not lev and node.startswith("LV-"):
            lev = node
    if lev and lev not in LEVER_FAM:
        lev = ""
    if not lev:
        pw = ""
    if lev:
        fam = LEVER_FAM[lev]
    if fam and fam in FAM_GROUP:
        grp = FAM_GROUP[fam]
    if lev:
        code = "LV"
    elif level in ("STD", "GOAL"):
        code = level
    elif fam:
        code = "L2"
    elif grp or level == "L1":
        code = "GRP"
    else:
        code = "NEW"
    return code, fam, lev, pw, grp


def read_plans(path):
    pp = os.path.join(os.path.dirname(path), "plans.csv")
    return list(csv.DictReader(open(pp, encoding="utf-8"))) if os.path.exists(pp) else []


def country(paths):
    """The country stack in a compact form: plans by start year, one short row per strategy."""
    rows, plans_csv, lifted_any = [], {}, False
    for path in paths:
        rd = csv.DictReader(open(path, encoding="utf-8"))
        lifted = "lever_id" not in (rd.fieldnames or [])
        lifted_any = lifted_any or lifted
        for r in rd:
            # a row from an older run (no lever_id, placed on a pathway) is lifted onto the lever
            r["_lifted"] = lifted or (not (r.get("lever_id") or "").strip() and (r.get("tree_version") or "") != "v4")
            rows.append(r)
        for p in read_plans(path):
            plans_csv.setdefault(p["plan_id"], p)
    if not rows:
        return None
    seen = {r["plan_id"] for r in rows}
    plans = {pid: p for pid, p in plans_csv.items() if pid in seen}
    for r in rows:  # plans missing from plans.csv: take them from the strategy rows
        if r["plan_id"] not in plans:
            plans[r["plan_id"]] = {k: r.get(k, "") for k in ("plan_id", "doc_type", "edition", "plan_title",
                                                               "period_start", "period_end", "published")}
    plans = list(plans.values())
    order = {"ndp": 0, "vision": 1, "sector": 2}
    plans.sort(key=lambda p: (order.get(p.get("doc_type", ""), 3), int(p.get("period_start") or 0), p["plan_id"]))
    idx = {p["plan_id"]: i for i, p in enumerate(plans)}
    out = []
    for r in rows:
        try:
            risks = json.loads(r.get("related_risks") or "[]")
        except ValueError:
            risks = []
        code, fam, lev, pw, grp = placement(r, r["_lifted"])
        reason = "" if r["_lifted"] else (r.get("reason") or "")[:200]
        out.append([idx[r["plan_id"]], r.get("name", ""), (r.get("objective") or "")[:200], code, fam, lev, pw, grp,
                    r.get("sector_canonical") or r.get("sector", ""), r.get("response_orientation", ""), risks, reason])
    first = rows[0]
    return {
        "name": first.get("country") or "Country",
        "provisional": lifted_any,
        "lifted_plans": sorted({r.get("plan_id", "") for r in rows if r["_lifted"]}),
        "sources": [os.path.relpath(p, HERE) for p in paths],
        "plans": [{"id": p["plan_id"], "doc_type": p.get("doc_type", ""), "edition": p.get("edition", ""),
                   "title": p.get("plan_title", ""), "start": int(p.get("period_start") or 0),
                   "end": int(p.get("period_end") or 0), "published": p.get("published", "")} for p in plans],
        "rows": out,
        "skipped": [{"title": p.get("plan_title", ""), "status": p.get("status", "")}
                    for pid, p in plans_csv.items() if pid not in seen],
    }


paths = sys.argv[1:]
if not paths:
    paths = sorted(glob.glob(os.path.join(HERE, "thailand", "strategies*.csv")))
if not paths:
    paths = [os.path.join(HERE, "..", "v3", "thailand", "strategies.csv")]
paths = [os.path.abspath(p) for p in paths if os.path.exists(p)]
data["country"] = country(paths) if paths else None
if data["country"]:
    c = data["country"]
    nlv = sum(1 for r in c["rows"] if r[3] == "LV")
    print("country: %s, %d plans, %d strategies, %d on a lever%s" % (
        c["name"], len(c["plans"]), len(c["rows"]), nlv,
        " (provisional: v3 placements lifted onto v4 levers)" if c["provisional"] else ""))

template = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
out = template.replace("/*TREE_DATA*/null", blob)
with open(os.path.join(HERE, "tree_v4_viewer.html"), "w", encoding="utf-8") as f:
    f.write(out)
print("wrote tree_v4_viewer.html (%d groups, %d families, %d levers, %d pathways, %.0f KB)" % (
    len(data["groups"]), len(data["families"]), len(data["levers"]), len(data["pathways"]), len(out) / 1024))
