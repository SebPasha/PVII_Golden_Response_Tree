"""Double-coding check of the Thai 13th Plan placements on tree v4: python3 double_coding.py

Reads inputs/double_coding/sample_key.json (the run's placement of the 119 sampled strategies, gpt-5.4
with M_map_v4), coder1.json and coder2.json (two independent blind codings from the same codebook:
family first, then a lever by its joins_when / joins_not tests), and writes
thailand/plan_13th/double_coding.csv (one row per strategy with the three codings) and
inputs/double_coding/summary.json (agreement and Cohen's kappa at family and lever level)."""
import csv, json, os, collections, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "inputs", "double_coding")
OUT = os.path.join(HERE, "thailand", "plan_13th", "double_coding.csv")


def kappa(a, b):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    key = {r["strategy_id"]: r for r in json.load(open(os.path.join(D, "sample_key.json"), encoding="utf-8"))}
    c1 = {r["strategy_id"]: r for r in json.load(open(os.path.join(D, "coder1.json"), encoding="utf-8"))}
    c2 = {r["strategy_id"]: r for r in json.load(open(os.path.join(D, "coder2.json"), encoding="utf-8"))}
    blind = {r["strategy_id"]: r for r in json.load(open(os.path.join(D, "sample_blind.json"), encoding="utf-8"))}
    tree = json.load(open(os.path.join(HERE, "tree_v4.json"), encoding="utf-8"))
    lname = {l["lever_id"]: l["lever"] for l in tree["levers"]}
    fname = {f["family_id"]: f["family"] for f in tree["families"]}
    ids = [s for s in key if s in c1 and s in c2]
    assert len(ids) == len(key), (len(ids), len(key))
    coders = {"run": key, "coder1": c1, "coder2": c2}
    rows, summary = [], {"n": len(ids), "pairs": {}}
    for s in ids:
        b = blind[s]
        r = {"strategy_id": s, "name": b["name"], "objective": b["objective"], "quote_en": b["quote_en"]}
        for c, src in coders.items():
            x = src[s]
            r[c + "_family_id"] = x.get("family_id", "")
            r[c + "_lever_id"] = x.get("lever_id", "")
            r[c + "_lever"] = lname.get(x.get("lever_id", ""), "")
            r[c + "_reason"] = x.get("reason", "")
        fams = {r[c + "_family_id"] for c in coders}
        levs = {r[c + "_lever_id"] for c in coders}
        r["family_agreement"] = "all three" if len(fams) == 1 else ("two of three" if len(fams) == 2 else "none")
        r["lever_agreement"] = "all three" if len(levs) == 1 else ("two of three" if len(levs) == 2 else "none")
        r["run_family"] = fname.get(r["run_family_id"], "")
        rows.append(r)
    for a, b in itertools.combinations(coders, 2):
        fa = [coders[a][s].get("family_id", "") for s in ids]; fb = [coders[b][s].get("family_id", "") for s in ids]
        la = [coders[a][s].get("lever_id", "") for s in ids]; lb = [coders[b][s].get("lever_id", "") for s in ids]
        # lever agreement among strategies both coders put on a lever
        both = [(x, y) for x, y in zip(la, lb) if x and y]
        pf, kf = kappa(fa, fb); pl, kl = kappa(la, lb)
        pb = sum(1 for x, y in both if x == y) / len(both) if both else 0
        summary["pairs"]["%s vs %s" % (a, b)] = {"family_agreement": round(pf, 3), "family_kappa": round(kf, 3),
                                                 "lever_agreement": round(pl, 3), "lever_kappa": round(kl, 3),
                                                 "both_on_lever": len(both), "lever_agreement_when_both": round(pb, 3)}
    summary["family_all_three"] = sum(1 for r in rows if r["family_agreement"] == "all three")
    summary["lever_all_three"] = sum(1 for r in rows if r["lever_agreement"] == "all three")
    summary["on_lever"] = {c: sum(1 for s in ids if coders[c][s].get("lever_id")) for c in coders}
    # disagreement by run lever: where the run's lever is contested
    contested = collections.Counter(key[s]["lever_id"] for s in ids if key[s].get("lever_id") and
                                    not (c1[s].get("lever_id") == key[s]["lever_id"] or c2[s].get("lever_id") == key[s]["lever_id"]))
    summary["run_lever_not_matched_by_either_coder"] = dict(contested.most_common())
    cols = ["strategy_id", "name", "objective", "quote_en", "run_family_id", "run_family", "run_lever_id", "run_lever", "run_reason",
            "coder1_family_id", "coder1_lever_id", "coder1_lever", "coder1_reason",
            "coder2_family_id", "coder2_lever_id", "coder2_lever", "coder2_reason", "family_agreement", "lever_agreement"]
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    json.dump(summary, open(os.path.join(D, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
