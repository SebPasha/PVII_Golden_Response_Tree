"""Proof of concept: the strategies of the earlier multi-country run, reshaped into the current
strategy format and joined to mother tree v4. No model calls.

    cd tree/v4/poc && python3 reshape.py <earlier run's data folder> [out folder]
    python3 reshape.py <data folder> <out folder> --mapping=<out folder>/mapping.csv   # after map_run.py
        [--instrument=<out folder>/instrument.csv]   # after inst_run.py: an instrument where the mapping names none

Reads, from the earlier run's data folder (read only):
  union/strategies.csv                  the 9,918 strategies (45 countries)
  union/documents.csv                   each source document with its plan period
  llm/<country>/<country>_strategy_rows.xlsx    the passage-level rows, which say which document
                                        (and so which plan edition) each passage comes from
  llm/<country>/<country>_strategygroup.xlsx or _strategyclean.xlsx   the strategies' component rows
and from this repo:
  tree/inputs/strategy_decomposition.csv   objective, target and instrument of each strategy
  tree/v4/tree_v4.json                     the tree
  objective_crosswalk.csv                  objective label -> lever, family, group or general branch

Writes strategies.csv (one row per strategy per plan edition, the columns of the current
workflow's strategies.csv), passages.csv (the passage-level rows under each strategy: document, page,
paragraph, the intervention read there and its evidence quote), plans.csv and placement_summary.csv.

The earlier run pooled every edition of a country's plan. Here a strategy is split back by the
plan editions its passages come from: a strategy found in three editions gives three rows that
share source_strategy_key, each with that edition's passages, quote and count.
"""
import collections
import csv
import json
import os
import re
import sys

import openpyxl  # noqa: F401

from reshape_common import REGION, NAMES, COLS, LV, FAM, GRP, SUB, PIL, HOLD, tree, place, norm, jl, sheet_rows  # noqa: E402,F401

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [x for x in sys.argv[1:] if not x.startswith("--")]
MAPPING = next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith("--mapping=")), "")
INSTRUMENT = next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith("--instrument=")), "")
SRC = ARGS[0] if ARGS else os.environ.get("PVII_SOURCES_ROOT", "")
OUT = ARGS[1] if len(ARGS) > 1 else os.path.join(HERE, "out")
csv.field_size_limit(10 ** 9)

# Periods the earlier run's document table lacks or has wrong: (slug, document name start) -> (start, end, note)
PERIOD_FIX = {
    ("bangladesh", "Sixth_Five_Year_Plan"): (2011, 2015, "title"),
    ("bhutan", "12340592_01"): (2019, 2030, "inferred from the text; confirm"),
    ("cambodia", "Cambodia Vision 2050 Pentagonal Strategy Phase 1"): (2023, 2028, "title"),
    ("china", "china2030"): (2013, 2030, "inferred from the title; confirm"),
    ("india", "yYo8lCuXK7n13xxElnay"): (2024, 2047, "inferred from the text; confirm"),
    ("papua_new_guinea", "PNG NDP 2016 17"): (2016, 2017, "title"),
    ("samoa", "688ff795095ccc71f0261315_Samoa 2040"): (2021, 2040, "inferred from the title; confirm"),
    ("sri_lanka", "1940_Sri_Lanka_Sustainable_Sri_Lanka_2030"): (2019, 2030, "title"),
    ("kazakhstan", "KZ National Development Plan 2029"): (2024, 2029, "title; the document table says 2018-2023"),
    ("serbia", "RS Agenda 2030 report 2021"): (2021, 2030, "title; the document table says 2000-2015"),
}
FORCE_TYPE = {("cambodia", 2023, 2028): "vision", ("india", 2024, 2047): "vision"}

