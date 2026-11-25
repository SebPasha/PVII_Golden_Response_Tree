#!/usr/bin/env python3
"""Place strategies on the three governance levers restored on 25 November 2026. No model calls.

    python3 restore_levers.py <migration out folder>

The paid mapping runs (17 to 19 November) used the tree without LV-177 (foresight), LV-178 (development
planning) and LV-190 (coordination across government), so the strategies that belong on them went to the
General governance branch. This moves a General governance strategy onto one of those levers when its name or
objective names that action in so many words. Rows the mapping put there by rule (budget
overhead lines) are left alone. The rows say how they were placed (depth_basis), so a later paid re-map can
replace them. Rewrites strategies.csv and the n_on_lever counts in plans.csv of every source folder under <out>.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
TREE = json.load(open(os.path.join(HERE, "..", "tree", "v4", "tree_v4.json"), encoding="utf-8"))
LV = {lv["lever_id"]: lv for lv in TREE["levers"]}
SUB = {s["code"]: s for s in TREE["subpillars"]}
PIL = {p["code"]: p["name"] for p in TREE["pillars"]}
BASIS = "rule: restored lever, by wording (25 Nov 2026)"

# checked in this order; the first that matches wins
RULES = [
    ("LV-177", r"\bforesight|\bscenario (planning|analysis|building)|horizon[- ]scan|futures? (studies|thinking|lab|unit)|"
               r"long[- ]term (strategy|strategic|vision|perspective)|strategic (foresight|anticipation)"),
    ("LV-178", r"development plan|national plan|five[- ]year plan|planning (system|process|framework|commission|agency|"
               r"ministry|capacit|function|and budget|and implementation)|investment (plan|programme|program)|"
               r"medium[- ]term (plan|development)|plan implementation|implementation of the (plan|national)|"
               r"(integrated|national|development|economic|spatial) planning"),
    ("LV-190", r"coordinat\w* (mechanism|body|bodies|committee|council|across|among|between|of (ministr|agenc|sector|polic|government))|"
               r"whole[- ]of[- ](the[- ])?government|inter[- ]?(ministerial|agency|governmental|sectoral)|polic(y|ies) coheren|"
               r"cross[- ]?(sectoral|sector|agency|ministerial|government) (coordinat|mechanism|committee|council|platform|integration)|intergovernmental|vertical(ly)? (integrat|coordinat)|"
               r"central[- ]local (relations|coordination)"),
]
RX = [(lid, re.compile(rx, re.I)) for lid, rx in RULES]


def place(r):
    if r["node_id"] != "H-SGO" or "rule" in (r.get("depth_basis") or ""):
        return None
    text = " ".join(r.get(k) or "" for k in ("name", "objective"))
    for lid, rx in RX:
        if rx.search(text):
            return lid
    return None


total = {}
for sub in ["", "sector", "unga", "budget"]:
    d = os.path.join(OUT, sub) if sub else OUT
    sp = os.path.join(d, "strategies.csv")
    if not os.path.exists(sp):
        continue
    with open(sp, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        cols, rows = rd.fieldnames, list(rd)
    n = {}
    for r in rows:
        lid = place(r)
        if not lid:
            continue
        lv = LV[lid]
        s = SUB[lv["subpillar_code"]]
        r.update({"node_id": lid, "level": "L3", "depth_basis": BASIS, "group_id": lv["group_id"], "group": lv["group"],
                  "family_id": lv["family_id"], "family": lv["family"], "lever_id": lid, "lever": lv["lever"],
                  "subpillar": s["name"], "pillar_rhdr": PIL[s["pillar"]],
                  "reason": "moved from General governance to a restored lever by wording; mapping said: " + (r.get("reason") or "")})
        n[lid] = n.get(lid, 0) + 1
    with open(sp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    # plan counts follow the rows
    pp = os.path.join(d, "plans.csv")
    if os.path.exists(pp) and n:
        with open(pp, encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            pcols, plans = rd.fieldnames, list(rd)
        on = {}
        for r in rows:
            if r["lever_id"]:
                on[r["plan_id"]] = on.get(r["plan_id"], 0) + 1
        if "n_on_lever" in pcols:
            for p in plans:
                p["n_on_lever"] = on.get(p["plan_id"], 0)
            with open(pp, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=pcols)
                w.writeheader()
                w.writerows(plans)
    total[sub or "national"] = n
    print("%-9s %s" % (sub or "national", ", ".join("%s %d" % kv for kv in sorted(n.items())) or "none"))
