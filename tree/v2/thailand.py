"""Place a country's workflow outputs on mother tree v2 and compute the comparability measures.

    python3 thailand.py                       # reads ../../data/plans/thailand_*/strategies.csv (+ risks.csv)
    python3 thailand.py --from extract.json   # reads a JSON extract with the same columns (see FALLBACK NOTE)

Writes thailand_v2.json (the page data) and thailand_v2.html (the interactive page, from page_template.html),
plus thailand_strategies_v2.csv with every strategy's v2 placement and flags.

The v1 node a strategy carries is re-read on v2: a pathway (L3-xxx) keeps its id (a merged pathway counts on its
survivor) and inherits its mechanism and family; a strategy v1 held at a family falls to the v2 family
(old_family_default) and is tried against the plan words of that family's mechanisms. Exactly one mechanism
matching the strategy's own name and objective places it at the mechanism, flagged "plan words (provisional)"
because step M has not re-run; none or several leave it at the family with the candidates listed.

Measures computed here need no model call: shares by family, mechanism and depth; target-group and instrument
classes; orientation; risk prominence; the mechanism-consistency flag and link confidence on every strategy x risk
link; the risk x mechanism RAG per plan; the SDG profile of the nodes a plan reaches and, where step E wrote SDG
targets, the coherence of each strategy's own targets with its node; carried, added and dropped mechanisms between
national plan editions; and the sector plans as a subordinate layer that never enters the national counts.

FALLBACK NOTE (28 October 2026): the Thai run outputs live on Sebastian's Mac. Until they are copied in, the page
is built from the Mirror Forests export, which carries node, orientation, target, instrument and risks per strategy
but not SDG targets, urgency, status or quotes; those measures show as "needs the run outputs".
"""
import collections
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data")
INPUTS = os.path.join(HERE, "..", "inputs")
TREE = json.load(open(os.path.join(HERE, "tree_v2.json"), encoding="utf-8"))
RISKS = TREE["risks"]