# Edition names where the plan is well known: (slug, start, end) -> (edition label, title)
TITLES = {
    ("afghanistan", 2008, 2013): ("ANDS", "Afghanistan National Development Strategy"),
    ("afghanistan", 2017, 2021): ("ANPDF I", "National Peace and Development Framework"),
    ("afghanistan", 2021, 2025): ("ANPDF II", "National Peace and Development Framework II"),
    ("afghanistan", 2026, 2030): ("NDS", "National Development Strategy"),
    ("bangladesh", 2011, 2015): ("6th", "Sixth Five Year Plan"),
    ("bangladesh", 2016, 2020): ("7th", "Seventh Five Year Plan"),
    ("bangladesh", 2020, 2025): ("8th", "Eighth Five Year Plan"),
    ("bangladesh", 2026, 2031): ("2026-31", "National Development Plan 2026-31"),
    ("bangladesh", 2021, 2041): ("Vision 2041", "Perspective Plan 2021-2041"),
    ("bhutan", 2013, 2018): ("11th", "Eleventh Five Year Plan"),
    ("bhutan", 2018, 2023): ("12th", "Twelfth Five Year Plan"),
    ("bhutan", 2024, 2029): ("13th", "Thirteenth Five Year Plan"),
    ("bhutan", 2019, 2030): ("2030", "Comprehensive national development plan to 2030 (file 12340592_01)"),
    ("brazil", 2024, 2027): ("PPA", "Plano Plurianual 2024-2027"),
    ("brunei", 2012, 2017): ("RKN 10", "Tenth National Development Plan"),
    ("brunei", 2018, 2023): ("RKN 11", "Eleventh National Development Plan"),
    ("brunei", 2024, 2029): ("RKN 12", "Twelfth National Development Plan"),
    ("cambodia", 2009, 2013): ("NSDP 2009-13", "National Strategic Development Plan Update 2009-2013"),
    ("cambodia", 2014, 2018): ("NSDP 2014-18", "National Strategic Development Plan 2014-2018"),
    ("cambodia", 2019, 2023): ("NSDP 2019-23", "National Strategic Development Plan 2019-2023"),
    ("cambodia", 2024, 2028): ("NSDP 2024-28", "National Strategic Development Plan 2024-2028"),
    ("cambodia", 2023, 2028): ("Pentagonal I", "Pentagonal Strategy Phase I (Cambodia Vision 2050)"),
    ("china", 2011, 2015): ("12th", "12th Five-Year Plan"),
    ("china", 2016, 2020): ("13th", "13th Five-Year Plan"),
    ("china", 2021, 2025): ("14th", "14th Five-Year Plan"),
    ("china", 2026, 2030): ("15th", "15th Five-Year Plan"),
    ("china", 2013, 2030): ("China 2030", "China 2030"),
    ("colombia", 2022, 2026): ("PND", "Plan Nacional de Desarrollo 2022-2026"),
    ("egypt", 2016, 2030): ("Vision 2030", "Egypt Vision 2030"),
    ("ethiopia", 2021, 2030): ("TYDP", "Ten Year Development Plan 2021-2030"),
    ("fiji", 2017, 2021): ("NDP 2017-21", "National Development Plan 2017-2021"),
    ("fiji", 2025, 2029): ("NDP 2025-29", "National Development Plan 2025-2029"),
    ("ghana", 2022, 2025): ("Agenda for Jobs II", "Agenda for Jobs II, Medium-Term National Development Policy Framework 2022-2025"),
    ("india", 2012, 2017): ("12th", "Twelfth Five Year Plan"),
    ("india", 2018, 2022): ("New India", "Strategy for New India @ 75"),
    ("india", 2024, 2047): ("Vision", "Long-term vision paper (file yYo8lCuXK7n13xxElnay)"),
    ("indonesia", 2015, 2019): ("RPJMN 2015-19", "National Medium-Term Development Plan 2015-2019"),
    ("indonesia", 2020, 2024): ("RPJMN 2020-24", "National Medium-Term Development Plan 2020-2024"),
    ("indonesia", 2025, 2029): ("RPJMN 2025-29", "National Medium-Term Development Plan 2025-2029"),
    ("iran", 2011, 2015): ("5th", "Fifth Five-Year Development Plan"),
    ("iran", 2017, 2021): ("6th", "Sixth Five-Year Development Plan"),
    ("iran", 2023, 2027): ("7th", "Seventh Five-Year Development Plan"),
    ("jamaica", 2024, 2027): ("MTF", "Medium Term Socio-Economic Policy Framework 2024-2027"),
    ("kazakhstan", 2024, 2029): ("NDP 2029", "National Development Plan to 2029"),
    ("kenya", 2023, 2027): ("MTP IV", "Fourth Medium Term Plan 2023-2027"),
    ("kiribati", 2012, 2015): ("KDP 2012-15", "Kiribati Development Plan 2012-2015"),
    ("kiribati", 2016, 2019): ("KDP 2016-19", "Kiribati Development Plan 2016-2019"),
    ("kiribati", 2020, 2023): ("KDP 2020-23", "Kiribati Development Plan 2020-2023"),
    ("kiribati", 2024, 2027): ("KDP 2024-27", "Kiribati Development Plan 2024-2027"),
    ("kiribati", 2016, 2036): ("KV20", "Kiribati 20-Year Vision 2016-2036"),
    ("malaysia", 2011, 2015): ("10th", "Tenth Malaysia Plan"),
    ("malaysia", 2016, 2020): ("11th", "Eleventh Malaysia Plan"),
    ("malaysia", 2021, 2025): ("12th", "Twelfth Malaysia Plan"),
    ("malaysia", 2026, 2030): ("13th", "Thirteenth Malaysia Plan"),
    ("maldives", 2019, 2023): ("SAP", "Strategic Action Plan 2019-2023"),
    ("marshall_islands", 2015, 2017): ("NSP 2015-17", "National Strategic Plan 2015-2017"),
    ("marshall_islands", 2020, 2030): ("NSP 2020-30", "National Strategic Plan 2020-2030"),
    ("mongolia", 2016, 2020): ("GAP 2016-20", "Government Action Plan 2016-2020"),
    ("mongolia", 2020, 2024): ("GAP 2020-24", "Government Action Plan 2020-2024"),
    ("mongolia", 2024, 2028): ("GAP 2024-28", "Government Action Plan 2024-2028"),
    ("mongolia", 2021, 2025): ("Guidelines 2021-25", "Five-Year Development Guidelines 2021-2025"),
    ("mongolia", 2026, 2030): ("Guidelines 2026-30", "Five-Year Development Guidelines 2026-2030"),
    ("morocco", 2021, 2035): ("NMD", "Nouveau Modele de Developpement"),
    ("myanmar", 2018, 2030): ("MSDP", "Myanmar Sustainable Development Plan 2018-2030"),
    ("nauru", 2005, 2025): ("NSDS 2005-25", "National Sustainable Development Strategy 2005-2025"),
    ("nauru", 2019, 2030): ("NSDS 2019-30", "National Sustainable Development Strategy 2019-2030"),
    ("nepal", 2016, 2018): ("14th", "Fourteenth Plan"),
    ("nepal", 2020, 2024): ("15th", "Fifteenth Plan"),
    ("nepal", 2025, 2029): ("16th", "Sixteenth Plan"),
    ("nigeria", 2021, 2025): ("NDP 2021-25", "National Development Plan 2021-2025"),
    ("nigeria", 2009, 2020): ("Vision 20:2020", "Nigeria Vision 20:2020"),
    ("pakistan", 2024, 2029): ("2024-29", "National plan 2024-29"),
    ("palau", 2009, 2014): ("2009-14", "National development plan 2009-14"),
    ("palau", 2023, 2026): ("PDP 2023-26", "Palau Development Plan 2023-2026"),
    ("papua_new_guinea", 2011, 2015): ("MTDP I", "Medium Term Development Plan 2011-2015"),
    ("papua_new_guinea", 2016, 2017): ("MTDP II", "Medium Term Development Plan 2 2016-2017"),
    ("papua_new_guinea", 2018, 2022): ("MTDP III", "Medium Term Development Plan III 2018-2022"),
    ("papua_new_guinea", 2023, 2027): ("MTDP IV", "Medium Term Development Plan IV 2023-2027"),
    ("peru", 2011, 2021): ("Bicentenario", "Plan Bicentenario: el Peru hacia el 2021"),
    ("peru", 2022, 2050): ("PEDN 2050", "Plan Estrategico de Desarrollo Nacional al 2050"),
    ("philippines", 2011, 2016): ("PDP 2011-16", "Philippine Development Plan 2011-2016"),
    ("philippines", 2017, 2022): ("PDP 2017-22", "Philippine Development Plan 2017-2022"),
    ("philippines", 2023, 2028): ("PDP 2023-28", "Philippine Development Plan 2023-2028"),
    ("rwanda", 2017, 2024): ("NST1", "National Strategy for Transformation 1"),
    ("rwanda", 2024, 2029): ("NST2", "National Strategy for Transformation 2"),
    ("samoa", 2021, 2026): ("PDS 2021-26", "Pathway for the Development of Samoa 2021-2026"),
    ("samoa", 2027, 2031): ("PDS 2026-30", "Pathway for the Development of Samoa (file says 2026-2030)"),
    ("samoa", 2021, 2040): ("Samoa 2040", "Samoa 2040"),
    ("serbia", 2021, 2023): ("ERP", "Economic Reform Programme 2021-2023"),
    ("serbia", 2021, 2030): ("Agenda 2030", "Serbia and the 2030 Agenda report (2021)"),
    ("solomon_islands", 2016, 2035): ("NDS", "National Development Strategy 2016-2035"),
    ("solomon_islands", 2016, 2020): ("MTDP 2016-20", "Medium Term Development Plan 2016-2020"),
    ("solomon_islands", 2026, 2030): ("MTDP 2026-30", "Medium Term Development Plan 2026-2030"),
    ("sri_lanka", 2017, 2020): ("2017-20", "National plan 2017-2020"),
    ("sri_lanka", 2022, 2025): ("2022-25", "National plan 2022-2025"),
    ("sri_lanka", 2024, 2026): ("2024-26", "National plan 2024-2026"),
    ("sri_lanka", 2026, 2030): ("2026-30", "National plan 2026-2030"),
    ("sri_lanka", 2019, 2030): ("Vision 2030", "Sustainable Sri Lanka 2030 Vision and Strategic Path"),
    ("thailand", 2012, 2016): ("11th", "11th National Economic and Social Development Plan"),
    ("thailand", 2017, 2021): ("12th", "12th National Economic and Social Development Plan"),
    ("thailand", 2023, 2027): ("13th", "13th National Economic and Social Development Plan"),
    ("thailand", 2018, 2037): ("NS", "National Strategy 2018-2037"),
    ("timor_leste", 2011, 2030): ("SDP", "Strategic Development Plan 2011-2030"),
    ("tonga", 2011, 2014): ("TSDF I", "Tonga Strategic Development Framework 2011-2014"),
    ("tonga", 2015, 2025): ("TSDF II", "Tonga Strategic Development Framework 2015-2025"),
    ("tuvalu", 2021, 2030): ("Te Kete", "Te Kete: National Strategy for Sustainable Development 2021-2030"),
    ("uzbekistan", 2023, 2030): ("Strategy 2030", "Uzbekistan 2030 Strategy"),
    ("vanuatu", 2016, 2030): ("NSDP", "National Sustainable Development Plan 2016-2030"),
    ("vietnam", 2006, 2010): ("SEDP 2006-10", "Socio-Economic Development Plan 2006-2010"),
    ("vietnam", 2016, 2020): ("SEDP 2016-20", "Socio-Economic Development Plan 2016-2020"),
}


