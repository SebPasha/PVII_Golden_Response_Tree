"""The real mapping of the earlier run's strategies onto tree v4: the workflow's step M (M_map_v4,
gpt-5.4), one call per 25 strategies of one country, in place of the objective-label crosswalk.

    cd tree/v4/poc && python3 map_run.py <out folder of reshape.py> [--dry-run] [--max-cost 30] [--country thailand]

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
    a = ap.parse_args()
    csv.field_size_limit(10 ** 9)

    rows = list(csv.DictReader(open(os.path.join(a.out, "strategies.csv"), encoding="utf-8")))
    plans = collections.defaultdict(dict)
    uniq = {}
    for r in sorted(rows, key=lambda r: (r["slug"], int(r["period_start"]))):
        plans[r["slug"]][r["plan_id"]] = "%s, %s-%s" % (r["plan_title"], r["period_start"], r["period_end"])
        u = uniq.setdefault(r["source_strategy_key"], dict(
            source_strategy_key=r["source_strategy_key"], country=r["country"], slug=r["slug"], name=r["name"],
            objective=r["objective"], target_group=r["target_group"], instrument=r["instrument"], quote="", quote_en=""))
        if not u["quote"] and r["quote"]:
            u["quote"] = r["quote"]
    by = collections.defaultdict(list)
    for u in uniq.values():
        if not a.country or u["slug"] == a.country:
            by[u["slug"]].append(u)

    t = T.load()
    prompt, menu = config.load_prompt("M"), t.menu()
    ledger = llm.Ledger(a.max_cost, config.MAX_CALLS, dry_run=a.dry_run)
    client = llm.LLMClient(ledger, dry_run=a.dry_run)
    batches = []
    for slug in sorted(by):
        ss = sorted(by[slug], key=lambda u: u["name"].lower())
        doc = ("Country: %s. The strategies below come from its national development plans and visions, "
               "pooled across editions: %s." % (ss[0]["country"], "; ".join(plans[slug].values())))
        batches += [(doc, ss[i:i + steps.MAP_BATCH]) for i in range(0, len(ss), steps.MAP_BATCH)]
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
        results, errors = client.map("M", batches, build, label="batch", expect="array")
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
