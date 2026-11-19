"""Name the policy instrument of every strategy the mapping left without one (gpt-5.4, 50 strategies a call).

    cd tree/v4/poc && python3 inst_run.py <folder with strategies.csv> [--mapping <mapping.csv>] [--dry-run] [--max-cost 30]

The mapping (map_run.py) takes an instrument only from the tree's short instrument list, so most
strategies come back without one. This pass names each one's instrument in plain words, its class
(money, authority, information, organisation) and the list entry where one fits. Reads
<folder>/strategies.csv and the mapping (default <folder>/mapping.csv); writes <folder>/instrument.csv.
Answers are cached like the mapping's.
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "workflow"))
from pvii import config, llm, steps  # noqa: E402

BATCH = 50
CLASSES = ("Money", "Authority", "Information", "Organisation")
PROMPT = """Role

Public policy analyst naming the instrument of each government strategy.

Task

For each strategy below, name its policy instrument: the main tool the government uses to deliver it.
Judge from what the strategy does, not from its sector.

1. instrument: two to six plain English words, in the singular, at the level of a tool, for example
   "Conditional cash transfer", "Public works programme", "Building and running facilities",
   "Law or regulation", "Product standards", "Tax incentive", "Concessional loan", "Training programme",
   "Information campaign", "Data system", "Research funding", "Plan or strategy", "Public-private partnership",
   "Agency or coordinating body", "Inspection and enforcement", "Procurement reform".
2. instrument_class, exactly one of:
   Money          the state pays, lends, insures, subsidises, or forgoes tax;
   Authority      the state commands, permits, prohibits, taxes or sets standards;
   Information    the state informs, advises, persuades, plans, collects or shares data, or funds research;
   Organisation   the state provides directly: services, facilities, staff, agencies, programmes it runs.
3. instrument_id: the entry of THE LIST below that is the same instrument, or "" where none is.

Where a line names a goal and no tool, give the tool its wording most implies and set confidence to low.

THE LIST
%s

Output

A valid JSON array only, one object per strategy in the order given, no markdown and no commentary:

[{"id": 1, "instrument": "", "instrument_class": "", "instrument_id": "", "confidence": ""}]
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--mapping", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-cost", type=float, default=30.0)
    ap.add_argument("--concurrency", type=int, default=6)
    a = ap.parse_args()
    csv.field_size_limit(10 ** 9)
    tree = json.load(open(os.path.join(HERE, "..", "tree_v4.json"), encoding="utf-8"))
    lst = "\n".join("%s | %s | %s" % (i["instrument_id"], i["instrument_label"], i["instrument_class"])
                    for i in tree["instrument_classes"])
    prompt = PROMPT % lst
    mp_path = a.mapping or os.path.join(a.folder, "mapping.csv")
    have = {r["source_strategy_key"] for r in csv.DictReader(open(mp_path, encoding="utf-8")) if r["instrument_id"]} \
        if os.path.exists(mp_path) else set()
    uniq = {}
    for r in csv.DictReader(open(os.path.join(a.folder, "strategies.csv"), encoding="utf-8")):
        k = r["source_strategy_key"]
        if k in have or k in uniq or r.get("statement_type") == "overhead":
            continue
        q = r["quote"] if r["quote"] != r["name"] else ""
        uniq[k] = (r["country"], r["name"], r["objective"], (q or r.get("pillar", ""))[:300])
    keys = sorted(uniq, key=lambda k: (uniq[k][0], uniq[k][1].lower()))
    batches = [keys[i:i + BATCH] for i in range(0, len(keys), BATCH)]
    print("%d strategies without an instrument, %d calls" % (len(keys), len(batches)), flush=True)

    ledger = llm.Ledger(a.max_cost, config.MAX_CALLS, dry_run=a.dry_run)
    client = llm.LLMClient(ledger, dry_run=a.dry_run)

    def build(batch):
        lines = ["%d | %s | %s | %s | %s" % ((i + 1,) + uniq[k]) for i, k in enumerate(batch)]
        return "%s%sSTRATEGIES (id | country | name | objective | quote or heading)\n%s\n" % (
            prompt, steps.SEP, "\n".join(lines))

    try:
        results, errors = client.map("I", batches, build, model=config.MODEL_LARGE, label="batch", expect="array",
                                     concurrency=a.concurrency, max_tokens=12000)
    except (llm.BudgetExceeded, llm.StageAborted) as e:
        print(ledger.report())
        print("STOPPED: %s (answers so far are cached; run again to finish)" % e)
        return 1
    print(ledger.report(), flush=True)
    if a.dry_run:
        return 0
    ids = {i["instrument_id"]: i["instrument_label"] for i in tree["instrument_classes"]}
    out = []
    for batch, res in zip(batches, results):
        ans = {}
        for x in res if isinstance(res, list) else []:
            try:
                ans[int(x.get("id"))] = x
            except (AttributeError, TypeError, ValueError):
                continue
        for i, k in enumerate(batch):
            x = ans.get(i + 1) or {}
            cl = x.get("instrument_class", "") if x.get("instrument_class") in CLASSES else ""
            iid = x.get("instrument_id", "") if x.get("instrument_id") in ids else ""
            out.append(dict(source_strategy_key=k, instrument=str(x.get("instrument") or "").strip(), instrument_class=cl,
                            instrument_id=iid, instrument_label=ids.get(iid, ""), confidence=x.get("confidence", "")))
    with open(os.path.join(a.folder, "instrument.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("wrote instrument.csv: %d strategies, %d named, %d errors" % (
        len(out), sum(1 for r in out if r["instrument"]), len(errors)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
