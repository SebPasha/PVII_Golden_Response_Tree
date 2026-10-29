"""Test the v2 mechanism level against the bottom-up strategy tree (Strategy Tree Review v48).

    python3 test_bottomup.py /path/to/strategy_tree_v48_review.html

The bottom-up tree groups the 9,918 PV2 strategies of 45 countries into 467 leaf objectives under 19 areas of
government work, with no structure imposed from above. The test asks whether each leaf objective finds one
mechanism in the top-down tree. A leaf is placed through v1 where v1 already put its objective on a pathway
(the pathway's mechanism is the answer); the 223 objectives v1 held at a family are placed by hand on their
definition, as the sibling test would, in OBJECTIVE_MECHANISM below; goals and the Standard branches stay outside.

Writes bottomup_test.json (read by the page) and bottomup_test.csv.
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = json.load(open(os.path.join(HERE, "tree_v2.json"), encoding="utf-8"))
MEC = {m["mechanism_id"]: m for m in TREE["mechanisms"]}
FAM = {f["family_id"]: f for f in TREE["families"]}
PATH = {p["pathway_id"]: p for p in TREE["pathways"]}

# v1 objective id -> v2 mechanism (MEC-xx), family (FAM-xx, when the definition names several levers) or "outside"
OBJECTIVE_MECHANISM = {
 # goals and Standard branches: outside the tree
 "O0062": "outside", "O0190": "outside", "O0248": "outside", "O0254": "outside", "O0264": "outside", "O0267": "outside", "O0268": "outside",
 "O0326": "outside", "O0331": "outside", "O0347": "outside", "O0054": "outside", "O0165": "outside", "O0167": "outside", "O0180": "outside",
 "O0183": "outside", "O0186": "outside", "O0299": "outside", "O0302": "outside", "O0305": "outside", "O0313": "outside", "O0315": "outside",
 "O0316": "outside", "O0321": "outside", "O0379": "outside", "O0082": "outside", "O0091": "outside", "O0179": "outside", "O0217": "outside",
 "O0357": "outside", "O0366": "outside", "O0368": "outside", "O0369": "outside", "O0371": "outside", "O0375": "outside", "O0378": "outside",
 # People-first
 "O0323": "MEC-02", "O0324": "MEC-01", "O0328": "MEC-04", "O0338": "FAM-06",
 "O0306": "MEC-09", "O0308": "MEC-07", "O0332": "MEC-08", "O0374": "MEC-08",
 "O0016": "MEC-22", "O0325": "MEC-20", "O0327": "MEC-20", "O0334": "FAM-06", "O0341": "MEC-20", "O0356": "MEC-20",
 "O0022": "MEC-23", "O0335": "MEC-23",
 "O0059": "MEC-14", "O0073": "MEC-14", "O0244": "MEC-14",
 "O0064": "FAM-04", "O0068": "MEC-12", "O0076": "MEC-15", "O0077": "MEC-12", "O0085": "MEC-13", "O0087": "MEC-12", "O0088": "MEC-15", "O0089": "FAM-04", "O0092": "MEC-15",
 "O0198": "FAM-05", "O0199": "MEC-16", "O0203": "FAM-05", "O0215": "MEC-19", "O0212": "MEC-98", "O0003": "MEC-24",
 "O0050": "MEC-58", "O0330": "FAM-07", "O0408": "FAM-07", "O0417": "MEC-27",
 "O0297": "MEC-06", "O0304": "MEC-05", "O0314": "MEC-06", "O0319": "MEC-06",
 "O0094": "MEC-29", "O0099": "MEC-29", "O0104": "MEC-29", "O0107": "MEC-29", "O0113": "MEC-29", "O0118": "MEC-29", "O0127": "FAM-08", "O0129": "MEC-28",
 "O0136": "FAM-08", "O0138": "FAM-08", "O0141": "FAM-08", "O0149": "FAM-08", "O0397": "MEC-31",
 "O0018": "MEC-33", "O0124": "MEC-32", "O0130": "MEC-33", "O0131": "MEC-34", "O0133": "MEC-32", "O0146": "MEC-32",
 "O0125": "MEC-36", "O0152": "MEC-38", "O0153": "MEC-36", "O0424": "FAM-10", "O0449": "MEC-36", "O0453": "MEC-36",
 "O0119": "MEC-43", "O0121": "MEC-40", "O0156": "FAM-11", "O0427": "MEC-41",
 "O0100": "MEC-45", "O0220": "MEC-45", "O0224": "MEC-45", "O0230": "MEC-45", "O0285": "MEC-44", "O0289": "MEC-44", "O0171": "MEC-46",
 "O0443": "MEC-35", "O0452": "MEC-35", "O0454": "MEC-35", "O0455": "MEC-35",
 # Smarter Growth
 "O0007": "MEC-47", "O0010": "FAM-13", "O0209": "MEC-48", "O0218": "MEC-47", "O0219": "MEC-47", "O0221": "MEC-61", "O0227": "MEC-48", "O0229": "MEC-47",
 "O0232": "MEC-48", "O0261": "MEC-47", "O0358": "MEC-49", "O0381": "MEC-47", "O0388": "MEC-47",
 "O0382": "MEC-51", "O0391": "MEC-51", "O0392": "MEC-51", "O0396": "MEC-51", "O0385": "MEC-52", "O0387": "MEC-52", "O0380": "MEC-53", "O0386": "MEC-53",
 "O0360": "MEC-50", "O0361": "MEC-50", "O0364": "MEC-50", "O0372": "MEC-50", "O0373": "MEC-50", "O0376": "MEC-50",
 "O0035": "MEC-54", "O0039": "MEC-54", "O0040": "MEC-49", "O0042": "MEC-56", "O0043": "FAM-15", "O0052": "MEC-54", "O0053": "MEC-54", "O0055": "MEC-54",
 "O0057": "MEC-54", "O0145": "MEC-54", "O0213": "MEC-54",
 "O0048": "MEC-58", "O0275": "MEC-61", "O0295": "MEC-57", "O0296": "MEC-62", "O0384": "FAM-16", "O0400": "MEC-57", "O0401": "MEC-57", "O0409": "MEC-57", "O0416": "MEC-57",
 "O0406": "MEC-60", "O0418": "MEC-60", "O0421": "MEC-60", "O0428": "MEC-60", "O0430": "MEC-60", "O0431": "MEC-60", "O0435": "MEC-60", "O0437": "MEC-60", "O0439": "MEC-60", "O0442": "MEC-60",
 "O0103": "MEC-59", "O0106": "MEC-59", "O0108": "MEC-59", "O0115": "MEC-59", "O0117": "MEC-59", "O0405": "MEC-59", "O0415": "MEC-59", "O0456": "MEC-59",
 "O0024": "MEC-61", "O0226": "MEC-61", "O0228": "MEC-61", "O0012": "MEC-64",
 "O0002": "MEC-63", "O0006": "MEC-63", "O0011": "MEC-63", "O0014": "MEC-63", "O0021": "MEC-63", "O0026": "MEC-63", "O0027": "MEC-63", "O0030": "MEC-63", "O0033": "MEC-63",
 "O0252": "MEC-65", "O0249": "MEC-70", "O0270": "MEC-70", "O0250": "MEC-71", "O0258": "MEC-71", "O0271": "MEC-71", "O0441": "MEC-71",
 "O0233": "MEC-66", "O0234": "MEC-99", "O0236": "MEC-66", "O0237": "MEC-67", "O0238": "MEC-66",
 "O0015": "MEC-62", "O0272": "MEC-93", "O0291": "MEC-62", "O0292": "MEC-62", "O0294": "MEC-62",
 "O0176": "MEC-69", "O0188": "MEC-69", "O0235": "MEC-69", "O0029": "MEC-72", "O0419": "MEC-72", "O0420": "MEC-72", "O0440": "MEC-72",
 # Making Change Happen
 "O0257": "MEC-76", "O0273": "MEC-76", "O0192": "MEC-77", "O0320": "MEC-77", "O0123": "MEC-91", "O0196": "MEC-91", "O0161": "MEC-74", "O0187": "MEC-74",
 "O0166": "MEC-95", "O0175": "MEC-96", "O0300": "MEC-79", "O0303": "MEC-80", "O0311": "MEC-80", "O0322": "MEC-78",
 "O0041": "MEC-83", "O0051": "MEC-83", "O0182": "MEC-83", "O0269": "MEC-83",
 "O0160": "MEC-84", "O0164": "MEC-84", "O0174": "MEC-84", "O0181": "MEC-84", "O0162": "MEC-86", "O0425": "MEC-86", "O0288": "MEC-88",
 "O0277": "MEC-89", "O0283": "MEC-89", "O0284": "MEC-89", "O0290": "MEC-89", "O0350": "MEC-89", "O0410": "FAM-26",
 "O0111": "MEC-87", "O0120": "MEC-87", "O0157": "MEC-87", "O0168": "MEC-94", "O0329": "FAM-28", "O0354": "MEC-94", "O0363": "MEC-95", "O0169": "MEC-96",
}
# leaf objectives in v48 that v1 never saw (split or added after the 20 October build), placed on their label
NEW_LEAVES = {"O0457": "MEC-70", "O0460": "MEC-57", "O0461": "MEC-62", "O0462": "MEC-06", "O0231_split": "MEC-47", "O0231A": "MEC-47",
              "O0231B": "MEC-47", "O0231C": "MEC-29", "O0463": "MEC-14", "O0464": "outside", "O0136A": "FAM-08", "O0136B": "FAM-08",
              "O0010B": "FAM-13", "O0138A": "MEC-14"}


def main():
    html = open(sys.argv[1], encoding="utf-8").read()
    i = html.index("const D = ") + len("const D = ")
    D = json.loads(html[i:html.index("\n", i)].rstrip(";"))
    N = D["tree"]["nodes"]
    counts = collections.Counter(s[2] for s in D["strategies"])
    v1 = list(csv.DictReader(open(os.path.join(HERE, "..", "v1", "objectives_v1.csv"), encoding="utf-8")))
    src = {}
    for r in v1:
        for o in [x.strip() for x in r["source_objective_ids"].split("|") if x.strip()]:
            src[o] = r
    held = [r["objective_id"] for r in v1 if not r["mechanism_id"]]
    missing = [o for o in held if o not in OBJECTIVE_MECHANISM]
    if missing:
        sys.exit("v1 objectives without a hand placement: %s" % missing)

    def area_of(nid):
        while N[nid].get("parent") not in (None, "ROOT"):
            nid = N[nid]["parent"]
        return N[nid]["label"]

    rows = []
    for oid, node in N.items():
        if not oid.startswith("O") or any(N[k].get("parent") == oid for k in N):
            continue  # not a leaf
        row = {"id": oid, "label": node["label"], "area": area_of(oid), "n": counts.get(oid, 0), "definition": node.get("definition", "")[:300]}
        r = src.get(oid)
        if r and r["mechanism_id"]:
            p = PATH[r["mechanism_id"]]
            mid = p["mechanism_id"]
            row.update(outcome="one mechanism", mechanism=MEC[mid]["mechanism"], mechanism_id=mid, family=MEC[mid]["family"], family_id=MEC[mid]["family_id"],
                       how="through its v1 pathway " + p["pathway"], note="")
        else:
            target = OBJECTIVE_MECHANISM.get(r["objective_id"]) if r else NEW_LEAVES.get(oid)
            how = "by hand on the definition" if r else "by hand on the label (not in the v1 objectives)"
            if target is None:
                row.update(outcome="no home", mechanism="", mechanism_id="", family="", family_id="", how=how, note="no placement")
            elif target == "outside":
                row.update(outcome="outside the tree", mechanism="", mechanism_id="", family="", family_id="", how=how,
                           note="goal-shaped or Standard branch (defence, foreign affairs, culture, sport, religion)")
            elif target.startswith("FAM"):
                row.update(outcome="family only", mechanism="", mechanism_id="", family=FAM[target]["family"], family_id=target, how=how,
                           note="the definition names the domain or several levers at once")
            else:
                row.update(outcome="one mechanism", mechanism=MEC[target]["mechanism"], mechanism_id=target, family=MEC[target]["family"],
                           family_id=MEC[target]["family_id"], how=how, note="")
        rows.append(row)

    spread_areas = collections.defaultdict(set)
    for r in rows:
        if r["mechanism_id"]:
            spread_areas[r["mechanism_id"]].add(r["area"])
    area_families = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        area_families[r["area"]][r["family_id"] or ("outside" if r["outcome"] == "outside the tree" else "none")] += 1
    c = collections.Counter(r["outcome"] for r in rows)
    ws = collections.Counter()
    for r in rows:
        ws[r["outcome"]] += r["n"]
    reached = {r["mechanism_id"] for r in rows if r["mechanism_id"]}
    empty = [m["mechanism"] for m in TREE["mechanisms"] if m["mechanism_id"] not in reached]
    note = ("Bottom-up tree v48 (built %s, %d strategies of 45 countries, %d leaf objectives under 19 areas) read through the top-down tree v2. "
            "Outcomes: %s. Weighted by strategies: %s. %d of 99 mechanisms receive no leaf objective: %s." % (
                D["built"], len(D["strategies"]), len(rows), ", ".join("%s %d" % kv for kv in c.most_common()),
                ", ".join("%s %d" % kv for kv in ws.most_common()), len(empty), "; ".join(empty)))
    out = {"note": note, "rows": rows, "spread": {k: len(v) for k, v in spread_areas.items()}, "spread_areas": {k: sorted(v) for k, v in spread_areas.items()},
           "area_families": {k: dict(v) for k, v in area_families.items()}, "empty_mechanisms": empty}
    json.dump(out, open(os.path.join(HERE, "bottomup_test.json"), "w", encoding="utf-8"), ensure_ascii=False)
    with open(os.path.join(HERE, "bottomup_test.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "area", "label", "n", "outcome", "family_id", "family", "mechanism_id", "mechanism", "how", "note", "definition"])
        w.writeheader()
        w.writerows(rows)
    print(note)
    many = sorted(spread_areas.items(), key=lambda kv: -len(kv[1]))[:8]
    print("mechanisms spanning most areas:", "; ".join("%s %d" % (MEC[k]["mechanism"], len(v)) for k, v in many))


if __name__ == "__main__":
    main()
