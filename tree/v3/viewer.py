"""Write tree_v3_viewer.html, a standalone page for browsing mother tree v3.

    cd tree/v3 && python3 viewer.py [country_dir]

Reads tree_v3.json and viewer_template.html. If thailand/ (or the folder given) holds a country
stack from the workflow (strategies.csv and plans.csv, mapped on tree v3), the page also shows
that country on the tree, plan by plan. No model calls.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

tree = json.load(open(os.path.join(HERE, "tree_v3.json"), encoding="utf-8"))

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
                                         "examples", "pathway_ids", "sdg_targets", "risks",
                                         "conditional_risks", "assets")} for f in tree["families"]],
    "pathways": [{k: p.get(k, "") for k in ("pathway_id", "pathway", "family_id", "causal_input", "transmission",
                                             "outcome", "conditions", "distinction", "evidence", "risks",
                                             "conditional_risks", "merged_into", "added_in", "revised")}
                 for p in tree["pathways"]],
}



def country(folder):
    """The country stack in a compact form: plans by start year, one short row per strategy."""
    sp, pp = os.path.join(folder, "strategies.csv"), os.path.join(folder, "plans.csv")
    if not (os.path.exists(sp) and os.path.exists(pp)):
        return None
    csv.field_size_limit(10 ** 8)
    plans = list(csv.DictReader(open(pp, encoding="utf-8")))
    rows = list(csv.DictReader(open(sp, encoding="utf-8")))
    seen = {r["plan_id"] for r in rows}
    plans = [p for p in plans if p["plan_id"] in seen]
    order = {"ndp": 0, "vision": 1, "sector": 2}
    plans.sort(key=lambda p: (order.get(p.get("doc_type", ""), 3), int(p.get("period_start") or 0), p["plan_id"]))
    idx = {p["plan_id"]: i for i, p in enumerate(plans)}
    out = []
    for r in rows:
        if r["plan_id"] not in idx:
            continue
        try:
            risks = json.loads(r.get("related_risks") or "[]")
        except ValueError:
            risks = []
        level = r.get("level", "")
        if not level:
            level = "NEW"
        elif level == "L1":
            level = "GRP"
        out.append([idx[r["plan_id"]], r.get("name", ""), (r.get("objective") or "")[:220], level,
                    r.get("family_id", ""), r.get("pathway_id", ""), r.get("group_id", ""), r.get("node_id", ""),
                    r.get("sector_canonical") or r.get("sector", ""), r.get("response_orientation", ""), risks])
    return {
        "name": rows[0].get("country") or os.path.basename(os.path.normpath(folder)).title() if rows else "",
        "plans": [{"id": p["plan_id"], "doc_type": p.get("doc_type", ""), "edition": p.get("edition", ""),
                   "title": p.get("plan_title", ""), "start": int(p.get("period_start") or 0),
                   "end": int(p.get("period_end") or 0), "published": p.get("published", "")} for p in plans],
        "rows": out,
        "skipped": [{"title": p.get("plan_title", ""), "status": p.get("status", "")} for p in
                    csv.DictReader(open(pp, encoding="utf-8")) if p["plan_id"] not in seen],
    }


folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "thailand")
data["country"] = country(folder)
if data["country"]:
    print("country: %s, %d plans, %d strategies" % (data["country"]["name"], len(data["country"]["plans"]),
                                                  len(data["country"]["rows"])))

template = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
out = template.replace("/*TREE_DATA*/null", blob)
with open(os.path.join(HERE, "tree_v3_viewer.html"), "w", encoding="utf-8") as f:
    f.write(out)
print("wrote tree_v3_viewer.html (%d groups, %d families, %d pathways, %.0f KB)" % (
    len(data["groups"]), len(data["families"]), len(data["pathways"]), len(out) / 1024))
