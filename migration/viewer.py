"""Write tree_v4_world_viewer.html: mother tree v4 with every country of the earlier run on it.

    cd migration && python3 viewer.py <folder with strategies.csv and plans.csv from reshape.py> [out.html]

The other sources (sources.py writes them to <folder>/sector, unga and budget) go beside the page as
rows_<source>.js, read when a reader switches that source on, so the page itself stays small.

Tab 1 is the mother tree for all countries or one region; tab 2 is one country, plan by plan. A details
table under the tree lists the strategies behind whatever is selected, sortable, each opening to its
underlying data. The passage text under a strategy is too large for the page, so it goes in a folder
detail/ beside the page (one file per national plan edition, and one per country for each other source, from passages.csv), which the page reads when a
strategy is opened. Reads ../tree/v4/tree_v4.json, viewer_template.html and forest.js (the country forest) here. No model calls.
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

tree = json.load(open(os.path.join(HERE, "..", "tree", "v4", "tree_v4.json"), encoding="utf-8"))
MERGED = tree["meta"].get("merged_pathways", {})
DROPPED = {d["lever_id"]: d for d in tree["meta"].get("dropped_levers", [])}
PW_LEVER = {p["pathway_id"]: p["lever_id"] or p["pathway_id"]
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
    "dropped": [],
}
FAMS = {f["family_id"]: f for f in data["families"]}
# the page draws all 33 framework families (the governance ones follow the Future-Ready Governance Index, as in the
# framework). Below them it shows the live tree: levers dropped by the literature review are not drawn, and a family
# left without a lever is drawn only where its framework family has no other family (no strategy is placed on it)
for g in data["groups"]:
    live = [x for x in g["family_ids"] if FAMS[x]["lever_ids"]]
    g["family_ids"] = live or g["family_ids"]
KEEP_F = {x for g in data["groups"] for x in g["family_ids"]}
data["families"] = [f for f in data["families"] if f["family_id"] in KEEP_F]

SOURCES = [("plans", SRC, "National plans")] + [(k, os.path.join(SRC, k), lab) for k, lab in (
    ("sector", "Sector plans"), ("unga", "UNGA statements"), ("budget", "Budgets"))
    if os.path.exists(os.path.join(SRC, k, "strategies.csv"))]
# documents taken off the page by decision (excluded_plans.json here: plan_id -> why); the Audit tab lists them
XPATH = os.path.join(HERE, "excluded_plans.json")
EXCL = json.load(open(XPATH, encoding="utf-8")) if os.path.exists(XPATH) else {}
plans = [p for _, d, _ in SOURCES for p in csv.DictReader(open(os.path.join(d, "plans.csv"), encoding="utf-8"))]
excluded = [{"country": p["country"], "title": p["plan_title"], "why": EXCL[p["plan_id"]]} for p in plans if p["plan_id"] in EXCL]
plans = [p for p in plans if p["plan_id"] not in EXCL]
# source files taken out of the edition they were merged into (reshape.py skips them): listed on the Audit tab too
XD = os.path.join(HERE, "excluded_documents.json")
NM = {p["slug"]: p["country"] for p in plans}
excluded += [{"country": NM.get(d["slug"], d["slug"]), "title": "file %s, merged into %s" % (d["file"], d["edition"]), "why": d["why"]}
             for d in (json.load(open(XD, encoding="utf-8")) if os.path.exists(XD) else [])]
REG_ORDER = ["South-East Asia", "South Asia", "East Asia", "Pacific", "Europe and Central Asia", "Arab States",
             "Africa", "Latin America and the Caribbean"]
countries, cidx = [], {}
for p in sorted(plans, key=lambda p: (REG_ORDER.index(p["region"]), p["country"])):
    if p["slug"] not in cidx:
        cidx[p["slug"]] = len(countries)
        countries.append({"name": p["country"], "slug": p["slug"], "region": p["region"]})
DT_ORDER = ["ndp", "vision", "sector", "unga", "budget"]
plans.sort(key=lambda p: (cidx[p["slug"]], DT_ORDER.index(p["doc_type"]), int(p["period_start"]), int(p["period_end"]), p["plan_title"]))
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


DICTS = ["sectors", "objs", "targets", "instruments", "sids", "chapters", "agencies", "leads", "sdgs", "urg", "status",
         "legal", "notes"]
RISK = {r: i for i, r in enumerate(tree["risks"])}
CODE = {"L3": "LV", "L2": "L2", "L1": "GRP", "STD": "STD", "GOAL": "GOAL"}


def money(r):
    try:
        return "{:,.1f} {}".format(float(r["amount"].replace(",", "")), r.get("currency") or "").strip()
    except (KeyError, ValueError, AttributeError):
        return r.get("amount") or ""


def encode(rows):
    """The rows of one source, with their strings stored once (each source has its own lists; the page
    joins them as it reads a source)."""
    D = {k: Dict() for k in DICTS}
    out = []
    for r in rows:
        code = CODE.get(r["level"], "NEW")
        # [plan, name, objective, level, family, lever, group, sector, orientation, risks, objective label, target,
        #  instrument, passages, source strategy]; a strategy on a general branch carries the branch id as its group
        out.append([pidx[r["plan_id"]], r["name"], r["objective"], code, r["family_id"], r["lever_id"],
                    r["node_id"] if code == "STD" else r["group_id"],
                    D["sectors"](r["sector"]), r["response_orientation"],
                    [RISK[x] for x in json.loads(r["related_risks"] or "[]") if x in RISK],
                    D["objs"](r["tree_objective"]), D["targets"](r["target_label"] or r["target_group"]),
                    D["instruments"](r["instrument_label"] or r["instrument"]), int(r["n_mentions"] or 0),
                    D["sids"](r["source_strategy_key"]),
                    # the rest of the row, shown when a strategy is opened in the details table:
                    # [number in its plan, quote, plan chapter, urgency, status, legal basis,
                    #  timeline + 2 * quantified target + 4 * monitoring, SDG targets, agencies, lead, plan editions it is in,
                    #  the mapping's reason and note, budget amount]
                    [int(r["strategy_id"].split("#s")[1]), r["quote"], D["chapters"](r["pillar"]), D["urg"](r["stated_urgency"]),
                     D["status"](r["implementation_status"] or (r["statement_type"] if r.get("doc_type") == "budget" else "")),
                     D["legal"](r["legal_or_plan_basis"]),
                     (r["has_timeline"] == "Y") + 2 * (r["has_quantified_target"] == "Y") + 4 * (r["has_monitoring"] == "Y"),
                     [D["sdgs"](x) for x in json.loads(r["sdg_targets"] or "[]")],
                     [D["agencies"](x) for x in json.loads(r["named_agencies"] or "[]")], D["leads"](r["institutional_lead"]),
                     int(r["n_editions"] or 1), D["notes"](r["reason"] if "mapping" in r["depth_basis"] or "rule" in r["depth_basis"] else ""),
                     money(r) if r.get("amount") else ""]])
    return {"rows": out, **{k: D[k].items for k in DICTS}}


blobs, src_meta = {}, []
for k, d, lab in SOURCES:
    rs = [r for r in csv.DictReader(open(os.path.join(d, "strategies.csv"), encoding="utf-8")) if r["plan_id"] not in EXCL]
    blobs[k] = encode(rs)
    src_meta.append({"k": k, "label": lab, "n": len(rs), "lv": sum(1 for r in rs if r["lever_id"]),
                     "un": sum(1 for r in rs if not r["node_id"]), "distinct": len(blobs[k]["sids"]) - 1,
                     "mapped": any("mapping" in r["depth_basis"] for r in rs)})
out = blobs["plans"]["rows"]
data["set"] = {
    "regions": [x for x in REG_ORDER if any(c["region"] == x for c in countries)],
    "countries": countries,
    "plans": [{"id": p["plan_id"], "c": cidx[p["slug"]], "doc_type": p["doc_type"], "edition": p["edition"],
               "title": p["plan_title"], "start": int(p["period_start"]), "end": int(p["period_end"]),
               "src": p["period_source"], "docs": p["source_documents"], "n": int(p["n_strategies"] or 0),
               "lv": int(p["n_on_lever"] or 0), "who": p["status"] if p["doc_type"] == "unga" else ""} for p in plans],
    **{k: v for k, v in blobs["plans"].items() if k != "rows"},
    "sources": src_meta,
    "excluded": excluded,
    "mapped": src_meta[0]["mapped"],
    "rows": out, "n_source": src_meta[0]["distinct"],
}

template = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = template.replace("/*TREE_DATA*/null", blob)
html = html.replace("/*FOREST*/", open(os.path.join(HERE, "forest.js"), encoding="utf-8").read())
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote %s: %d countries, %d plans, %d rows, %d on a lever, %.0f KB" % (
    os.path.basename(OUT), len(countries), len(plans), len(out), sum(1 for r in out if r[5]), len(html) / 1024))
for k in list(blobs)[1:]:
    js = "PVR(%s,%s);" % (json.dumps(k), json.dumps(blobs[k], ensure_ascii=False, separators=(",", ":")))
    with open(os.path.join(os.path.dirname(os.path.abspath(OUT)), "rows_%s.js" % k), "w", encoding="utf-8") as f:
        f.write(js)
    print("wrote rows_%s.js: %d rows, %.1f MB" % (k, len(blobs[k]["rows"]), len(js) / 1e6))

# the passages under each strategy, one file per plan edition, read by the page on demand
det = os.path.join(os.path.dirname(os.path.abspath(OUT)), "detail")
os.makedirs(det, exist_ok=True)
by = {}
for _, folder, _ in SOURCES:
    pp = os.path.join(folder, "passages.csv")
    for r in csv.DictReader(open(pp, encoding="utf-8")) if os.path.exists(pp) else []:
        if r["plan_id"] in EXCL:
            continue
        d = by.setdefault(r["plan_id"], {"docs": Dict(), "s": {}})
        x = [d["docs"](r["document"]), r["page"], r["paragraph"], r["intervention"], r["evidence"], r["agencies"]]
        lst = d["s"].setdefault(r["strategy_id"].split("#s")[1], [])
        if x not in lst:   # a passage read twice the same way is shown once
            lst.append(x)
# a national plan has a file of its own; a country's sector plans, UNGA statements or budgets share one file per
# source (detail/<country>_<source>.js), which keeps the folder to a few hundred files
pinfo = {p["plan_id"]: p for p in plans}
fileOf = lambda pid: pid if pinfo[pid]["doc_type"] in ("ndp", "vision") else "%s_%s" % (pinfo[pid]["slug"], pinfo[pid]["doc_type"])
files = {}
for pid, d in by.items():
    files.setdefault(fileOf(pid), []).append("PVD(%s,%s);" % (json.dumps(pid), json.dumps({"docs": d["docs"].items, "s": d["s"]}, ensure_ascii=False, separators=(",", ":"))))
size = 0
for fn, parts in files.items():
    js = "\n".join(parts)
    size += len(js)
    with open(os.path.join(det, fn + ".js"), "w", encoding="utf-8") as f:
        f.write(js)
print("wrote detail/: %d files for %d plan editions, %.1f MB" % (len(files), len(by), size / 1e6))