# ---------- inputs ----------
XW = {r["objective_id"]: r["node_id"] for r in csv.DictReader(open(os.path.join(HERE, "objective_crosswalk.csv")))}
# strategies go only to a live family (one that still has a lever), one of its levers, or a general branch
LIVE = {f["family_id"] for f in tree["families"] if f["lever_ids"]}
for _o, _n in XW.items():
    assert _n in LV or _n in LIVE or _n in ("H-SEC", "H-SPE", "H-SGO"), "%s -> %s is not a live node" % (_o, _n)
# the real mapping (map_run.py), where it has been run: node by strategy, in place of the crosswalk
MAP = {r["source_strategy_key"]: r for r in csv.DictReader(open(MAPPING, encoding="utf-8"))} if MAPPING else {}
INS = {r["source_strategy_key"]: r for r in csv.DictReader(open(INSTRUMENT, encoding="utf-8"))} if INSTRUMENT else {}
DEC = {r["strategy_key"]: r for r in csv.DictReader(open(os.path.join(HERE, "..", "..", "inputs", "strategy_decomposition.csv"), encoding="utf-8"))}
union = list(csv.DictReader(open(os.path.join(SRC, "union", "strategies.csv"), encoding="utf-8")))
docs = collections.defaultdict(dict)
for d in csv.DictReader(open(os.path.join(SRC, "union", "documents.csv"), encoding="utf-8")):
    docs[d["slug"]][norm(d["file"])] = d