# the population a macro factor bears on, for the affected-group test (a claim distinct from addressing the mechanism)
AFFECTED = {
    "Demographic Shifts": {"Older people", "Women and girls", "Children and youth"},
    "Climate Change": {"Farmers and fishers", "Regions and places", "Households and the poor"},
    "Pandemics": {"Households and the poor", "Older people", "Workers and informal workers"},
    "Technological Change": {"Workers and informal workers", "Firms and MSMEs", "Children and youth"},
    "Shifts in Globalisation": {"Firms and MSMEs", "Workers and informal workers", "Farmers and fishers"},
    "Environmental Degradation and Pollution": {"Households and the poor", "Regions and places"},
    "Biodiversity Loss": {"Farmers and fishers", "Regions and places"},
    "Resource and Energy Pressures": {"Households and the poor", "Firms and MSMEs", "Farmers and fishers"},
    "Democratic Backsliding": {"Excluded and affected groups", "Whole population and future generations"},
    "Growing Populism": {"Excluded and affected groups", "Workers and informal workers", "Regions and places"},
    "Increased Polarisation": {"Excluded and affected groups", "Whole population and future generations"},
}
NATIONAL_ORDER = ["ndp", "vision"]  # national plan editions are compared within doc_type; the vision is shown beside them


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def aslist(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    v = str(v or "").strip()
    if not v:
        return []
    if v.startswith("["):
        try:
            return [str(x).strip() for x in json.loads(v.replace("'", '"')) if str(x).strip()]
        except ValueError:
            pass
    return [x.strip() for x in re.split(r"\s*\|\s*", v) if x.strip()]


# ---------------------------------------------------------------- tree lookups
FAM = {f["family_id"]: f for f in TREE["families"]}
MEC = {m["mechanism_id"]: m for m in TREE["mechanisms"]}
PATH = {p["pathway_id"]: p for p in TREE["pathways"]}
MERGE = TREE["meta"]["merges"]
OLD_DEFAULT = TREE["old_family_default"]
WORDS = {m["mechanism_id"]: re.compile(m["plan_words"], re.I) for m in TREE["mechanisms"]}
TRIGGERS = {}
for m in TREE["mechanisms"]:
    for c in m["conditional_risks"]:
        try:
            TRIGGERS[(c["pathway_id"], c["risk"])] = re.compile(c["trigger"], re.I)
        except re.error:
            pass
TCLASS = {t["target_label"].lower(): t["target_class"] for t in TREE["target_classes"]}
ICLASS = {i["instrument_label"].lower(): i["instrument_class"] for i in TREE["instrument_classes"]}
# the label lists' aliases, so a free-text label from an older export still classifies
for _r in csv.DictReader(open(os.path.join(INPUTS, "targets.csv"), encoding="utf-8")):
    for _a in _r["aliases"].split(" | "):
        TCLASS.setdefault(_a.strip().lower(), TCLASS.get(_r["label"].lower(), ""))
for _r in csv.DictReader(open(os.path.join(INPUTS, "instruments.csv"), encoding="utf-8")):
    for _a in _r["aliases"].split(" | "):
        ICLASS.setdefault(_a.strip().lower(), ICLASS.get(_r["label"].lower(), ""))
# Hood's four resources by keyword, for free-text instrument wording step M has not normalised
IKEY = [("Authority", re.compile(r"\b(law|act|regulat|legislat|decree|standard|certif|licen[cs]|tax|levy|tariff|agreement|treaty|ban|mandate|quota|code|enforce|penalt|rule)", re.I)),
        ("Money", re.compile(r"\b(fund|loan|credit|subsid|grant|incentive|insurance|transfer|scholarship|budget|financ|guarantee|bond|payment|investment|compensation|allowance|pension|voucher)", re.I)),
        ("Information", re.compile(r"\b(information|data|platform|database|register|registry|system|guideline|plan|strateg|research|stud|survey|awareness|campaign|monitor|indicator|assessment|map|forecast|warning|advice|advisory|label|curricul|roadmap|framework|policy|standardi[sz]ation)", re.I)),
        ("Organisation", re.compile(r"\b(facilit|build|construct|infrastructure|cent(re|er)|network|partnership|program|project|service|training|hospital|school|unit|agency|team|office|committee|institute|zone|corridor|laborator|staff|workforce|personnel|equipment|vehicle|plant|station|clinic|shelter|stockpile|reserve|support|assistance|promotion|development|workshop|education|capacity|measure|mechanism|cooperation|collaboration|participation|forum|meeting|visit|technical|volunteer|deploy|channel|process|innovation|technolog)", re.I))]
TKEY = [("Workers and informal workers", re.compile(r"personnel|manpower|human resource|staff|workforce|labou?r\b|worker|teacher|lecturer|professional|official", re.I)),
        ("Children and youth", re.compile(r"child|youth|student|learner|pupil|young", re.I)),
        ("Older people", re.compile(r"elderly|older|senior|ageing|aging", re.I)),
        ("Women and girls", re.compile(r"women|girl|female|mother", re.I)),
        ("Households and the poor", re.compile(r"household|poor|patient|famil|consumer|low-income|vulnerable", re.I)),
        ("Farmers and fishers", re.compile(r"farm|fisher|agricultur|livestock|grower", re.I)),
        ("Firms and MSMEs", re.compile(r"private sector|business|enterprise|firm|industr|entrepreneur|operator|producer|investor|exporter|SME", re.I)),
        ("Public institutions", re.compile(r"agenc|ministr|government|authorit|public sector|department|institution|university|school|hospital|court", re.I)),
        ("Regions and places", re.compile(r"area|region|province|district|destination|point of entry|points of entry|border|city|cities|rural|urban|communit|village|zone", re.I)),
        ("Excluded and affected groups", re.compile(r"migrant|minorit|disab|indigenous|refugee|prisoner|victim|survivor|affected", re.I)),
        ("Whole population and future generations", re.compile(r"thailand|thai people|all sectors|society|the public|citizen|population|individual|people|nation", re.I))]


def target_class(label):
    if not label:
        return "None stated"
    cls = TCLASS.get(label.lower())
    if cls:
        return cls
    for name, rx in TKEY:
        if rx.search(label):
            return name
    return "Unclassified"


def instrument_class(label):
    if not label:
        return "None stated"
    cls = ICLASS.get(label.lower())
    if cls:
        return cls
    for name, rx in IKEY:
        if rx.search(label):
            return name
    return "Unclassified"
# families that v1 split: the plan words of every candidate family's mechanisms decide, else the default
SPLIT = {"L2-11": ["FAM-06", "FAM-04", "FAM-05", "FAM-17"], "L2-38": ["FAM-19", "FAM-17"]}


def place(node_v1, text):
    """-> dict(node_id, level, family_id, mechanism_id, pathway_id, basis, candidates)"""
    if node_v1 in PATH:
        p = PATH[node_v1]
        pathway = p["merged_into"] or node_v1
        return {"node_id": pathway, "level": "L3", "family_id": p["family_id"], "mechanism_id": p["mechanism_id"],
                "pathway_id": pathway, "basis": "pathway kept from v1" + (" (merged)" if p["merged_into"] else ""), "candidates": []}
    if node_v1 in OLD_DEFAULT:
        fams = SPLIT.get(node_v1, [OLD_DEFAULT[node_v1]])
        hits = [m for f in fams for m in FAM[f]["mechanism_ids"] if WORDS[m].search(text)]
        if len(hits) == 1:
            m = hits[0]
            return {"node_id": m, "level": "L2", "family_id": MEC[m]["family_id"], "mechanism_id": m, "pathway_id": "",
                    "basis": "plan words (provisional)", "candidates": []}
        fid = OLD_DEFAULT[node_v1]
        if len(hits) > 1:
            # several levers named: stay at the family the most hits point to, list the candidates
            byfam = collections.Counter(MEC[m]["family_id"] for m in hits)
            fid = byfam.most_common(1)[0][0]
        return {"node_id": fid, "level": "L1", "family_id": fid, "mechanism_id": "", "pathway_id": "",
                "basis": "family (several levers named)" if hits else "family (no lever named)", "candidates": hits}
    return {"node_id": node_v1, "level": "held", "family_id": "", "mechanism_id": "", "pathway_id": "", "basis": "holding", "candidates": []}


def node_risks(pl):
    """Risks the literature ties to the node at the depth placed, plus conditional (pathway, risk) pairs."""
    if pl["level"] == "L3":
        p = PATH[pl["pathway_id"]]
        return set(p["risks"]), [(pl["pathway_id"], c["risk"]) for c in p["conditional_risks"]]
    if pl["level"] == "L2":
        m = MEC[pl["mechanism_id"]]
        return set(m["risks"]), [(c["pathway_id"], c["risk"]) for c in m["conditional_risks"]]
    if pl["level"] == "L1":
        f = FAM[pl["family_id"]]
        conds = [(c["pathway_id"], c["risk"]) for mid in f["mechanism_ids"] for c in MEC[mid]["conditional_risks"]]
        return set(f["risks"]), conds
    return set(), []


def classify_link(pl, risk, text, tclass):
    tagged, conds = node_risks(pl)
    if risk in tagged:
        return "mechanism-consistent" if pl["level"] in ("L2", "L3") else "family-consistent"
    for (pw, r) in conds:
        if r == risk and TRIGGERS.get((pw, r)) and TRIGGERS[(pw, r)].search(text):
            return "mechanism-consistent (conditional)"
    if tclass in AFFECTED.get(risk, ()):
        return "affected-group support"
    return "mention-only"


def sdg_coherence(own, pl):
    if not own:
        return ""
    node = MEC[pl["mechanism_id"]]["sdg_targets"] if pl["mechanism_id"] else (FAM[pl["family_id"]]["sdg_targets"] if pl["family_id"] else [])
    if not node:
        return "no node targets"
    goals = {t.split(".")[0] for t in node}
    if any(t in node for t in own):
        return "consistent"
    if any(t.split(".")[0] in goals for t in own):
        return "adjacent"
    return "off-node"


# ---------------------------------------------------------------- load
def load_plans(country, extract):
    if extract:
        d = json.load(open(extract, encoding="utf-8"))
        return d["plans"], d["strategies"], {}, d.get("source", "")
    plans, strategies, risks = [], [], {}
    for d in sorted(glob.glob(os.path.join(DATA, "plans", country + "_*"))):
        st = read_csv(os.path.join(d, "strategies.csv"))
        if not st:
            continue
        s0 = st[0]
        run = json.load(open(os.path.join(d, "run.json"), encoding="utf-8")) if os.path.exists(os.path.join(d, "run.json")) else {}
        rk = read_csv(os.path.join(d, "risks.csv")) if os.path.exists(os.path.join(d, "risks.csv")) else []
        pid = s0["plan_id"]
        plans.append({"plan_id": pid, "title": s0["plan_title"], "short": s0["plan_title"], "doc_type": s0["doc_type"],
                      "period_start": int(s0["period_start"] or 0), "period_end": int(s0["period_end"] or 0),
                      "n_all": len(st), "unplaced": {}, "risk_records": dict(collections.Counter(r["risk"] for r in rk)),
                      "colour": "", "run": run})
        for s in st:
            strategies.append({"strategy_id": s["strategy_id"], "plan_id": pid, "name": s["name"], "objective": s.get("objective", ""),
                               "node_id": s["node_id"], "level": s["level"], "response_orientation": s.get("response_orientation", ""),
                               "target_label": s.get("target_label") or s.get("target_group", ""),
                               "instrument_label": s.get("instrument_label") or s.get("instrument", ""),
                               "related_risks": aslist(s.get("related_risks")), "sdg_targets": aslist(s.get("sdg_targets")),
                               "stated_urgency": s.get("stated_urgency", ""), "implementation_status": s.get("implementation_status", ""),
                               "has_monitoring": s.get("has_monitoring", ""), "legal_or_plan_basis": s.get("legal_or_plan_basis", ""),
                               "target_year": s.get("target_year", ""), "quote": s.get("quote_en") or s.get("quote", "")})
    return plans, strategies, risks, "workflow outputs in data/plans"


def main():
    extract = sys.argv[sys.argv.index("--from") + 1] if "--from" in sys.argv else ""
    country = "thailand"
    plans, strategies, _, source = load_plans(country, extract)
    if not plans:
        sys.exit("no plans found for %s; pass --from extract.json" % country)
    full = not extract
    plans.sort(key=lambda p: (p["doc_type"] != "ndp", p["doc_type"] != "vision", p["period_start"]))
    pidx = {p["plan_id"]: i for i, p in enumerate(plans)}

    rows = []
    for s in strategies:
        text = "%s. %s" % (s["name"], s["objective"])
        pl = place(s["node_id"], text)
        if pl["level"] == "held":
            continue
        tcl = target_class(s["target_label"])
        icl = instrument_class(s["instrument_label"])
        links = []
        for r in s["related_risks"]:
            if r not in RISKS:
                continue
            kind = classify_link(pl, r, text, tcl)
            conf = "explicit" if pl["level"] in ("L2", "L3") else "inferred"
            links.append({"risk": r, "kind": kind, "confidence": conf})
        rows.append({**{k: s[k] for k in ("strategy_id", "plan_id", "name", "objective", "response_orientation", "target_label",
                                            "instrument_label", "sdg_targets", "stated_urgency", "implementation_status",
                                            "has_monitoring", "legal_or_plan_basis", "target_year", "quote")},
                     "node_v1": s["node_id"], "level_v1": s["level"], **pl,
                     "mechanism": MEC[pl["mechanism_id"]]["mechanism"] if pl["mechanism_id"] else "",
                     "family": FAM[pl["family_id"]]["family"], "subpillar": FAM[pl["family_id"]]["subpillar"],
                     "pillar": FAM[pl["family_id"]]["pillar"], "target_class": tcl, "instrument_class": icl,
                     "links": links, "sdg_coherence": sdg_coherence(s["sdg_targets"], pl), "p": pidx[s["plan_id"]]})

    # ---------------------------------------------------------------- per plan measures
    def share(counter, n):
        return {k: round(v / n, 4) for k, v in counter.items()} if n else {}

    measures = []
    for i, p in enumerate(plans):
        rs = [r for r in rows if r["p"] == i]
        n = len(rs)
        fam = collections.Counter(r["family_id"] for r in rs)
        mec = collections.Counter(r["mechanism_id"] for r in rs if r["mechanism_id"])
        depth = collections.Counter(r["level"] for r in rs)
        basis = collections.Counter(r["basis"] for r in rs)
        ori = collections.Counter(r["response_orientation"] or "not stated" for r in rs)
        tcl = collections.Counter(r["target_class"] for r in rs)
        icl = collections.Counter(r["instrument_class"] for r in rs)
        urg = collections.Counter(r["stated_urgency"] or "not stated" for r in rs)
        status = collections.Counter(r["implementation_status"] or "not stated" for r in rs)
        basis_legal = collections.Counter(r["legal_or_plan_basis"] or "not stated" for r in rs)
        coh = collections.Counter(r["sdg_coherence"] for r in rs if r["sdg_coherence"])
        links = [(r, l) for r in rs for l in r["links"]]
        kinds = collections.Counter(l["kind"] for _, l in links)
        risk_prom = collections.Counter(l["risk"] for _, l in links)
        # SDG profile of the nodes reached: each strategy contributes its node's targets' primary dimension
        dims = collections.Counter()
        sdgt = collections.Counter()
        for r in rs:
            tg = MEC[r["mechanism_id"]]["sdg_targets"] if r["mechanism_id"] else FAM[r["family_id"]]["sdg_targets"]
            for t in tg:
                sdgt[t] += 1 / len(tg)
                d = SDG_DIM.get(t, "")
                if d:
                    dims[d] += 1 / len(tg)
        # RAG per risk x mechanism
        rag = {}
        for risk in RISKS:
            framed = p["risk_records"].get(risk, 0) > 0 or risk_prom.get(risk, 0) > 0
            cells = {}
            for mid, m in MEC.items():
                carries = risk in m["risks"] or any(c["risk"] == risk for c in m["conditional_risks"])
                ls = [(r, l) for r, l in links if l["risk"] == risk and (r["mechanism_id"] == mid)]
                fam_ls = [(r, l) for r, l in links if l["risk"] == risk and not r["mechanism_id"] and r["family_id"] == m["family_id"]]
                if not carries and not ls:
                    continue
                strong = [1 for r, l in ls if l["kind"].startswith("mechanism-consistent")]
                weak = [1 for r, l in ls if l["kind"] == "affected-group support"] + [1 for r, l in fam_ls if l["kind"] == "family-consistent"]
                colour = "green" if strong else ("amber" if weak else ("red" if framed and carries else "none"))
                cells[mid] = {"c": colour, "n": len(ls), "strong": len(strong), "weak": len(weak), "share": round(mec.get(mid, 0) / n, 4) if n else 0,
                              "fam_n": len(fam_ls), "carries": carries}
            rag[risk] = {"framed": framed, "records": p["risk_records"].get(risk, 0), "links": risk_prom.get(risk, 0), "cells": cells}
        future = (ori.get("proactive", 0) + ori.get("transformative", 0)) / n if n else 0
        years = [int(r["target_year"]) for r in rs if str(r["target_year"]).isdigit()]
        beyond = sum(1 for y in years if y > p["period_end"]) / n if n else 0
        measures.append({"plan_id": p["plan_id"], "n": n, "family_share": share(fam, n), "mechanism_share": share(mec, n),
                         "mechanism_n": dict(mec), "family_n": dict(fam), "depth": share(depth, n), "basis": dict(basis),
                         "orientation": share(ori, n), "target_class": share(tcl, n), "instrument_class": share(icl, n),
                         "urgency": share(urg, n), "status": share(status, n), "legal_basis": share(basis_legal, n),
                         "sdg_coherence": dict(coh), "link_kinds": dict(kinds), "n_links": len(links),
                         "consistency_share": round(sum(v for k, v in kinds.items() if k.startswith("mechanism")) / len(links), 4) if links else 0,
                         "risk_prominence": {k: round(v / n, 4) for k, v in risk_prom.items()} if n else {},
                         "risk_records": p["risk_records"], "sdg_profile": {k: round(v, 1) for k, v in dims.items()},
                         "sdg_targets": {k: round(v, 1) for k, v in sdgt.most_common(40)}, "rag": rag,
                         "indices": {"future_orientation": round(future, 4), "beyond_period_share": round(beyond, 4) if full else None,
                                     "mechanism_depth": round((depth.get("L2", 0) + depth.get("L3", 0)) / n, 4) if n else 0,
                                     "consistency": round(sum(v for k, v in kinds.items() if k.startswith("mechanism")) / len(links), 4) if links else 0,
                                     "urgency_high_share": round(urg.get("high", 0) / n, 4) if (n and full) else None}})

    # ---------------------------------------------------------------- editions: national plans by doc_type, in period order
    editions = []
    for dt in ("ndp",):
        seq = [p for p in plans if p["doc_type"] == dt]
        for a, b in zip(seq, seq[1:]):
            ma, mb = measures[pidx[a["plan_id"]]], measures[pidx[b["plan_id"]]]
            for level, key in (("mechanism", "mechanism_n"), ("family", "family_n")):
                for node in sorted(set(ma[key]) | set(mb[key])):
                    na, nb = ma[key].get(node, 0), mb[key].get(node, 0)
                    status = "carried" if na and nb else ("added" if nb else "dropped")
                    editions.append({"from": a["plan_id"], "to": b["plan_id"], "level": level, "node_id": node, "status": status,
                                     "n_from": na, "n_to": nb, "share_from": round(na / ma["n"], 4) if ma["n"] else 0,
                                     "share_to": round(nb / mb["n"], 4) if mb["n"] else 0})

    # ---------------------------------------------------------------- sector plans: where they sit against the national plan in force
    sector = []
    for i, p in enumerate(plans):
        if p["doc_type"] != "sector":
            continue
        m = measures[i]
        nat = [q for q in plans if q["doc_type"] == "ndp" and q["period_start"] <= p["period_end"] and q["period_end"] >= p["period_start"]]
        overlap = {}
        for q in nat:
            mq = measures[pidx[q["plan_id"]]]
            shared = [k for k in m["mechanism_n"] if k in mq["mechanism_n"]]
            only = [k for k in m["mechanism_n"] if k not in mq["mechanism_n"]]
            overlap[q["plan_id"]] = {"shared_mechanisms": shared, "sector_only_mechanisms": only,
                                     "share_of_sector_strategies_on_shared": round(sum(m["mechanism_n"][k] for k in shared) / m["n"], 4) if m["n"] else 0}
        sector.append({"plan_id": p["plan_id"], "national_in_force": [q["plan_id"] for q in nat], "overlap": overlap,
                       "top_families": [k for k, _ in collections.Counter(m["family_n"]).most_common(5)],
                       "top_mechanisms": [k for k, _ in collections.Counter(m["mechanism_n"]).most_common(8)]})

    out = {"meta": {"country": country, "built": "2026-10-28", "source": source, "full_outputs": full,
                    "tree_version": TREE["meta"]["version"], "n_strategies": len(rows),
                    "note": "" if full else "Built from the Mirror Forests export: SDG coherence, urgency, status, legal basis and quotes need the run outputs."},
           "plans": plans, "strategies": rows, "measures": measures, "editions": editions, "sector": sector, "tree": TREE}
    with open(os.path.join(HERE, "thailand_v2.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    cols = ["strategy_id", "plan_id", "name", "objective", "node_v1", "level_v1", "node_id", "level", "basis", "candidates", "family_id",
            "family", "mechanism_id", "mechanism", "pathway_id", "subpillar", "pillar", "response_orientation", "target_label", "target_class",
            "instrument_label", "instrument_class", "risk_links", "sdg_targets", "sdg_coherence"]
    with open(os.path.join(HERE, "thailand_strategies_v2.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "candidates": " | ".join(r["candidates"]), "sdg_targets": " | ".join(r["sdg_targets"]),
                        "risk_links": " | ".join("%s: %s (%s)" % (l["risk"], l["kind"], l["confidence"]) for l in r["links"])})
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    test_path = os.path.join(HERE, "bottomup_test.json")
    test = open(test_path, encoding="utf-8").read() if os.path.exists(test_path) else "null"
    page = tpl.replace("/*DATA*/", json.dumps(out, ensure_ascii=False).replace("</", "<\\/")).replace("/*TEST*/", test.replace("</", "<\\/"))
    with open(os.path.join(HERE, "thailand_v2.html"), "w", encoding="utf-8") as f:
        f.write(page)
    d = collections.Counter(r["level"] for r in rows)
    b = collections.Counter(r["basis"] for r in rows)
    print("strategies placed %d  depth %s" % (len(rows), dict(d)))
    print("basis", dict(b))
    print("link kinds", dict(collections.Counter(l["kind"] for r in rows for l in r["links"])))
    print("page %.1f MB" % (len(page) / 1e6))


SDG_DIM = {k: v.get("primary_dimension", "") for k, v in
           json.load(open(os.path.join(HERE, "..", "..", "workflow", "vocab", "sdg_target_dimensions.json"), encoding="utf-8")).items()}

if __name__ == "__main__":
    main()
