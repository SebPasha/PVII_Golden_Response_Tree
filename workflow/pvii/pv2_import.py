"""PV2's consolidated strategies, split into plan editions and placed on the mother tree (step M).

For countries PV2 already extracted, this reuses that work instead of re-running C, E and F:

    python -m pvii.pv2_import --pv2 <PV2 repo> --country south_korea --dry-run   # price it
    python -m pvii.pv2_import --pv2 <PV2 repo> --country south_korea --max-cost 5

It reads two PV2 files per country, both under <PV2>/data/llm/<slug>/:

    <slug>_strategyclean.xlsx   one row per consolidated strategy, with its component interventions
    <slug>_strategy_rows.xlsx   one row per intervention per paragraph, with the document in `Ref`

PV2 merged strategies across plan editions. Here a strategy goes to every edition one of its
component interventions was extracted from, found by the component's name in the paragraph rows
(whose `Ref` names the document). Chunk numbers are a fallback only: in Brunei they are shared
by more than one plan. A strategy found in two editions becomes one row in each, so
editions.csv reads it as carried.

What this does not give, against a run of C, E and F from the PDFs: no objective x target x
instrument decomposition (step M proposes them); no commitment test; the quote is PV2's evidence
phrase, often an English rendering, never checked against the paragraph (quote_check says so);
risks, SDG targets and the step-4 fields are PV2's country-level values, repeated on each
edition. Every plan's run.json records `source: pv2_import` and these limits.

Each plan also gets a strategy_rows.csv in step E's columns, built from PV2's paragraph rows
(row_id <plan_id>#pv2r<n>, n the row's line in the workbook), and a strategy's `members` are
those row_ids, as after step F. migration/add_country.py reads the two files. For plans mapped
before the rows were written, --rows-only writes them and repoints `members` with no model call:

    python -m pvii.pv2_import --pv2 <PV2 repo> --country south_korea --rows-only
"""
import argparse
import collections
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from pvii import config, io, llm, parse, plans as P, stack, steps, tree as T, vocab

QUOTE_CHECK = "pv2: not checked"
LIMITS = ["no objective x target x instrument decomposition (step M proposes them)",
          "no commitment test", "quote is PV2's evidence phrase, not checked against the paragraph",
          "risks, SDG targets and step-4 fields are PV2's country-level values, repeated per edition"]

# ---------------------------------------------------------------- xlsx, standard library only
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"


def _col(ref):
    n = 0
    for c in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(c) - 64
    return n - 1


def read_xlsx(path, sheet=None):
    """The first (or named) sheet as a list of dicts keyed by the header row."""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % _NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target")
            for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).iter(_REL)}
    sheets = wb.find("m:sheets", _NS)
    node = next((s for s in sheets if s.get("name") == sheet), None) if sheet else sheets[0]
    target = rels[node.get("{%s}id" % _NS["r"])].lstrip("/")
    target = target if target.startswith("xl/") else "xl/" + target
    rows = []
    for row in ET.fromstring(z.read(target)).iter("{%s}row" % _NS["m"]):
        cells = {}
        for c in row.findall("m:c", _NS):
            t, v = c.get("t"), c.find("m:v", _NS)
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{%s}t" % _NS["m"]))
            else:
                val = v.text if v is not None else ""
            cells[_col(c.get("r"))] = val
        rows.append([cells.get(i, "") for i in range(max(cells) + 1)] if cells else [])
    head = rows[0] if rows else []
    return [dict(zip(head, r)) for r in rows[1:] if any(r)]


# ---------------------------------------------------------------- PV2 rows -> per-plan strategies
def _jlist(v):
    return [x for x in io.as_list(v) if str(x).strip()]


def _doc_label(ref):
    """'KOR State Administration Plan 2017 2022 Korean · p.81 · §3' -> the document part."""
    return str(ref or "").split(" · ")[0].strip()


