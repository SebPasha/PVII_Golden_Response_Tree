"""The real mapping of the earlier run's strategies onto tree v4: the workflow's step M (M_map_v4,
gpt-5.4), one call per 25 strategies of one country, in place of the objective-label crosswalk.

    cd tree/v4/poc && python3 map_run.py <out folder of reshape.py> [--dry-run] [--max-cost 30] [--country thailand]
    python3 map_run.py <out>/sector        # likewise the sector plans, UNGA statements or budget lines (sources.py)
    python3 map_run.py <out>/budget --batch 50

Each distinct strategy is mapped once (a strategy that runs through several plan editions has the
same name, objective, target and instrument in each) and the answer applies to all its editions.
Reads <out>/strategies.csv; writes <out>/mapping.csv (one row per source strategy) and
<out>/mapping_run.json (counts and cost). Answers are cached, so a re-run after a stop pays only for
what is missing. Then `python3 reshape.py <data> <out> --mapping=<out>/mapping.csv` places the
strategies by the mapping instead of the crosswalk.
"""
import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "workflow"))
from pvii import config, llm, steps, tree as T  # noqa: E402

COLS = ["source_strategy_key", "country", "slug", "name", "relation", "node_id", "level", "group_id", "family_id",
        "lever_id", "pathway_id", "new_objective", "reason", "proposal", "target_id", "target_label",
        "instrument_id", "instrument_label", "confidence", "map_note"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--dry-run", action="store_true", help="price the run, spend nothing")
    ap.add_argument("--max-cost", type=float, default=30.0)
    ap.add_argument("--country", default="", help="one country slug only")
    ap.add_argument("--batch", type=int, default=steps.MAP_BATCH, help="strategies per call")
    ap.add_argument("--concurrency", type=int, default=0, help="calls at once (default: the workflow's)")
    a = ap.parse_args()
    csv.field_size_limit(10 ** 9)

    rows = list(csv.DictReader(open(os.path.join(a.out, "strategies.csv"), encoding="utf-8")))
    plans = collections.defaultdict(dict)
    years = collections.defaultdict(set)
    uniq = {}
    for r in sorted(rows, key=lambda r: (r["slug"], int(r["period_start"]))):
        plans[r["slug"]][r["plan_id"]] = "%s, %s-%s" % (r["plan_title"], r["period_start"], r["period_end"])
        typ = r.get("doc_type", "ndp")
        if r.get("statement_type") == "overhead":   # placed by rule in sources.py
            continue
        years[r["slug"]].add(r["period_start"])
        q = r["quote"] if r["quote"] != r["name"] else ""
        if typ == "budget":
            q = "budget heading: %s" % r["pillar"] if r["pillar"] else ""
        u = uniq.setdefault(r["source_strategy_key"], dict(
            source_strategy_key=r["source_strategy_key"], country=r["country"], slug=r["slug"], name=r["name"],
            objective=r["objective"], target_group=r["target_group"], instrument=r["instrument"], quote="", quote_en="",
            typ=typ, group=r["plan_id"] if typ == "sector" else r["slug"],
            plan="%s, %s-%s" % (r["plan_title"], r["period_start"], r["period_end"])))
        if not u["quote"] and q:
            u["quote"] = q
    by = collections.defaultdict(list)
    for u in uniq.values():
        if not a.country or u["slug"] == a.country:
            by[u["group"]].append(u)

    t = T.load()
    prompt, menu = config.load_prompt("M"), t.menu()
    ledger = llm.Ledger(a.max_cost, config.MAX_CALLS, dry_run=a.dry_run)
    client = llm.LLMClient(ledger, dry_run=a.dry_run)
    batches = []
    for g in sorted(by):
        ss = sorted(by[g], key=lambda u: u["name"].lower())
        c, typ = ss[0]["country"], ss[0]["typ"]
        if typ == "sector":
            doc = ("Country: %s. The strategies below come from one of its sector plans or policies: %s."
                   % (c, ss[0]["plan"]))
        elif typ == "unga":
            doc = ("Country: %s. Each line below is a passage of its statement to the UN General Assembly general "
                   "debate in %s, in the speaker's words, with what the passage advances as its objective. Place the "
                   "policy the passage commits to or calls for." % (c, ", ".join(sorted(years[ss[0]["slug"]]))))
        elif typ == "budget":
            doc = ("Country: %s. Each line below is a programme of its national budget for fiscal years %s: the programme's name, its "
                   "description where the budget gives one, and the budget heading it sits under. Place the programme "
                   "by what it funds." % (c, ", ".join(sorted(years[ss[0]["slug"]]))))
        else:
            doc = ("Country: %s. The strategies below come from its national development plans and visions, "
                   "pooled across editions: %s." % (c, "; ".join(plans[ss[0]["slug"]].values())))
        batches += [(doc, ss[i:i + a.batch]) for i in range(0, len(ss), a.batch)]
    print("%d strategies, %d countries, %d calls, tree %s (%d live families)" % (
        sum(len(b) for _, b in batches), len(by), len(batches), t.version, len(t.mid) - len(t.closed & set(t.mid))),
        flush=True)

    def build(item):
        doc, batch = item
        lines = ["%d | %s | %s | %s | %s | %s" % (
            i + 1, s["name"], s["objective"], s["target_group"] or "-", s["instrument"] or "-",
            (s["quote_en"] or s["quote"])[:400]) for i, s in enumerate(batch)]
        return "%s%sTHE TREE\n%s%sTHE DOCUMENT\n%s%sSTRATEGIES\n%s\n" % (
            prompt, steps.SEP, menu, steps.SEP, doc, steps.SEP, "\n".join(lines))

    stopped = ""
    try:
        results, errors = client.map("M", batches, build, label="batch", expect="array",
                                     concurrency=a.concurrency or None)
    except (llm.BudgetExceeded, llm.StageAborted) as e:
        stopped, results, errors = str(e), [None] * len(batches), []
    print(ledger.report(), flush=True)
    if a.dry_run or stopped:
        if stopped:
            print("STOPPED: %s (answers so far are cached; run again to finish)" % stopped)
        return 1 if stopped else 0

    out = []
    for (doc, batch), res in zip(batches, results):
        answers = {}
        for x in res if isinstance(res, list) else []:
            try:
                answers[int(x.get("id"))] = x
            except (AttributeError, TypeError, ValueError):
                continue
        for i, s in enumerate(batch):
            steps.resolve(s, answers.get(i + 1), t)
            out.append({k: s.get(k, "") for k in COLS})
    with open(os.path.join(a.out, "mapping.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(out)
    rec = {"strategies": len(out), "calls": len(batches), "errors": [e[1] for e in errors][:20],
           "relation": collections.Counter(r["relation"] for r in out),
           "level": collections.Counter(r["level"] for r in out), "ledger": ledger.as_dict(),
           "tree_version": t.version, "prompt_sha": steps.sha(prompt)}
    json.dump(rec, open(os.path.join(a.out, "mapping_run.json"), "w"), indent=1, default=str)
    print("wrote mapping.csv: %d strategies; %s; %s" % (len(out), dict(rec["relation"]), dict(rec["level"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
