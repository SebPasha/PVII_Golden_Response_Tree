"""The earlier run's other sources, reshaped into the current strategy format like the national plans
(reshape.py): sector plans, UNGA general-debate statements and budget programme lines. No model calls.

    cd tree/v4/poc && python3 sources.py <earlier run's data folder> <reshape.py's out folder> [--mapping=<run folder>]

Writes, for each source, <out>/<source>/strategies.csv, plans.csv and passages.csv in the columns
reshape.py writes, so map_run.py and viewer.py take them as they take the national plans:
  sector   one row per intervention of a sector plan or policy (llm/<c>/sector/<c>_sector_responses.xlsx);
           a plan edition per document, its period from the document table or the title
  unga     one row per theme a statement advances, with the speaker's words (llm/<c>/unga/<c>_unga_statements.xlsx,
           sheet hdi, present = Y); a plan edition per statement year
  budget   one row per programme line (union/budget_rows.csv, line_type = program); a plan edition per
           fiscal year. Overhead lines (administration, personnel) go to General Governance without a call.
With --mapping=<run folder>, each source is placed by <run folder>/mapping_<source>.csv (map_run.py), and
the instrument by <run folder>/instrument_<source>.csv (inst_run.py) where the mapping names none.
"""
import collections
import csv
import glob
import json
import os
import re
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [x for x in sys.argv[1:] if not x.startswith("--")]
RUN = next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith("--mapping=")), "")
SRC, OUT = ARGS[0], ARGS[1]
csv.field_size_limit(10 ** 9)
sys.argv = [sys.argv[0]]
from reshape_common import REGION, NAMES, COLS, place, norm, jl, sheet_rows  # noqa: E402

COLS = COLS + ["amount", "currency"]
docs = collections.defaultdict(dict)
for d in csv.DictReader(open(os.path.join(SRC, "union", "documents.csv"), encoding="utf-8")):
    docs[d["slug"]][norm(d["file"])] = d
nat = collections.defaultdict(list)   # the national plan periods, for an undated sector document
pp = os.path.join(OUT, "plans.csv")   # the national plans, when <out> is reshape.py's out folder
for p in csv.DictReader(open(pp, encoding="utf-8")) if os.path.exists(pp) else []:
    nat[p["slug"]].append((int(p["period_start"]), int(p["period_end"])))


def load(name):
    p = os.path.join(RUN, name)
    return {r["source_strategy_key"]: r for r in csv.DictReader(open(p, encoding="utf-8"))} if RUN and os.path.exists(p) else {}


def period(slug, doc):
    """(start, end, source) of a sector document: a year range in its title, else the document table,
    else the one year in its title."""
    m = docs[slug].get(norm(doc))
    ys = re.findall(r"(?<!\d)((?:19|20)\d\d)(?:\s+(\d{2,4}))?(?!\d)", doc)
    for a, b in ys:
        if b:
            a, b = int(a), int(b) if len(b) == 4 else int(a[:2] + b)
            if b >= a:
                return a, b, "title"
    if m and m["plan_period_start"] and m["plan_period_end"]:
        return int(m["plan_period_start"]), int(m["plan_period_end"]), m["plan_period_source"] or "document"
    if ys:
        a = int(ys[0][0])
        if a >= 2030:   # a horizon year: the start is not in the title
            return min(2020, a), a, "title gives the horizon only; start set to 2020"
        return a, a + 4, "title gives one year; read as the first of five"
    a, b = max(nat.get(slug) or [(2020, 2025)])
    return a, b, "undated; shown with the latest national plan"


def row(**k):
    r = {c: "" for c in COLS}
    r.update(tree_version="v4", statement_type="commitment", quote_check="from the earlier run", n_editions=1)
    r.update(k)
    return r


def apply(r, mp, ins):
    """The placement and instrument: the mapping where it has run, else nothing (unmapped)."""
    node = (mp or {}).get("node_id", "")
    r.update(place(node))
    if mp:
        r.update(relation=mp["relation"], depth_basis="mapping prompt M_map_v4", confidence=mp["confidence"],
                 reason="; ".join(x for x in (mp["reason"], mp["map_note"], mp["proposal"]) if x),
                 tree_objective=mp.get("new_objective", ""))
        for k in ("target", "instrument"):
            if mp[k + "_id"]:
                r.update({k + "_id": mp[k + "_id"], k + "_label": mp[k + "_label"]})
    else:
        r.update(relation="unmapped")
    if not r["instrument_label"] and ins and ins.get("instrument"):
        r.update(instrument_label=ins["instrument"] + (" (%s)" % ins["instrument_class"] if ins.get("instrument_class") else ""))


