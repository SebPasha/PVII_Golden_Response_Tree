#!/usr/bin/env python3
"""Regional messages and comparability checks for the page's Regional messages tab. No model calls.

    python3 regional.py <migration out folder> [<out json>]

Comparable basis: each country's latest national plan edition (the one that starts last; a medium-term
plan wins a tie with a vision), shares of that plan's strategies rather than counts, and every country
weighted equally inside its region. Writes <out>/regional.json, which viewer.py puts on the page.
The message texts are written by hand in regional_messages.json from these numbers (25 Nov 2026 build); read them
again after a rebuild that changes the data. The page draws its charts from the numbers here, so those stay current.
"""
import csv, json, os, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
DEST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(OUT, "regional.json")
EXCL = set(json.load(open(os.path.join(HERE, "excluded_plans.json"), encoding="utf-8")))
GEN = {"H-SEC": ("Smarter Growth", "General economy"), "H-SPE": ("People-first Approach", "General people"),
       "H-SGO": ("Making Change Happen", "General governance")}
MIN_N = 30  # a plan edition needs this many strategies to stand for its country
PILLARS = ["Smarter Growth", "People-first Approach", "Making Change Happen"]


def rows(sub):
    d = os.path.join(OUT, sub) if sub else OUT
    s = [r for r in csv.DictReader(open(os.path.join(d, "strategies.csv"), encoding="utf-8")) if r["plan_id"] not in EXCL]
    p = [r for r in csv.DictReader(open(os.path.join(d, "plans.csv"), encoding="utf-8")) if r["plan_id"] not in EXCL]
    return s, p


def pillar(r):
    if r["node_id"] in GEN:
        return GEN[r["node_id"]]
    return r["pillar_rhdr"] or None, r["subpillar"] or None


def shares(rs, key):
    c = Counter(k for k in map(key, rs) if k)
    n = sum(c.values())
    return {k: v / n for k, v in c.items()} if n else {}


def mean_of(dicts, keys):
    return {k: sum(d.get(k, 0) for d in dicts) / len(dicts) for k in keys} if dicts else {}


nat, nplans = rows("")
srcs = {k: rows(k) for k in ("sector", "unga", "budget")}
by_plan = defaultdict(list)
for r in nat:
    by_plan[r["plan_id"]].append(r)

# country facts
cty = {}
for p in nplans:
    c = cty.setdefault(p["country"], {"region": p["region"], "plans": []})
    c["plans"].append(p)
docs = {}
for r in csv.DictReader(open(os.path.join(HERE, "pv2_data", "union", "documents.csv"), encoding="utf-8")):
    docs[(r["slug"], "".join(ch for ch in r["file"].rsplit(".", 1)[0].lower() if ch.isalnum()))] = r


def pages(p):
    t = 0
    for x in p["source_documents"].split("|"):
        d = docs.get((p["slug"], "".join(ch for ch in x.strip().lower() if ch.isalnum())))
        t += int(d["pages"]) if d and d["pages"] else 0
    return t


latest = {}
for c, v in cty.items():
    v["plans"].sort(key=lambda p: (int(p["period_start"]), p["doc_type"] == "ndp", int(p["period_end"])))
    # the latest edition with at least MIN_N strategies (a stub or a one-page file would stand for the country otherwise)
    ok = [p for p in v["plans"] if len(by_plan[p["plan_id"]]) >= MIN_N]
    latest[c] = ok[-1] if ok else max(v["plans"], key=lambda p: len(by_plan[p["plan_id"]]))

key_sub = lambda r: pillar(r)[1]
key_pil = lambda r: pillar(r)[0]
key_grp = lambda r: r["group"] if r["group"] else (pillar(r)[1] if r["node_id"] in GEN else None)
key_fam = lambda r: r["family"] or None
inst = lambda r: (r["instrument_label"].rsplit("(", 1)[-1].rstrip(")") if r["instrument_label"].endswith(")") else None)

prof = {}
for c, p in latest.items():
    rs = by_plan[p["plan_id"]]
    risks = Counter(x for r in rs for x in json.loads(r["related_risks"] or "[]"))
    nrisk = sum(1 for r in rs if json.loads(r["related_risks"] or "[]"))
    prof[c] = {
        "sub": shares(rs, key_sub), "pil": shares(rs, key_pil), "grp": shares(rs, key_grp), "fam": shares(rs, key_fam),
        "ori": shares(rs, lambda r: r["response_orientation"] or None), "ins": shares(rs, inst),
        "risk": {k: v / len(rs) for k, v in risks.items()}, "risk_any": nrisk / len(rs),
        "qt": sum(r["has_quantified_target"] == "Y" for r in rs) / len(rs),
        "mon": sum(r["has_monitoring"] == "Y" for r in rs) / len(rs),
        "high": sum(r["stated_urgency"] == "high" for r in rs) / len(rs),
        "lever": sum(bool(r["lever_id"]) for r in rs) / len(rs),
        "general": sum(r["node_id"] in GEN for r in rs) / len(rs),
        "n": len(rs),
    }

REG = ["South-East Asia", "South Asia", "East Asia", "Pacific", "Europe and Central Asia", "Arab States", "Africa",
       "Latin America and the Caribbean"]