def split_by_plan(slug, pv2_root, plans):
    """{plan_id: [strategy dicts]} plus a report of how each strategy was attributed."""
    d = os.path.join(pv2_root, "data", "llm", slug)
    clean = read_xlsx(os.path.join(d, "%s_strategyclean.xlsx" % slug))
    rows = read_xlsx(os.path.join(d, "%s_strategy_rows.xlsx" % slug))
    plan_of_label = {parse.doc_name(f): p for p in plans for f in p.files}
    by_name = collections.defaultdict(list)
    docs_of_chunk = collections.defaultdict(set)
    unknown_labels = collections.Counter()
    rows_of_plan = {p.plan_id: [] for p in plans}
    for i, r in enumerate(rows, 1):
        label = _doc_label(r.get("Ref"))
        p = plan_of_label.get(label)
        if not p:
            unknown_labels[label] += 1
            continue
        r["_plan"] = p
        r["_row_id"] = "%s#pv2r%d" % (p.plan_id, i)
        rows_of_plan[p.plan_id].append(_row(p, r))
        by_name[r.get("intervention_name", "").strip()].append(r)
        docs_of_chunk[str(r.get("ref number", "")).strip()].add(p.plan_id)
    report = collections.Counter()
    out = {p.plan_id: [] for p in plans}
    for n, c in enumerate(clean, 1):
        comps = [str(x).strip() for x in _jlist(c.get("component_interventions"))]
        chunks = {str(x) for x in _jlist(c.get("source_chunks"))}
        hits = [r for name in comps for r in by_name.get(name, [])]
        cited = [r for r in hits if str(r.get("ref number", "")).strip() in chunks]
        hits = cited or hits                     # rows the strategy itself cites, where there are any
        per_plan = collections.defaultdict(list)
        for r in hits:
            per_plan[r["_plan"].plan_id].append(r)
        how = "component names"
        if not per_plan:                         # fallback: chunks that belong to one plan only
            for ch in chunks:
                ids = docs_of_chunk.get(ch, set())
                if len(ids) == 1:
                    per_plan[next(iter(ids))].append({})
            how = "unambiguous chunks"
        if not per_plan:
            report["unattributed"] += 1
            continue
        report["by " + how] += 1
        report["in %d edition(s)" % len(per_plan)] += 1
        for pid, rs in per_plan.items():
            plan = next(p for p in plans if p.plan_id == pid)
            out[pid].append(_strategy(plan, c, n, [r for r in rs if r]))
    report["unknown document labels in rows"] = sum(unknown_labels.values())
    return out, dict(report), {"clean": len(clean), "rows": len(rows),
                               "unknown_labels": dict(unknown_labels.most_common(5))}, rows_of_plan


def _row(plan, r):
    """One PV2 paragraph row in strategy_rows.csv's columns (step E's)."""
    parts = [x.strip() for x in str(r.get("Ref") or "").split(" · ")]
    page = parts[1][2:].strip() if len(parts) > 1 and parts[1].startswith("p.") else ""
    risks = []
    for x in [r.get("primary_risk")] + _jlist(r.get("related_risks")):
        x = str(x or "").strip()
        if x in config.RISKS and x not in risks:
            risks.append(x)
    st = str(r.get("statement_type") or "").strip().lower()
    out = dict(plan.row())
    out.update(row_id=r["_row_id"], ref=str(r.get("Ref") or "").strip(), page=page,
               statement_type=st if st in steps.STATEMENT_TYPES else "",
               name=str(r.get("intervention_name") or "").strip(),
               related_risks=risks, named_agencies=_jlist(r.get("ministries")),
               quantified_targets=_jlist(r.get("details_and_specific_targets")),
               quote=str(r.get("intervention_evidence") or "").strip(), quote_en="",
               quote_check=QUOTE_CHECK, stated_urgency=str(r.get("stated_urgency") or "").strip().lower(),
               sdg_targets=_jlist(r.get("sdg_targets")))
    return out


