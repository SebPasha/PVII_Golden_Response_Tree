"""Link national and sector plan responses to the budget lines that fund them, where the match is clear. No model calls.

    cd migration && python3 budget_links.py <out folder>

A budget line is linked to a response only when all of these hold:
  - same country, and both are placed on the same lever;
  - the budget's fiscal year falls inside the plan's period;
  - the two share a two-word phrase of content words, such as "green building", "water supply" or
    "renewable energy" (stop words and generic budget words such as programme, development, ministry are left out
    first, and plural endings are dropped).
A response keeps its three best lines (most shared phrases, then the largest amount). Anything less clear is left
unlinked: a lever's other budget lines still show on the page, just not tied to a response.

Writes <out>/budget_links.csv, which viewer.py puts on the page (run it after add_country.py / restore_levers.py and
before viewer.py; run_migration.sh does).
"""
import collections
import csv
import os
import re
import sys

csv.field_size_limit(10 ** 9)

STOP = set("""a an and the of for in on to with by from at as or its their into under over through per via new all other
general national state federal government public ministry department office division unit agency authority council commission
programme program programmes programs project projects scheme schemes plan plans policy policies strategy strategies sector
sectors development develop improve improvement improving strengthen strengthening enhance enhancement support supporting
promotion promote promoting management services service activities activity operations operation administration administrative
capital recurrent expenditure fund funds funding budget allocation grant grants transfer transfers investment investments
implementation establishment expansion including related etc such various level levels system systems infrastructure facilities
facility capacity building institutional regional local district provincial central other miscellaneous special affairs matters
measures initiative initiatives access quality increase increased provide provision ensure use based between within""".split())
# "building" is generic in "capacity building" but not in "green building": keep it as a content word after "green"
KEEP_AFTER = {("green", "building"), ("school", "building"), ("government", "building")}


def stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def phrases(text):
    """Adjacent pairs of content words (after stop words are dropped)."""
    raw = [stem(x) for x in re.findall(r"[a-z]{3,}", (text or "").lower())]
    out, prev = set(), None
    for w in raw:
        if w in STOP and (prev, w) not in KEEP_AFTER:
            continue          # stop words are dropped, so "control of water pollution" gives "water pollution"
        if prev and prev != w:
            out.add((prev, w))
        prev = w
    return out


def amount(r):
    try:
        return float(str(r.get("amount") or "").replace(",", ""))
    except ValueError:
        return 0.0


def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = sys.argv[1]
    budget = [r for r in read(os.path.join(out, "budget", "strategies.csv")) if r["lever_id"]]
    resp = [dict(r, source="national") for r in read(os.path.join(out, "strategies.csv")) if r["lever_id"]] + \
           [dict(r, source="sector") for r in read(os.path.join(out, "sector", "strategies.csv")) if r["lever_id"]]
    by = collections.defaultdict(list)
    for b in budget:
        b["_p"] = phrases(b["name"])
        by[(b["slug"], b["lever_id"])].append(b)
    links = []
    for r in resp:
        cand = by.get((r["slug"], r["lever_id"]))
        if not cand:
            continue
        rp = phrases(r["name"] + " . " + r["objective"])
        s0, s1 = int(r["period_start"]), int(r["period_end"])
        hits = []
        for b in cand:
            if not s0 <= int(b["period_start"]) <= s1:
                continue
            sh = rp & b["_p"]
            if sh:
                hits.append((len(sh), amount(b), b, sh))
        hits.sort(key=lambda x: (-x[0], -x[1]))
        for _, _, b, sh in hits[:3]:
            links.append({"response_id": r["strategy_id"], "source": r["source"], "country": r["country"], "slug": r["slug"],
                          "lever_id": r["lever_id"], "plan_id": r["plan_id"], "response": r["name"],
                          "budget_id": b["strategy_id"], "budget_plan_id": b["plan_id"], "fiscal_year": b["period_start"],
                          "budget_line": b["name"], "amount": b.get("amount", ""), "currency": b.get("currency", ""),
                          "shared": "; ".join(sorted(" ".join(p) for p in sh))})
    cols = ["response_id", "source", "country", "slug", "lever_id", "plan_id", "response", "budget_id", "budget_plan_id",
            "fiscal_year", "budget_line", "amount", "currency", "shared"]
    with open(os.path.join(out, "budget_links.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(links)
    print("wrote budget_links.csv: %d links, %d responses, %d budget lines, %d countries, %d levers" % (
        len(links), len({x["response_id"] for x in links}), len({x["budget_id"] for x in links}),
        len({x["slug"] for x in links}), len({x["lever_id"] for x in links})))


if __name__ == "__main__":
    main()