regions = [r for r in REG if any(v["region"] == r for v in cty.values())]
thin = sorted(c for c in cty if prof[c]["n"] < MIN_N)   # left out of the averages, listed on the page
members = {r: sorted(c for c, v in cty.items() if v["region"] == r and c not in thin) for r in regions}
allc = sorted(c for c in cty if c not in thin)


def agg(field, keys):
    world = mean_of([prof[c][field] for c in allc], keys)
    reg = {r: mean_of([prof[c][field] for c in members[r]], keys) for r in regions}
    return world, reg


def keys(field):
    return sorted({k for c in allc for k in prof[c][field]})


out = {"basis": "Each country's latest national plan edition; shares of its strategies; countries weighted equally in a region.",
       "regions": regions, "pillars": PILLARS}
for field in ("sub", "pil", "grp", "ori", "ins", "risk"):
    w, rg = agg(field, keys(field))
    out[field] = {"keys": sorted(w, key=lambda k: -w[k]), "world": w, "reg": rg}
    # how many member countries sit above the all-country average, to show whether a regional lean is shared
    out[field]["above"] = {r: {k: sum(prof[c][field].get(k, 0) > w[k] for c in members[r]) for k in w} for r in regions}
for f in ("risk_any", "qt", "mon", "high", "lever", "general"):
    out.setdefault("scal", {})[f] = {"world": statistics.mean(prof[c][f] for c in allc),
                                     **{r: statistics.mean(prof[c][f] for c in members[r]) for r in regions}}

# trend: first vs latest national edition, for countries with two or more
trend = {}
for r in regions:
    d = []
    for c in members[r]:
        ps = [p for p in cty[c]["plans"] if by_plan[p["plan_id"]]]
        if len(ps) >= 2:
            a, b = shares(by_plan[ps[0]["plan_id"]], key_sub), prof[c]["sub"]
            d.append((c, ps[0]["period_start"], latest[c]["period_start"], {k: b.get(k, 0) - a.get(k, 0) for k in set(a) | set(b)}))
    trend[r] = {"countries": [x[0] for x in d],
                "delta": {k: statistics.mean(x[3].get(k, 0) for x in d) for k in out["sub"]["keys"]} if d else {}}
out["trend"] = trend

# coverage and comparability, per country
cov = []
for c in sorted(cty):
    v, p = cty[c], latest[c]
    src_n = {k: len({q["plan_id"] for q in srcs[k][1] if q["country"] == c}) for k in srcs}
    pg = pages(p)
    cov.append({"c": c, "region": v["region"], "editions": len(v["plans"]), "latest": p["plan_title"], "doc_type": p["doc_type"],
                "start": int(p["period_start"]), "end": int(p["period_end"]), "n": prof[c]["n"], "pages": pg,
                "per100": round(prof[c]["n"] / pg * 100) if pg > 5 else None,
                "lever": prof[c]["lever"], "general": prof[c]["general"], "thin": c in thin, **src_n})
out["coverage"] = cov
nat_all = [len(by_plan[p["plan_id"]]) for c in cty for p in cty[c]["plans"]]
pg_all = [(len(by_plan[p["plan_id"]]), pages(p)) for c in cty for p in cty[c]["plans"] if pages(p) > 5]


def spearman(xy):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for k, i in enumerate(o): r[i] = k
        return r
    a, b = rank([x for x, _ in xy]), rank([y for _, y in xy])
    n = len(xy); return 1 - 6 * sum((i - j) ** 2 for i, j in zip(a, b)) / (n * (n * n - 1))


out["checks"] = {
    "countries": len(cty), "thin": thin, "min_n_rule": MIN_N, "editions": len(nplans),
    "all_four": sum(1 for x in cov if x["sector"] and x["unga"] and x["budget"]),
    "national_only": sum(1 for x in cov if not (x["sector"] or x["unga"] or x["budget"])),
    "one_edition": sum(1 for x in cov if x["editions"] == 1),
    "vision_latest": sum(1 for x in cov if x["doc_type"] == "vision"),
    "stale": sorted([x["c"] for x in cov if x["end"] < 2022]),
    "min_n": min(nat_all), "max_n": max(nat_all), "rho_pages": round(spearman(pg_all), 2),
    "vision_lever": statistics.mean(x["lever"] for x in cov if x["doc_type"] == "vision"),
    "ndp_lever": statistics.mean(x["lever"] for x in cov if x["doc_type"] == "ndp"),
    "lever_min": min(x["lever"] for x in cov), "lever_max": max(x["lever"] for x in cov),
    "lever_min_c": min(cov, key=lambda x: x["lever"])["c"], "lever_max_c": max(cov, key=lambda x: x["lever"])["c"],
    "repeat_rows": sum(1 for r in nat if int(r["n_editions"] or 1) > 1) / len(nat),
}
# which pillar and subpillar each framework family and subpillar sits under, for colours and row order on the page
out["sub_pillar"], out["grp_sub"] = {}, {}
for r in nat:
    p, sp = pillar(r)
    if sp: out["sub_pillar"][sp] = p
    g = key_grp(r)
    if g and sp: out["grp_sub"].setdefault(g, sp)
out["messages"] = json.load(open(os.path.join(HERE, "regional_messages.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(HERE, "regional_messages.json")) else {}
os.makedirs(os.path.dirname(os.path.abspath(DEST)), exist_ok=True)
json.dump(out, open(DEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote %s: %d regions, %d countries" % (DEST, len(regions), len(allc)))