def _strategy(plan, c, n, rs):
    """One PV2 strategy as it appears in one plan, in strategies.csv's columns."""
    members = []
    for r in rs:
        if r["_row_id"] not in members:
            members.append(r["_row_id"])
    quote = next((r.get("intervention_evidence", "").strip() for r in rs
                  if len(r.get("intervention_evidence", "").strip()) >= 12), "")
    agencies = []
    for r in rs:
        for a in _jlist(r.get("ministries")):
            if a not in agencies:
                agencies.append(a)
    risks, ev, _ = vocab.pair_risks(_jlist(c.get("related_risks")), _jlist(c.get("risk_evidence")),
                                    lambda q: bool(str(q).strip()))
    targets = []
    for t in _jlist(c.get("sdg_targets")):
        if t in vocab.SDG_TARGET_DIMENSIONS and t not in targets:
            targets.append(t)
    st, lb, ur = (str(c.get(k) or "").strip().lower() for k in
                  ("implementation_status", "legal_or_plan_basis", "stated_urgency"))
    sector = str(c.get("sector") or "").strip()
    s = dict(plan.row())
    s.update(strategy_id="%s#s%d" % (plan.plan_id, n),
             name=str(c.get("intervention_name") or "").strip(), objective="", target_group="",
             instrument="", pillar=str(c.get("ndp_milestone") or "").strip(), statement_type="",
             related_risks=risks, risk_evidence=ev, target_year=None, horizon="", place="",
             n_mentions=len(members), members=members,
             refs=sorted({r.get("Ref", "") for r in rs if r.get("Ref")}),
             quote=quote, quote_en="", quote_check=QUOTE_CHECK if quote else "",
             quantified_targets=[], named_agencies=agencies,
             stated_urgency=ur if ur in vocab.URGENCIES else "medium",
             sdg_targets=targets, sdg_primary_dimension=vocab.primary_dimension(targets),
             response_orientation=vocab.ORIENTATIONS.get(
                 str(c.get("response_orientation") or "").strip().lower(), "BAU"),
             response_evidence="", sector=sector, sector_canonical=vocab.sector_canonical(sector),
             institutional_lead=str(c.get("institutional_lead") or "").strip(),
             implementation_status=st if st in vocab.STATUSES else "aspiration",
             legal_or_plan_basis=lb if lb in vocab.BASES else "none",
             **{yn: "Y" if str(c.get(yn) or "").upper().startswith("Y") else "N"
                for yn in ("has_timeline", "has_quantified_target", "has_monitoring")})
    return s


# ---------------------------------------------------------------- run
def import_country(slug, pv2_root, client, tree):
    plans = [p for p in P.load_country(slug) if not p.why_not_runnable()]
    by_plan, report, counts, rows_of_plan = split_by_plan(slug, pv2_root, plans)
    print("== %s: %d PV2 strategies, %d paragraph rows -> %s" % (
        slug, counts["clean"], counts["rows"], json.dumps(report)), flush=True)
    if counts["unknown_labels"]:
        print("   rows naming a document not in the config: %s" % counts["unknown_labels"])
    records = []
    for plan in plans:
        strategies = by_plan[plan.plan_id]
        print("   %s: %d strategies" % (plan.plan_id, len(strategies)), flush=True)
        if not strategies:
            continue
        out = tempfile.mkdtemp() if client.dry_run else P.plan_dir(plan.plan_id)
        if not client.dry_run:
            io.write_csv(os.path.join(out, "strategy_rows.csv"), rows_of_plan[plan.plan_id], steps.ROW_COLUMNS)
        ctx = io.read_json(os.path.join(P.plan_dir(plan.plan_id), "context.json")) or {}
        mapped, proposals, errors = steps.map_to_tree(client, plan, strategies, ctx, tree, out)
        if client.dry_run:
            continue
        cnt = lambda k: dict(collections.Counter(s.get(k) or "" for s in mapped))
        rec = {"plan_id": plan.plan_id, "source": "pv2_import", "limits": LIMITS,
               "pv2": {"root": pv2_root, "slug": slug, "files": [
                   "data/llm/%s/%s_strategyclean.xlsx" % (slug, slug),
                   "data/llm/%s/%s_strategy_rows.xlsx" % (slug, slug)],
                   "country_attribution": report},
               "prompts": {"M": steps.sha(config.load_prompt("M"))},
               "models": {"M": config.STAGE_MODELS["M"]},
               "map": {"tree_version": tree.version, "strategies": len(mapped),
                       "proposals": len(proposals), "errors": errors[:20],
                       "relations": cnt("relation"), "levels": cnt("level"),
                       "subpillar": cnt("subpillar"),
                       "group_only": sum(1 for s in mapped if "is required" in s.get("map_note", ""))}}
        io.write_json(os.path.join(out, "run.json"), rec)
        records.append(rec)
    return records


