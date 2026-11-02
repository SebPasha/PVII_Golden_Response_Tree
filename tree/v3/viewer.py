"""Write tree_v3_viewer.html, a standalone page for browsing mother tree v3.

    cd tree/v3 && python3 viewer.py

Reads tree_v3.json and viewer_template.html; no model calls, no other inputs.
"""
import json
import os

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

template = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
out = template.replace("/*TREE_DATA*/null", blob)
with open(os.path.join(HERE, "tree_v3_viewer.html"), "w", encoding="utf-8") as f:
    f.write(out)
print("wrote tree_v3_viewer.html (%d groups, %d families, %d pathways, %.0f KB)" % (
    len(data["groups"]), len(data["families"]), len(data["pathways"]), len(out) / 1024))
