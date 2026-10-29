"""The workflow, one plan at a time.

    python -m pvii.run --list thailand                          # every document and whether it runs
    python -m pvii.run --plan thailand_ndp_2023-2027 --dry-run  # price it, spend nothing
    python -m pvii.run --plan thailand_ndp_2023-2027            # C, E, F, M, then stack thailand
    python -m pvii.run --country thailand --doc-types ndp       # every runnable plan of one type
    python -m pvii.run --global                                 # stack every country, no model calls

Responses are cached by prompt, so a re-run after a failure, or after editing context.json,
spends only on the calls whose prompt changed. Exit codes: 0 done, 1 a step failed, 2 could
not start.
"""
import argparse
import datetime
import os
import sys

from pvii import config, io, llm, parse, plans as P, stack, steps, tree as T

STEPS = ("C", "E", "F", "M")


def run_plan(plan, client, steps_wanted=STEPS, force_context=False):
    why = plan.why_not_runnable()
    if why:
        raise SystemExit("%s does not run: %s" % (plan.plan_id or plan.file, why))
    missing = [p for p in plan.paths if not os.path.exists(p)] if plan.paths else ["(no file)"]
    if missing:
        raise SystemExit("source document not found: %s (set PVII_SOURCES_ROOT)" % missing[0])
    out = P.plan_dir(plan.plan_id)
    os.makedirs(out, exist_ok=True)
    started = datetime.datetime.now().isoformat(timespec="seconds")
    print("== %s: %s (%s-%s)" % (plan.plan_id, plan.title, plan.start, plan.end), flush=True)
    doc = parse.parse_documents(plan.paths)
    print("parsed: %d pages, %d paragraphs" % (doc.page_count, len(doc.paragraphs)), flush=True)
    record = {"plan_id": plan.plan_id, "started": started, "file": plan.file,
              "pages": doc.page_count, "paragraphs": len(doc.paragraphs),
              "prompts": {s: steps.sha(steps.e_prompt() if s == "E" else config.load_prompt(s))
                          for s in config.PROMPT_FILES},
              "models": {s: config.STAGE_MODELS[s] for s in config.STAGE_MODELS},
              "dry_run": bool(client.dry_run)}
    ctx = steps.context(client, plan, doc, out, force=force_context) if "C" in steps_wanted \
        else (io.read_json(os.path.join(out, "context.json")) or {})
    plan.published = steps.published(ctx)
    result = {}
    if "E" in steps_wanted:
        result = steps.extract(client, plan, doc, ctx, out)
        record["extract"] = {"risks": len(result["risks"]), "rows": len(result["rows"]),
                             "dropped": len(result["dropped"]), "errors": result["errors"][:20],
                             "invalid": result["invalid"][:20], "guards": result["guards"],
                             "quote_checks": _count(result["rows"] + result["risks"], "quote_check")}
    if client.dry_run:
        _dry_run_rest(client, plan, doc, steps_wanted)
    elif "F" in steps_wanted or "M" in steps_wanted:
        rows = result.get("rows") if result else _rows_from_disk(out)
        strategies, f_errors = steps.fold(client, plan, rows, out)
        record["fold"] = {"rows": len(rows), "strategies": len(strategies), "errors": f_errors[:20]}
        if "M" in steps_wanted:
            t = T.load()
            strategies, proposals, m_errors = steps.map_to_tree(client, plan, strategies, ctx, t, out)
            record["map"] = {"tree_version": t.version, "strategies": len(strategies),
                             "proposals": len(proposals), "errors": m_errors[:20],
                             "relations": _count(strategies, "relation"),
                             "levels": _count(strategies, "level"),
                             "response_orientation": _count(strategies, "response_orientation"),
                             "subpillar": _count(strategies, "subpillar")}
    record["ledger"] = client.ledger.as_dict()
    record["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    if not client.dry_run:
        io.write_json(os.path.join(out, "run.json"), record)
        with open(os.path.join(out, "cost_report.md"), "w", encoding="utf-8") as f:
            f.write(client.ledger.report())
    return record


def _rows_from_disk(out):
    rows = io.read_csv(os.path.join(out, "strategy_rows.csv"))
    for r in rows:
        for k in ("related_risks", "risk_evidence", "sdg_targets", "quantified_targets",
                  "named_agencies"):
            r[k] = io.as_list(r.get(k))
        r["target_year"] = steps._year(r.get("target_year"))
    return rows


def _dry_run_rest(client, plan, doc, steps_wanted):
    """F and M priced on an assumed yield, since a dry run has no rows to fold or map."""
    est_strategies = max(1, len(doc.paragraphs) // 3)
    if "F" in steps_wanted:
        for _ in range(max(1, est_strategies // steps.FOLD_SHARD_MAX + 1)):
            client.call("F", config.load_prompt("F") + "x" * 4 * 60 * 40, expect="array")
    if "M" in steps_wanted:
        menu = T.load().menu()
        for _ in range(max(1, est_strategies // steps.MAP_BATCH + 1)):
            client.call("M", config.load_prompt("M") + menu + "x" * 4 * 25 * 60, expect="array")
    print("dry run: F and M priced on about %d strategies (one per three paragraphs)"
          % est_strategies, flush=True)


def _count(rows, key):
    out = {}
    for r in rows:
        out[r.get(key) or ""] = out.get(r.get(key) or "", 0) + 1
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", help="one plan_id, e.g. thailand_ndp_2023-2027")
    g.add_argument("--country", help="every runnable plan of one country")
    g.add_argument("--global", dest="global_", action="store_true", help="stack only")
    g.add_argument("--list", metavar="SLUG", help="list a country's documents and plan_ids")
    ap.add_argument("--doc-types", default="", help="with --country: e.g. ndp or ndp,sector")
    ap.add_argument("--steps", default="C,E,F,M", help="a subset of C,E,F,M")
    ap.add_argument("--dry-run", action="store_true", help="price the run, spend nothing")
    ap.add_argument("--max-cost", type=float, default=config.MAX_COST_USD)
    ap.add_argument("--max-calls", type=int, default=config.MAX_CALLS)
    ap.add_argument("--force-context", action="store_true", help="re-read C over an existing file")
    a = ap.parse_args(argv)

    if a.list:
        for p in P.load_country(a.list):
            why = p.why_not_runnable()
            print("%-62s %s" % (p.plan_id or "(no plan_id)", "RUNS" if not why else why))
            print("    %s" % p.file)
        return 0
    if a.global_:
        g = stack.stack_global()
        print("global: %d plans, %d strategies, %d risk records -> %s"
              % (sum(1 for p in g["plans"] if p.get("status") == "run"), len(g["strategies"]),
                 len(g["risks"]), stack.global_dir()))
        return 0

    wanted = tuple(s.strip().upper() for s in a.steps.split(",") if s.strip())
    if a.plan:
        todo = [P.find(a.plan)]
    else:
        types = tuple(t.strip() for t in a.doc_types.split(",") if t.strip()) or None
        todo = P.runnable(a.country, types)
    if not todo:
        print("nothing to run")
        return 2
    parse.DRY_RUN = a.dry_run
    ledger = llm.Ledger(a.max_cost, a.max_calls, dry_run=a.dry_run)
    client = llm.LLMClient(ledger, dry_run=a.dry_run)
    failed = 0
    for p in todo:
        try:
            run_plan(p, client, wanted, force_context=a.force_context)
        except (llm.BudgetExceeded, llm.StageAborted) as e:
            print("STOPPED %s: %s" % (p.plan_id, e), flush=True)
            failed += 1
            break
        except Exception as e:                       # one plan's failure does not stop the rest
            print("FAILED %s: %s: %s" % (p.plan_id, type(e).__name__, e), flush=True)
            failed += 1
    print(ledger.report(), flush=True)
    if not a.dry_run:
        for slug in sorted({p.slug for p in todo}):
            c = stack.stack_country(slug)
            print("stacked %s: %d strategies, %d risk records -> %s"
                  % (slug, len(c["strategies"]), len(c["risks"]), stack.country_dir(slug)))
        stack.stack_global()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