def write(kind, rows, plans, passages):
    d = os.path.join(OUT, kind)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "strategies.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v for k, v in r.items()})
    with open(os.path.join(d, "passages.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["strategy_id", "country", "plan_id", "document", "page", "paragraph", "intervention",
                               "evidence", "agencies", "primary_risk"])
        w.writeheader()
        w.writerows(passages)
    pl = sorted(plans.values(), key=lambda p: (p["country"], p["period_start"], p["plan_id"]))
    for p in pl:
        p["n_strategies"] = sum(1 for r in rows if r["plan_id"] == p["plan_id"])
        p["n_on_lever"] = sum(1 for r in rows if r["plan_id"] == p["plan_id"] and r["lever_id"])
    with open(os.path.join(d, "plans.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(pl[0].keys()))
        w.writeheader()
        w.writerows(pl)
    lv = sum(1 for r in rows if r["lever_id"])
    print("%s: %d rows, %d distinct, %d editions, %d countries; on a lever %d (%.0f%%), unmapped %d" % (
        kind, len(rows), len({r["source_strategy_key"] for r in rows}), len(plans), len({r["slug"] for r in rows}),
        lv, 100 * lv / max(1, len(rows)), sum(1 for r in rows if not r["node_id"])))


def plan(plans, pid, slug, typ, label, title, a, b, src, status):
    return plans.setdefault(pid, dict(plan_id=pid, country=NAMES.get(slug, slug.replace("_", " ").title()), slug=slug,
                                      region=REGION[slug], doc_type=typ, edition=label, plan_title=title,
                                      period_start=a, period_end=b, published="", language="", status=status,
                                      period_source=src, source_documents=title, n_strategies=0, n_on_lever=0,
                                      tree_version="v4"))


def sector():
    MAP, INS = load("mapping_sector.csv"), load("instrument_sector.csv")
    rows, plans, ps, seq = [], {}, [], collections.Counter()
    for f in sorted(glob.glob(os.path.join(SRC, "llm", "*", "sector", "*_sector_responses.xlsx"))):
        slug = f.split(os.sep)[-3]
        if slug not in REGION:
            continue
        for _, r in sheet_rows(f):
            doc, nm = str(r.get("sector_document") or "").strip(), str(r.get("intervention_name") or "").strip()
            if not (doc and nm):
                continue
            a, b, src = period(slug, doc)
            pid = "%s_sector_%s" % (slug, norm(doc).replace(" ", "-")[:70])
            pl = plan(plans, pid, slug, "sector", doc, doc, a, b, src, "sector plan of the earlier run")
            seq[pid] += 1
            key = "%s|sector|%s" % (slug, nm.lower())
            rel, match = r.get("ndp_relation") or "", r.get("ndp_match") or ""
            basis = {"carried": "carried in the national plan as “%s”" % match if match else "carried in the national plan",
                     "broader_only": "the national plan covers it only broadly", "silent": "not in the national plan"}.get(rel, rel)
            refs = jl(r.get("source_refs"))
            x = row(strategy_id="%s#s%d" % (pid, seq[pid]), plan_id=pid, country=pl["country"], slug=slug,
                    region=REGION[slug], doc_type="sector", edition=doc, plan_title=doc, period_start=a, period_end=b,
                    name=nm, pillar=r.get("HDICategory") or "", related_risks=jl(r.get("related_risks")),
                    sdg_targets=jl(r.get("sdg_targets")), n_mentions=len(refs) or 1, refs=refs[:5],
                    quote=str(r.get("evidence") or ""), legal_or_plan_basis=basis, source_strategy_key=key,
                    first_edition=pid)
            apply(x, MAP.get(key), INS.get(key))
            rows.append(x)
            for ref in refs or [doc]:
                d, page, para = (str(ref).split(" · ") + ["", ""])[:3]
                ps.append(dict(strategy_id=x["strategy_id"], country=x["country"], plan_id=pid, document=d,
                               page=page.replace("p.", ""), paragraph=para.replace("§", ""), intervention=nm,
                               evidence=x["quote"], agencies="", primary_risk=""))
    write("sector", rows, plans, ps)


def unga():
    MAP, INS = load("mapping_unga.csv"), load("instrument_unga.csv")
    rows, plans, ps, seq = [], {}, [], collections.Counter()
    for f in sorted(glob.glob(os.path.join(SRC, "llm", "*", "unga", "*_unga_statements.xlsx"))):
        slug = f.split(os.sep)[-3]
        if slug not in REGION:
            continue
        wb = openpyxl.load_workbook(f, read_only=True)
        spk = {}
        for _, s in sheet_rows(f):
            spk[str(s.get("statement_year"))] = "%s, %s" % (s.get("speaker_name") or "", s.get("speaker_role") or "")
        it = wb["hdi"].iter_rows(values_only=True)
        head = list(next(it))
        for v in it:
            r = dict(zip(head, v))
            if r.get("present") != "Y" or not r.get("evidence"):
                continue
            y = int(str(r["statement_year"])[:4])
            pid = "%s_unga_%d" % (slug, y)
            title = "Statement to the UN General Assembly general debate, %d" % y
            pl = plan(plans, pid, slug, "unga", "UNGA %d" % y, title, y, y, "statement year", spk.get(str(y), "").strip(", "))
            seq[pid] += 1
            ev = " ".join(str(r["evidence"]).split())
            key = "%s|unga|%d|%s" % (slug, y, r.get("category") or "")
            x = row(strategy_id="%s#s%d" % (pid, seq[pid]), plan_id=pid, country=pl["country"], slug=slug,
                    region=REGION[slug], doc_type="unga", edition="UNGA %d" % y, plan_title=title, period_start=y,
                    period_end=y, name=ev if len(ev) <= 180 else ev[:177].rsplit(" ", 1)[0] + "…",
                    objective=str(r.get("rationale") or ""), pillar=r.get("category") or "", statement_type="statement",
                    stated_urgency=r.get("salience") or "", n_mentions=1, quote=ev, institutional_lead=pl["status"],
                    source_strategy_key=key, first_edition=pid)
            apply(x, MAP.get(key), INS.get(key))
            rows.append(x)
            ps.append(dict(strategy_id=x["strategy_id"], country=x["country"], plan_id=pid, document=r.get("doc_name") or "",
                           page=str(r.get("evidence_page") or ""), paragraph="", intervention=r.get("category") or "",
                           evidence=ev, agencies="", primary_risk=""))
    write("unga", rows, plans, ps)


CLASS = {"development": "development programme", "standing_function": "standing function", "overhead": "overhead",
         "mixed": "mixed", "": "not classed"}


def budget():
    MAP, INS = load("mapping_budget.csv"), load("instrument_budget.csv")
    rows, plans, ps, seq = [], {}, [], collections.Counter()
    for r in csv.DictReader(open(os.path.join(SRC, "union", "budget_rows.csv"), encoding="utf-8")):
        slug, nm = r["slug"], " ".join((r["program_name"] or "").split())
        if r["line_type"] != "program" or slug not in REGION or not nm or not r["fiscal_year"]:
            continue
        y = int(r["fiscal_year"])
        pid = "%s_budget_%d" % (slug, y)
        title = "National budget, fiscal year %d" % y
        pl = plan(plans, pid, slug, "budget", "Budget %d" % y, title, y, y, "fiscal year", "budget of the earlier run")
        seq[pid] += 1
        key = "%s|budget|%s" % (slug, nm.lower())
        x = row(strategy_id="%s#s%d" % (pid, seq[pid]), plan_id=pid, country=pl["country"], slug=slug,
                region=REGION[slug], doc_type="budget", edition="Budget %d" % y, plan_title=title, period_start=y,
                period_end=y, name=nm, objective=" ".join((r["program_description"] or "").split()),
                pillar=r["strategy_name"] or "", statement_type=CLASS.get(r["programme_class"], r["programme_class"]),
                n_mentions=1, quote="", source_strategy_key=key, first_edition=pid, amount=r["amount"],
                currency=r["currency_unit"])
        if r["programme_class"] == "overhead":
            x.update(place("H-SGO"))
            x.update(relation="placed", depth_basis="overhead line: General Governance by rule, no call",
                     confidence="rule", reason="administration or personnel line of the budget")
            ins = INS.get(key)
            if ins and ins.get("instrument"):
                x.update(instrument_label=ins["instrument"])
        else:
            apply(x, MAP.get(key), INS.get(key))
        rows.append(x)
        ps.append(dict(strategy_id=x["strategy_id"], country=x["country"], plan_id=pid, document=r["source_location"],
                       page="", paragraph=r["program_code"], intervention=nm,
                       evidence="%s %s %s" % (r["amount"], r["currency_unit"], "· " + r["program_description"] if r["program_description"] else ""),
                       agencies="", primary_risk=""))
    write("budget", rows, plans, ps)


if __name__ == "__main__":
    sector()
    unga()
    budget()
