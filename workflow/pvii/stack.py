"""Step 5: plan files stacked into a country, country files stacked into the global set.

Nothing is recomputed on the way up. A country's strategies.csv is its plans' strategies.csv
one after another, and the global one is the countries'. Two tables are added, both read only
from what the plans already hold:

    editions.csv       per country: for each pair of consecutive editions of the same doc_type,
                       every tree node either carried, new or dropped. This is the time axis:
                       a strategy carried from one plan to the next is found here, by node,
                       never by merging rows across plans.
    node_coverage.csv  global: tree node x country x plan, with counts.
"""
import os

from pvii import config, io, plans as P, steps

PLAN_COLUMNS = ["plan_id", "country", "slug", "doc_type", "edition", "plan_title",
                "period_start", "period_end", "language", "status", "n_risks", "n_strategies",
                "n_same", "n_differs", "n_new", "n_unmapped", "tree_version"]
EDITION_COLUMNS = ["country", "doc_type", "from_plan", "to_plan", "from_period", "to_period",
                   "node_id", "level", "family", "mechanism", "status", "n_from", "n_to"]
COVERAGE_COLUMNS = ["node_id", "level", "family_id", "family", "mechanism", "subpillar",
                    "country", "plan_id", "period_start", "period_end", "n_strategies"]


def country_dir(slug):
    return os.path.join(config.DATA_DIR, "country", slug)


def global_dir():
    return os.path.join(config.DATA_DIR, "global")


def stack_country(slug, configs_dir=None):
    """Every plan of this country that has outputs, stacked, plus the edition comparison."""
    risks, strategies, plan_rows = [], [], []
    for p in P.load_country(slug, configs_dir):
        row = dict(p.row(), status=p.why_not_runnable() or "not run")
        d = P.plan_dir(p.plan_id) if p.plan_id else ""
        st = io.read_csv(os.path.join(d, "strategies.csv")) if d else []
        rk = io.read_csv(os.path.join(d, "risks.csv")) if d else []
        if st or rk:
            row["status"] = "run"
            rel = {}
            for s in st:
                rel[s.get("relation")] = rel.get(s.get("relation"), 0) + 1
            row.update(n_risks=len(rk), n_strategies=len(st), n_same=rel.get("same", 0),
                       n_differs=rel.get("differs", 0), n_new=rel.get("new", 0),
                       n_unmapped=rel.get("unmapped", 0),
                       tree_version=st[0].get("tree_version", "") if st else "")
            risks += rk
            strategies += st
        plan_rows.append(row)
    out = country_dir(slug)
    io.write_csv(os.path.join(out, "plans.csv"), plan_rows, PLAN_COLUMNS)
    io.write_csv(os.path.join(out, "risks.csv"), risks, steps.RISK_COLUMNS)
    io.write_csv(os.path.join(out, "strategies.csv"), strategies, steps.STRATEGY_COLUMNS)
    eds = editions(strategies, plan_rows)
    io.write_csv(os.path.join(out, "editions.csv"), eds, EDITION_COLUMNS)
    return {"plans": plan_rows, "risks": risks, "strategies": strategies, "editions": eds}


def editions(strategies, plan_rows):
    """Consecutive editions of the same doc_type compared on tree nodes."""
    run = [p for p in plan_rows if p.get("status") == "run" and p.get("doc_type") != "sector"]
    by_type = {}
    for p in run:
        by_type.setdefault(p["doc_type"], []).append(p)
    nodes = {}                       # plan_id -> {node_id: (count, sample strategy)}
    for s in strategies:
        if s.get("node_id"):
            c, sample = nodes.setdefault(s["plan_id"], {}).get(s["node_id"], (0, s))
            nodes[s["plan_id"]][s["node_id"]] = (c + 1, sample)
    out = []
    for doc_type, ps in by_type.items():
        ps = sorted(ps, key=lambda p: (int(p["period_start"]), int(p["period_end"])))
        for a, b in zip(ps, ps[1:]):
            na, nb = nodes.get(a["plan_id"], {}), nodes.get(b["plan_id"], {})
            for node in sorted(set(na) | set(nb)):
                ca, sa = na.get(node, (0, None))
                cb, sb = nb.get(node, (0, None))
                sample = sb or sa
                out.append({"country": a["country"], "doc_type": doc_type,
                            "from_plan": a["plan_id"], "to_plan": b["plan_id"],
                            "from_period": "%s-%s" % (a["period_start"], a["period_end"]),
                            "to_period": "%s-%s" % (b["period_start"], b["period_end"]),
                            "node_id": node, "level": sample.get("level", ""),
                            "family": sample.get("family", ""), "mechanism": sample.get("mechanism", ""),
                            "status": "carried" if ca and cb else ("new" if cb else "dropped"),
                            "n_from": ca, "n_to": cb})
    return out


def stack_global(slugs=None, configs_dir=None):
    slugs = slugs or P.countries(configs_dir)
    risks, strategies, plan_rows, eds = [], [], [], []
    for slug in slugs:
        c = stack_country(slug, configs_dir)
        risks += c["risks"]
        strategies += c["strategies"]
        plan_rows += c["plans"]
        eds += c["editions"]
    out = global_dir()
    io.write_csv(os.path.join(out, "plans.csv"), plan_rows, PLAN_COLUMNS)
    io.write_csv(os.path.join(out, "risks.csv"), risks, steps.RISK_COLUMNS)
    io.write_csv(os.path.join(out, "strategies.csv"), strategies, steps.STRATEGY_COLUMNS)
    io.write_csv(os.path.join(out, "editions.csv"), eds, EDITION_COLUMNS)
    cov = {}
    for s in strategies:
        if not s.get("node_id"):
            continue
        k = (s["node_id"], s["plan_id"])
        if k not in cov:
            cov[k] = {c: s.get(c, "") for c in COVERAGE_COLUMNS if c != "n_strategies"}
            cov[k]["n_strategies"] = 0
        cov[k]["n_strategies"] += 1
    rows = sorted(cov.values(), key=lambda r: (r["node_id"], r["country"], r["plan_id"]))
    io.write_csv(os.path.join(out, "node_coverage.csv"), rows, COVERAGE_COLUMNS)
    return {"plans": plan_rows, "risks": risks, "strategies": strategies, "coverage": rows}
