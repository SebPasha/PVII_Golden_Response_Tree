"""Key messages, bottom up: the chains behind each country's plan.

For one plan edition (or every edition of a country) this lays out the chain in the key-messages notes:

    risks and opportunities (the 11 megatrends) + comparative advantages
        -> mechanism (the lever on tree v4, or its family where no lever fits)
        -> objective (Growth = Smarter Growth, Wellbeing = People-first Approach,
                      Governance = Making Change Happen, the RHDR pillars)
        -> instrument (what the state uses: Money, Authority, Information, Organisation)
        -> target (the group of people the objective is for)

It reads the page build's outputs (run ./run_migration.sh first) and makes no model calls. One row per
mechanism family, ranked by how much of the plan it takes (mentions), with the budget lines placed on
the same family for each budget year the country has. Comparative advantages are not in the data yet
(the C step does not ask for them); the write-up drafts them by hand for the pilot.

    python3 key_messages.py ../data/migration_out brazil_ndp_2024-2027 [--out key_messages_brazil.json]
"""
import argparse
import collections
import csv
import json
import os
import re

csv.field_size_limit(10 ** 9)

OBJECTIVE = {"Smarter Growth": "Growth", "People-first Approach": "Wellbeing",
             "Making Change Happen": "Governance"}
MEGATRENDS = ["Climate Change", "Pandemics", "Biodiversity Loss", "Environmental Degradation and Pollution",
              "Resource and Energy Pressures", "Shifts in Globalisation", "Technological Change",
              "Demographic Shifts", "Democratic Backsliding", "Growing Populism", "Increased Polarisation"]


def instrument_class(label):
    m = re.search(r"\((Money|Authority|Information|Organisation)\)", label or "")
    return m.group(1) if m else ""


def load(path, keep):
    with open(path, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if keep(r)]


def chains(rows, budget):
    fam = collections.OrderedDict()
    for r in rows:
        key = r["family_id"] or "off-tree"
        c = fam.setdefault(key, {"family": r["family"] or "Not on a lever family", "group": r["group"],
                                 "objective": OBJECTIVE.get(r["pillar_rhdr"], "Not placed"),
                                 "mentions": 0, "strategies": [], "levers": collections.Counter(),
                                 "risks": collections.Counter(), "instruments": collections.Counter(),
                                 "instrument_classes": collections.Counter(), "targets": collections.Counter(),
                                 "budget_bn": {}})
        n = int(r["n_mentions"] or 1)
        c["mentions"] += n
        c["strategies"].append({"name": r["name"], "mentions": n, "lever": r["lever"],
                                "instrument": r.get("instrument_label") or r.get("instrument", ""), "target": r["target_label"] or r["target_group"],
                                "risks": json.loads(r["related_risks"] or "[]"),
                                "orientation": r["response_orientation"]})
        if r["lever_id"]:
            c["levers"][f'{r["lever_id"]} {r["lever"]}'] += n
        for x in json.loads(r["related_risks"] or "[]"):
            c["risks"][x] += n
        ins = r.get("instrument_label") or r.get("instrument") or ""
        if ins:
            c["instruments"][ins] += n
            c["instrument_classes"][instrument_class(ins) or "unclassed"] += n
        t = r["target_label"] or r["target_group"]
        if t:
            c["targets"][t] += n
    for b in budget:
        key = b["family_id"]
        if key in fam and b["amount"]:
            y = b["period_start"]
            fam[key]["budget_bn"][y] = round(fam[key]["budget_bn"].get(y, 0) + float(b["amount"]) / 1000, 2)
    total = sum(c["mentions"] for c in fam.values()) or 1
    out = []
    for k, c in fam.items():
        out.append({"family_id": k, **c, "share": round(c["mentions"] / total, 3),
                    "levers": c["levers"].most_common(), "risks": c["risks"].most_common(),
                    "instruments": c["instruments"].most_common(5),
                    "instrument_classes": c["instrument_classes"].most_common(),
                    "targets": c["targets"].most_common(5),
                    "strategies": sorted(c["strategies"], key=lambda s: -s["mentions"])})
    return sorted(out, key=lambda c: -c["mentions"])


def risk_coverage(rows):
    cov = {m: {"strategies": 0, "mentions": 0, "families": collections.Counter()} for m in MEGATRENDS}
    for r in rows:
        for x in json.loads(r["related_risks"] or "[]"):
            if x in cov:
                cov[x]["strategies"] += 1
                cov[x]["mentions"] += int(r["n_mentions"] or 1)
                cov[x]["families"][r["family"] or "Not on a lever family"] += 1
    return {m: {**v, "families": v["families"].most_common(4)} for m, v in cov.items()}


def plan_rows(out_dir, plan):
    """A plan's strategies: from a workflow plan folder (holding strategies.csv), or by plan_id or country
    slug from the page build's outputs."""
    if os.path.isdir(plan) and os.path.exists(os.path.join(plan, "strategies.csv")):
        return load(os.path.join(plan, "strategies.csv"), lambda r: True)
    return load(os.path.join(out_dir, "strategies.csv"), lambda r: plan in (r["plan_id"], r["slug"]))


def build(out_dir, plan):
    rows = plan_rows(out_dir, plan)
    if not rows:
        raise SystemExit(f"no strategies for {plan}")
    slug = rows[0]["slug"]
    budget = load(os.path.join(out_dir, "budget", "strategies.csv"), lambda r: r["slug"] == slug)
    r0 = rows[0]
    return {"plan": r0["plan_id"], "country": r0["country"], "slug": slug, "title": r0.get("plan_title", ""), "region": r0.get("region", ""),
            "period": f'{r0.get("period_start", "")}-{r0.get("period_end", "")}', "doc_type": r0.get("doc_type", ""),
            "strategies": len(rows), "mentions": sum(int(r["n_mentions"] or 1) for r in rows),
            "on_a_lever": sum(1 for r in rows if r["lever_id"]),
            "objectives": dict(collections.Counter(OBJECTIVE.get(r["pillar_rhdr"], "Not placed") for r in rows)),
            "budget_years": sorted({b["period_start"] for b in budget}),
            "chains": chains(rows, budget), "risk_coverage": risk_coverage(rows)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", help="the page build's output folder, e.g. ../data/migration_out")
    ap.add_argument("plan", help="a plan_id, a country slug (all its national plan editions), or a workflow plan folder")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    res = build(a.out_dir, a.plan)
    out = a.out or f"key_messages_{res['plan']}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"{res['country']}: {res['strategies']} strategies, {len(res['chains'])} mechanism families -> {out}")
    for c in res["chains"][:12]:
        print(f'  {c["share"]:5.1%} {c["objective"]:10} {c["family"][:45]:45} '
              f'risks={",".join(k for k, _ in c["risks"][:2])} budget={c["budget_bn"]}')


if __name__ == "__main__":
    main()
