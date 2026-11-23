"""Add a country run through the live workflow (workflow/, steps C, E, F, M on tree v4) to the migration's
outputs, so it shows on the page beside the earlier run. No model calls.

    cd migration && python3 add_country.py <out folder> <plan folder> [<plan folder> ...] [--region "Pacific"] [--replace]

A plan folder is what the workflow writes for one plan edition, data/plans/<plan_id>/, holding
strategies.csv and strategy_rows.csv (a folder of such folders works too, for example data/plans/ or
added/<slug>/). run_migration.sh adds every folder under added/ automatically.

National plans and visions go into <out>/strategies.csv, plans.csv and passages.csv; sector plans into
<out>/sector/. A plan already in the outputs under the same plan_id is replaced. With --replace, every
earlier plan of that country in the same source (national or sector) is replaced, so the new run stands
alone. --region (or a region.txt beside the plan folders) is needed only for a country the migration does not
know (see reshape_common.REGIONS).
Run it after reshape.py and sources.py, which rewrite the outputs, and before viewer.py.
"""
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reshape_common import COLS, REGION, LV, FAM, GRP, SUB, place  # noqa: E402

PLAN_COLS = ["plan_id", "country", "slug", "region", "doc_type", "edition", "plan_title", "period_start", "period_end",
             "published", "language", "status", "period_source", "source_documents", "n_strategies", "n_on_lever",
             "tree_version"]
PASS_COLS = ["strategy_id", "country", "plan_id", "document", "page", "paragraph", "intervention", "evidence",
             "agencies", "primary_risk"]
REGIONS = ["South-East Asia", "South Asia", "East Asia", "Pacific", "Europe and Central Asia", "Arab States",
           "Africa", "Latin America and the Caribbean"]
csv.field_size_limit(10 ** 9)


def jl(s):
    try:
        v = json.loads(s) if s else []
        return v if isinstance(v, list) else [v]
    except ValueError:
        return [x.strip() for x in str(s).split("|") if x.strip()]


def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def write(p, rows, cols):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


GENERAL = {"SMG": "H-SEC", "PFA": "H-SPE", "MCH": "H-SGO"}


def live(r):
    """The strategy's placement on the live tree: a lever the tree no longer has goes to its family, a family
    left without a lever to its pillar's General branch (the rule the rest of the page follows)."""
    node, why = r.get("node_id", ""), ""
    if r.get("lever_id") and r["lever_id"] not in LV:
        node, why = r.get("family_id", ""), "lever %s is not on the live tree; placed on its family" % r["lever_id"]
    if node.startswith("F-") and not (node in FAM and FAM[node].get("n_levers")):
        g = GRP.get((FAM.get(node) or {}).get("group_id", ""))
        node = GENERAL.get(SUB[g["subpillar_code"]]["pillar"], "") if g else ""
        why = (why + "; " if why else "") + "family left without a lever; placed on the General branch"
    if node == r.get("node_id"):
        return
    r.update(place(node))
    r["reason"] = (r.get("reason", "") + " [" + why + "]").strip()


def plan_folders(paths):
    for p in paths:
        for d, _, files in os.walk(p):
            if "strategies.csv" in files and "strategy_rows.csv" in files:
                yield d


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sys.argv[1:]
    region = next((flags[i + 1] for i, a in enumerate(flags[:-1]) if a == "--region"), "")
    args = [a for a in args if a != region]
    replace = "--replace" in flags
    if len(args) < 2:
        sys.exit(__doc__)
    out, srcs = args[0], args[1:]

    new = collections.defaultdict(lambda: {"s": [], "p": [], "x": []})   # lane -> rows
    for d in plan_folders(srcs):
        st = read(os.path.join(d, "strategies.csv"))
        if not st:
            continue
        rows = {r["row_id"]: r for r in read(os.path.join(d, "strategy_rows.csv"))}
        s0 = st[0]
        slug, typ = s0["slug"], s0["doc_type"]
        rf = next((p for p in (os.path.join(d, "region.txt"), os.path.join(d, "..", "region.txt")) if os.path.exists(p)), "")
        reg = REGION.get(slug) or region or (open(rf, encoding="utf-8").read().strip() if rf else "")
        if reg not in REGIONS:
            sys.exit("%s: give --region, one of: %s" % (slug, "; ".join(REGIONS)))
        lane = "sector" if typ == "sector" else "" if typ in ("ndp", "vision") else None
        if lane is None:
            print("skipped %s: doc_type %s is not shown on the page" % (s0["plan_id"], typ))
            continue
        docs = set()
        for r in st:
            r.update(region=reg, source_strategy_key=r["strategy_id"], n_editions=1, first_edition=r["plan_id"])
            live(r)
            new[lane]["s"].append(r)
            for rid in jl(r.get("members")):
                w = rows.get(rid)
                if not w:
                    continue
                doc, page, para = (w["ref"].split(" · ") + ["", "", ""])[:3]
                docs.add(doc)
                new[lane]["x"].append(dict(strategy_id=r["strategy_id"], country=r["country"], plan_id=r["plan_id"],
                                           document=doc, page=w.get("page") or page.replace("p.", ""),
                                           paragraph=para.replace("§", ""), intervention=w["name"], evidence=w["quote"],
                                           agencies=" | ".join(jl(w.get("named_agencies"))),
                                           primary_risk=(jl(w.get("related_risks")) or [""])[0]))
        new[lane]["p"].append(dict(plan_id=s0["plan_id"], country=s0["country"], slug=slug, region=reg, doc_type=typ,
                                   edition=s0["edition"], plan_title=s0["plan_title"], period_start=s0["period_start"],
                                   period_end=s0["period_end"], published=s0.get("published", ""), language="",
                                   status="run through the current workflow", period_source="workflow config",
                                   source_documents=" | ".join(sorted(docs)), n_strategies=len(st),
                                   n_on_lever=sum(1 for r in st if r.get("lever_id")), tree_version=s0.get("tree_version", "v4")))
        print("%s: %d strategies (%s)" % (s0["plan_id"], len(st), lane or "national"))

    for lane, n in new.items():
        d = os.path.join(out, lane) if lane else out
        ids = {p["plan_id"] for p in n["p"]}
        slugs = {p["slug"] for p in n["p"]}
        drop = (lambda r: r["plan_id"] in ids or r.get("slug", r["plan_id"].split("_" + r.get("doc_type", "x"))[0]) in slugs) \
            if replace else (lambda r: r["plan_id"] in ids)
        old_p = read(os.path.join(d, "plans.csv"))
        gone = {p["plan_id"] for p in old_p if drop(p)}
        keep = lambda rows: [r for r in rows if r["plan_id"] not in gone and r["plan_id"] not in ids]
        write(os.path.join(d, "plans.csv"), keep(old_p) + n["p"], PLAN_COLS)
        write(os.path.join(d, "strategies.csv"), keep(read(os.path.join(d, "strategies.csv"))) + n["s"], COLS)
        write(os.path.join(d, "passages.csv"), keep(read(os.path.join(d, "passages.csv"))) + n["x"], PASS_COLS)
        print("%s: %d plan editions added, %d earlier ones replaced" % (d, len(ids), len(gone)))


if __name__ == "__main__":
    main()