# Source files taken out of the plan edition they were merged into, by decision: (slug, file) -> why.
# Their passages are skipped; a strategy found only in them yields no row. The Audit tab lists them.
XDOCS = {(d["slug"], d["file"]): d["why"] for d in json.load(open(os.path.join(HERE, "excluded_documents.json"), encoding="utf-8"))} \
    if os.path.exists(os.path.join(HERE, "excluded_documents.json")) else {}


def edition_of(slug, doc):
    """(doc_type, start, end, period_source) of the plan edition a document belongs to."""
    fix = next((v for (s, d), v in PERIOD_FIX.items() if s == slug and doc.startswith(d)), None)
    if fix:
        a, b, src = fix
    else:
        m = docs[slug].get(norm(doc))
        if not (m and m["plan_period_start"] and m["plan_period_end"]):
            return None
        a, b, src = int(m["plan_period_start"]), int(m["plan_period_end"]), m["plan_period_source"]
    typ = FORCE_TYPE.get((slug, a, b)) or ("vision" if b - a + 1 >= 10 else "ndp")
    return typ, a, b, src


by_slug = collections.defaultdict(list)
for u in union:
    by_slug[u["slug"]].append(u)

out_rows, pass_rows, plans, undated = [], [], {}, collections.Counter()
for slug in sorted(by_slug):
    country = NAMES.get(slug, slug.replace("_", " ").title())
    ref, at = {}, collections.defaultdict(list)
    for sheet, r in sheet_rows(os.path.join(SRC, "llm", slug, slug + "_strategy_rows.xlsx"), all_sheets=True):
        k = r.get("ref number")
        ref[k] = str(r.get("Ref") or "")
        at[k].append(r)
    comp = {}
    for kind in ("strategygroup", "strategyclean"):
        p = os.path.join(SRC, "llm", slug, "%s_%s.xlsx" % (slug, kind))
        if os.path.exists(p):
            for _, r in sheet_rows(p):
                comp[(r.get("intervention_name") or "").strip().lower()] = set(jl(r.get("component_interventions")))
            break
    seq = collections.Counter()
    for u in by_slug[slug]:
        d = DEC.get(u["strategy_key"], {})
        mp = MAP.get(u["strategy_key"])
        # a strategy with no dated passage was not in map_run's input and yields no row here either
        node = (mp or {}).get("node_id", "") if MAPPING else XW.get(d.get("objective_id", ""), "")
        tr = place(node)
        mine = comp.get(u["strategy"].strip().lower(), set())
        risks_u = jl(u["related_risks"])
        per, src_of = collections.defaultdict(list), {}  # edition -> passage ids
        for k in jl(u["source_chunks"]):
            if k not in ref:
                continue
            if (slug, ref[k].split(" · ")[0]) in XDOCS:
                continue
            ed = edition_of(slug, ref[k].split(" · ")[0])
            if ed is None:
                undated[(slug, ref[k].split(" · ")[0])] += 1
                continue
            per[ed[:3]].append(k)
            src_of[ed[:3]] = ed[3]
        eds = sorted(per, key=lambda e: (e[1], e[2]))
        first = None
        made = []
        for ed in eds:
            typ, a, b = ed
            src = src_of[ed]
            pid = "%s_%s_%d-%d" % (slug, typ, a, b)
            label, title = TITLES.get((slug, a, b), ("%d-%d" % (a, b), "%s plan %d-%d" % (country, a, b)))
            pl = plans.setdefault(pid, dict(plan_id=pid, country=country, slug=slug, region=REGION[slug], doc_type=typ,
                                            edition=label, plan_title=title, period_start=a, period_end=b,
                                            published="", language="", status="reshaped from the earlier run",
                                            period_source=src, source_documents=set(), n_strategies=0,
                                            n_on_lever=0, tree_version="v4"))
            first = first or pid
            members, refs, agencies, risks_e, quote, ps = [], [], [], set(), "", []
            for k in per[ed]:
                pl["source_documents"].add(ref[k].split(" · ")[0])
                if len(refs) < 5:
                    refs.append(ref[k])
                for r in at[k]:
                    nm = (r.get("intervention_name") or "").strip()
                    if mine and nm not in mine:
                        continue
                    if nm and nm not in members:
                        members.append(nm)
                    doc, page, para = (ref[k].split(" · ") + ["", ""])[:3]
                    ps.append(dict(document=doc, page=page.replace("p.", ""), paragraph=para.replace("§", ""),
                                   intervention=nm, evidence=str(r.get("intervention_evidence") or "").strip(),
                                   agencies=" | ".join(jl(r.get("ministries"))), primary_risk=r.get("primary_risk") or ""))
                    for m in jl(r.get("ministries")):
                        if m not in agencies:
                            agencies.append(m)
                    risks_e.update([r.get("primary_risk")] + jl(r.get("related_risks")))
                    if not quote and r.get("_sheet", "Results") != "Dropped":
                        quote = str(r.get("intervention_evidence") or "")
            risks = [x for x in risks_u if x in risks_e]
            seq[pid] += 1
            row = dict(strategy_id="%s#s%d" % (pid, seq[pid]), plan_id=pid, country=country, slug=slug,
                       region=REGION[slug], doc_type=typ, edition=label, plan_title=title, period_start=a,
                       period_end=b, published="", name=u["strategy"], objective=d.get("objective_phrase", ""),
                       target_group=d.get("target_phrase", ""), instrument=d.get("instrument_phrase", ""),
                       pillar=u["ndp_milestone"], statement_type="commitment",
                       related_risks=risks, n_mentions=len(per[ed]), members=members, refs=refs, quote=quote,
                       quote_check="from the earlier run", named_agencies=agencies[:12],
                       stated_urgency=u["stated_urgency"], sdg_targets=[x.strip() for x in u["sdg_targets"].split(";") if x.strip()],
                       response_orientation=u["response_orientation"], sector=u["sector"],
                       institutional_lead=u["institutional_lead"], implementation_status=u["implementation_status"],
                       has_timeline=u["has_timeline"], has_quantified_target=u["has_quantified_target"],
                       has_monitoring=u["has_monitoring"], legal_or_plan_basis=u["legal_or_plan_basis"],
                       tree_version="v4", relation="placed" if node else "new",
                       objective_id=d.get("objective_id", ""), tree_objective=d.get("objective", ""),
                       depth_basis="objective label crosswalk", target_id=d.get("target_id", ""),
                       target_label=d.get("target", ""), instrument_id=d.get("instrument_id", ""),
                       instrument_label=d.get("instrument", ""), confidence="medium" if tr["lever_id"] else "low",
                       reason="objective '%s' sits on %s" % (d.get("objective", ""), node),
                       source_strategy_key=u["strategy_key"], n_editions=len(eds), first_edition=first)
            row.update(tr)
            if mp:
                row.update(relation=mp["relation"], depth_basis="mapping prompt M_map_v4", confidence=mp["confidence"],
                           reason="; ".join(x for x in (mp["reason"], mp["map_note"], mp["proposal"]) if x))
                for k in ("target", "instrument"):
                    if mp[k + "_id"]:
                        row.update({k + "_id": mp[k + "_id"], k + "_label": mp[k + "_label"]})
            ins = INS.get(u["strategy_key"])
            if not row["instrument_label"] and ins and ins["instrument"]:
                row.update(instrument_label=ins["instrument"] + (" (%s)" % ins["instrument_class"] if ins["instrument_class"] else ""))
            made.append(row)
            pass_rows.extend(dict(x, strategy_id=row["strategy_id"], plan_id=pid, country=country) for x in ps)
            pl["n_strategies"] += 1
            pl["n_on_lever"] += 1 if tr["lever_id"] else 0
        # a strategy keeps its risks in every edition when no single edition's passages name them
        if risks_u and made and not any(r["related_risks"] for r in made):
            for r in made:
                r["related_risks"] = risks_u
        out_rows.extend(made)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "strategies.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    for r in out_rows:
        w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v for k, v in r.items()})