def write_rows(slug, pv2_root):
    """strategy_rows.csv for plans already mapped, and their strategies' members repointed to its
    row_ids. No model call: the split is the same one import_country made."""
    plans = [p for p in P.load_country(slug) if not p.why_not_runnable()]
    by_plan, _, counts, rows_of_plan = split_by_plan(slug, pv2_root, plans)
    for plan in plans:
        d = P.plan_dir(plan.plan_id)
        path = os.path.join(d, "strategies.csv")
        mapped = io.read_csv(path)
        if not mapped:
            continue
        fresh = {s["strategy_id"]: s["members"] for s in by_plan[plan.plan_id]}
        if set(fresh) != {s["strategy_id"] for s in mapped}:
            raise SystemExit("%s: the split no longer gives the mapped strategies; re-run the import"
                             % plan.plan_id)
        for s in mapped:
            s["members"] = fresh[s["strategy_id"]]
            s["n_mentions"] = len(fresh[s["strategy_id"]])
        cols = list(mapped[0].keys())
        io.write_csv(path, mapped, cols)
        io.write_csv(os.path.join(d, "strategy_rows.csv"), rows_of_plan[plan.plan_id], steps.ROW_COLUMNS)
        print("   %s: %d rows, %d strategies repointed" % (
            plan.plan_id, len(rows_of_plan[plan.plan_id]), len(mapped)), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pv2", required=True, help="the PV2 repository (holds data/llm/<slug>/)")
    ap.add_argument("--country", action="append", required=True, help="a slug; repeat for more")
    ap.add_argument("--dry-run", action="store_true", help="price step M, spend nothing, write nothing")
    ap.add_argument("--max-cost", type=float, default=5.0)
    ap.add_argument("--max-calls", type=int, default=2000)
    ap.add_argument("--rows-only", action="store_true",
                    help="write strategy_rows.csv for plans already mapped; no model call")
    a = ap.parse_args(argv)
    if a.rows_only:
        for slug in a.country:
            print("== %s" % slug, flush=True)
            write_rows(slug, os.path.abspath(os.path.expanduser(a.pv2)))
        return 0
    ledger = llm.Ledger(a.max_cost, a.max_calls, dry_run=a.dry_run)
    client = llm.LLMClient(ledger, dry_run=a.dry_run)
    tree = T.load()
    failed = 0
    for slug in a.country:
        try:
            import_country(slug, os.path.abspath(os.path.expanduser(a.pv2)), client, tree)
        except (llm.BudgetExceeded, llm.StageAborted) as e:
            print("STOPPED %s: %s" % (slug, e), flush=True)
            failed += 1
            break
        if not a.dry_run:
            c = stack.stack_country(slug)
            print("stacked %s: %d strategies, %d edition rows -> %s" % (
                slug, len(c["strategies"]), len(c["editions"]), stack.country_dir(slug)), flush=True)
    print(ledger.report(), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