with open(os.path.join(OUT, "passages.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["strategy_id", "country", "plan_id", "document", "page", "paragraph", "intervention", "evidence",
                           "agencies", "primary_risk"])
    w.writeheader()
    w.writerows(pass_rows)
pl_list = sorted(plans.values(), key=lambda p: (p["country"], p["doc_type"] != "ndp", p["period_start"], p["period_end"]))
with open(os.path.join(OUT, "plans.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(pl_list[0].keys()))
    w.writeheader()
    for p in pl_list:
        w.writerow(dict(p, source_documents=" | ".join(sorted(p["source_documents"]))))
with open(os.path.join(OUT, "placement_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["country", "region", "plan editions", "strategies (earlier run)", "strategy x edition rows", "on a lever",
                "on a family", "general economy", "general people", "general governance", "share on a lever"])
    for slug in sorted(by_slug):
        rs = [r for r in out_rows if r["slug"] == slug]
        c = collections.Counter(r["level"] for r in rs)
        g = collections.Counter(r["node_id"] for r in rs if r["level"] == "STD")
        w.writerow([rs[0]["country"] if rs else slug, REGION[slug], len({r["plan_id"] for r in rs}), len(by_slug[slug]),
                    len(rs), c["L3"], c["L2"], g["H-SEC"], g["H-SPE"], g["H-SGO"], "%.0f%%" % (100 * c["L3"] / max(1, len(rs)))])

lv = sum(1 for r in out_rows if r["lever_id"])
print("strategies in: %d; with a dated passage: %d; rows out (strategy x edition): %d; plan editions: %d; countries: %d" % (
    len(union), len({r["source_strategy_key"] for r in out_rows}), len(out_rows), len(plans), len(by_slug)))
print("passage rows under the strategies: %d" % len(pass_rows))
print("on a lever: %d (%.0f%%); levers used: %d of %d" % (lv, 100 * lv / len(out_rows), len({r["lever_id"] for r in out_rows if r["lever_id"]}), len(LV)))
if undated:
    print("passages left out (document without a period):", dict(undated))
