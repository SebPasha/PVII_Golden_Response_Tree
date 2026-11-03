"""Mother tree v4: levers in place of pathways at the bottom level.

Reads ../v3/tree_v3.json (the reviewer's groups and families, the 263 live pathways with their
bridge face from ../v3/bridge.py) and writes groups_v4.csv, families_v4.csv, levers_v4.csv,
pathways_v4.csv and tree_v4.json.

Levels under the RHDR subpillars:
  group (L1, 33) and family (L2, 60): the reviewer's, unchanged from v3
  lever (L3): what a government does, the level every strategy that names an action reaches.
              Built from the bridge face of v3's pathways: one lever per pathway, except where
              LEVER_MERGES says several pathways are one action, in which case the lever carries
              them all as its literature.
  pathway (L4, literature): v3's 263 pathways, each under its lever, with the causal chain,
              conditions, distinction and evidence. An optional depth: recorded on a strategy
              only when the lever has one pathway or the strategy's wording names the channel.

The join is made on the lever by meaning, with its joins_when and joins_not tests; the text cues
of its pathways are kept as an advisory flag, never a veto. Decided 3 November 2026 (Sebastian:
"build the tree with levers instead of pathways, and replace that part of the tree").

Run: python3 build.py
"""
import collections
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.join(os.path.dirname(HERE), "v3", "tree_v3.json")
BUILT = "2026-11-03"

# ---------------------------------------------------------------- the decisions
# Pathways that are one action for a government, merged into one lever. Key: the pathway whose
# bridge face leads; "also": the pathways that join it as literature; "lever": the lever's name;
# "joins_when": the test for the merged lever (the pathways' joins_not lines are kept on the
# pathway rows, since the siblings they point to may now be one lever).
LEVER_MERGES = {
    "L3-021": {"also": ["L3-022", "L3-023"], "lever": "Insurance and income replacement in shocks",
               "joins_when": "it pays out, insures or transfers when income falls, whether to hold consumption, stop distress sales or let households take productive risks"},
    "L3-053": {"also": ["L3-055"], "lever": "Food access and food price measures",
               "joins_when": "it secures households' access to food through income support, consumer prices, distribution or price stabilisation"},
    "L3-069": {"also": ["L3-070"], "lever": "Clean technology support and deployment",
               "joins_when": "it supports developing, adopting or deploying clean and low-carbon technology, from research incentives to building capacity at scale"},
    "L3-080": {"also": ["L3-084"], "lever": "Pollution standards, permits, levies and toxic substance control",
               "joins_when": "it regulates or prices pollution or controls hazardous substances: standards, permits, levies, chemical and pesticide rules"},
    "L3-091": {"also": ["L3-094"], "lever": "Resource revenue funds and stabilisation rules",
               "joins_when": "it saves, invests or smooths resource revenues: sovereign or stabilisation funds, counter-cyclical rules for commodity income"},
    "L3-095": {"also": ["L3-096"], "lever": "Debt management and fiscal sustainability",
               "joins_when": "it manages public debt or the fiscal balance to keep debt sustainable or to lift its drag on investment"},
    "L3-100": {"also": ["L3-101"], "lever": "Family planning, reproductive health and fertility policy",
               "joins_when": "it provides family planning or reproductive health, or aims to change fertility or investment per child"},
    "L3-118": {"also": ["L3-119"], "lever": "Trade agreements, blocs and preferences",
               "joins_when": "it negotiates, joins, uses or defends trade agreements, regional integration or tariff preferences"},
    "L3-110": {"also": ["L3-111"], "lever": "Diversification into higher-value products and sectors",
               "joins_when": "it moves the economy into new, related or higher-productivity products and sectors"},
    "L3-128": {"also": ["L3-133"], "lever": "R&D funding, public and private",
               "joins_when": "it raises R&D investment or funds research in public institutions"},
    "L3-129": {"also": ["L3-130"], "lever": "Technology adoption and absorptive capacity of firms",
               "joins_when": "it helps firms adopt existing technology or builds their capability to use it"},
    "L3-121": {"also": ["L3-123"], "lever": "Investment attraction, promotion and facilitation",
               "joins_when": "it attracts, promotes, facilitates or deregulates foreign and private investment"},
    "L3-135": {"also": ["L3-137"], "lever": "National road, rail and inland transport networks",
               "joins_when": "it builds or upgrades transport between domestic markets and regions, including links from peripheral regions to centres"},
    "L3-147": {"also": ["L3-148"], "lever": "Utility tariffs, subsidies and cost recovery",
               "joins_when": "it reforms utility tariffs, fee collection, subsidies or price structures for energy, water or waste services"},
    "L3-151": {"also": ["L3-154"], "lever": "Supply-chain linkages, local processing and local content",
               "joins_when": "it builds links between stages of a chain: processing, supplier development, local procurement, local content around primary industries"},
    "L3-145": {"also": ["L3-142"], "lever": "Urban planning and serviced expansion",
               "joins_when": "it plans and services urban land, whole city plans, or acts to make cities more productive through density and scale"},
    "L3-185": {"also": ["L3-186"], "lever": "Place-based support for lagging regions",
               "joins_when": "it directs investment, incentives or zones to a lagging region or province, or acts on the conditions that keep it poor"},
    "L3-176": {"also": ["L3-177"], "lever": "Employment services and active labour-market programmes",
               "joins_when": "it matches workers to jobs or runs programmes for job seekers: employment services, job portals, job-search assistance, wage subsidies, training for the unemployed"},
    "L3-190": {"also": ["L3-191"], "lever": "Skilled emigration, return and retention",
               "joins_when": "it addresses emigration of skilled people, their retention, or their return and reintegration"},
    "L3-169": {"also": ["L3-166"], "lever": "Competition law and removal of firm-specific distortions",
               "joins_when": "it strengthens competition or removes rules and subsidies that favour some firms over more productive ones"},
    "L3-194": {"also": ["L3-195"], "lever": "Tenure security and land titling",
               "joins_when": "it secures rights to land or issues and registers titles: community titles, tenure recognition, titling programmes"},
    "L3-202": {"also": ["L3-199", "L3-203"], "lever": "Reducing concentration and dependence in trade and supply",
               "joins_when": "it reduces dependence on few suppliers, commodities, markets or chokepoints: energy security, supply-chain resilience, export diversification"},
    "L3-198": {"also": ["L3-200", "L3-201"], "lever": "Macro-financial buffers: reserves, debt composition, bank supervision",
               "joins_when": "it builds reserves, manages the exchange rate, limits foreign-currency or short-term debt, or supervises banks for stability"},
    "L3-204": {"also": ["L3-205"], "lever": "Strategic capacity and stocks of critical goods",
               "joins_when": "it builds domestic production or physical reserves of critical goods: food, fuel, medicines, vaccines"},
    "L3-218": {"also": ["L3-228"], "lever": "Iterative, problem-driven reform methods",
               "joins_when": "it adopts an iterative or experimental way of working inside government, or sequences reform to what the administration can do"},
    "L3-229": {"also": ["L3-230"], "lever": "Decentralisation and local accountability",
               "joins_when": "it devolves functions, decisions or revenue powers to local government, or guards local spending against capture"},
    "L3-240": {"also": ["L3-241"], "lever": "Regulatory and enforcement capacity",
               "joins_when": "it builds or empowers a regulator, or monitors and enforces compliance with existing rules"},
    "L3-233": {"also": ["L3-234"], "lever": "Tax reform: rates, bases, equity and the fiscal contract",
               "joins_when": "it reforms the tax system's rates, bases or fairness, or links taxes visibly to services"},
    "L3-253": {"also": ["L3-254"], "lever": "Electoral competition and integrity",
               "joins_when": "it strengthens electoral competition, voters' information, or the running and safeguarding of elections"},
    "L3-213": {"also": ["L3-216"], "lever": "Judicial independence and safeguards of checks and balances",
               "joins_when": "it strengthens courts' independence or review of government, or protects checks and balances from executive capture"},
    "L3-012": {"also": ["L3-017"], "lever": "Reducing polarisation between groups and parties",
               "joins_when": "it names polarisation between social groups or political sides and acts to lower it"},
}


def short_name(lever_text):
    """A lever's short name from its bridge text: the first clause, at most 72 characters."""
    s = re.split(r"[;:]", lever_text, maxsplit=1)[0].strip()
    if len(s) > 72:
        head = s[:72]
        cuts = [head.rfind(sep) for sep in (" in ", " for ", " that ", " so ", " to ", " with ", " across ",
                                             " on ", " from ", " at ", " of ", ", ")]
        at = max(c for c in cuts if c > 30) if any(c > 30 for c in cuts) else head.rfind(" ")
        s = head[:at].rstrip(",")
    return s[:1].upper() + s[1:]


def main():
    v3 = json.load(open(V3, encoding="utf-8"))
    groups = {g["group_id"]: dict(g) for g in v3["groups"]}
    families = {f["family_id"]: dict(f) for f in v3["families"]}
    paths = {p["pathway_id"]: dict(p) for p in v3["pathways"] if not p.get("merged_into")}
    merged_away = {p["pathway_id"]: p["merged_into"] for p in v3["pathways"] if p.get("merged_into")}

    # every merged-in pathway must exist and sit in the lead's family
    lead_of = {}
    for lead, spec in LEVER_MERGES.items():
        assert lead in paths, lead
        for pid in spec["also"]:
            assert pid in paths, pid
            assert paths[pid]["family_id"] == paths[lead]["family_id"], (lead, pid)
            lead_of[pid] = lead

    levers = {}
    n = 0
    for fid, fam in families.items():
        fam["lever_ids"] = []
        for pid in fam["pathway_ids"]:
            if pid not in paths or pid in lead_of:
                continue
            p = paths[pid]
            n += 1
            lid = "LV-%03d" % n
            spec = LEVER_MERGES.get(pid, {})
            members = [pid] + list(spec.get("also", []))
            cues = [paths[m].get("text_cues", "") for m in members if paths[m].get("text_cues")]
            risks = []
            for m in members:
                for r in paths[m].get("risks") or []:
                    if r not in risks:
                        risks.append(r)
            entry = []
            for m in members:
                for e in paths[m].get("entry_points") or []:
                    if e not in entry:
                        entry.append(e)
            lever = {"lever_id": lid, "level": "L3",
                     "lever": spec.get("lever") or short_name(p["lever"]),
                     "lever_full": p["lever"] if not spec else "; ".join(paths[m]["lever"] for m in members),
                     "family_id": fid, "family": fam["family"], "group_id": fam["group_id"], "group": fam["group"],
                     "subpillar": fam["subpillar"], "subpillar_code": fam["subpillar_code"], "pillar": fam["pillar"],
                     "joins_when": spec.get("joins_when") or p["joins_when"],
                     "joins_not": p["joins_not"] if not spec else "; ".join(
                         "%s (%s)" % (paths[m]["joins_not"], m) for m in members),
                     "pathway_ids": members, "n_pathways": len(members),
                     "pathways": "; ".join("%s %s" % (m, paths[m]["pathway"]) for m in members),
                     "text_cues": "|".join(cues), "risks": risks, "entry_points": entry[:8],
                     "evidence": "; ".join("%s: %s" % (paths[m]["pathway"], paths[m].get("evidence", "")) for m in members)}
            levers[lid] = lever
            fam["lever_ids"].append(lid)
            for m in members:
                paths[m]["lever_id"] = lid
                paths[m]["lever"] = lever["lever"]
        fam["n_levers"] = len(fam["lever_ids"])
    for g in groups.values():
        g["n_levers"] = sum(families[f]["n_levers"] for f in g["family_ids"])

    # ---- write
    def write_csv(path, rows, columns):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                            for k, v in r.items()})
    write_csv(os.path.join(HERE, "groups_v4.csv"), groups.values(),
              ["group_id", "group", "level", "pillar", "subpillar", "subpillar_code", "basis", "definition",
               "n_families", "n_levers", "family_ids", "sdg_targets", "risks"])
    write_csv(os.path.join(HERE, "families_v4.csv"), families.values(),
              ["family_id", "family", "level", "group_id", "group", "pillar", "subpillar", "subpillar_code",
               "definition", "examples", "plan_words", "n_levers", "lever_ids", "n_pathways", "pathway_ids",
               "sdg_targets", "risks"])
    write_csv(os.path.join(HERE, "levers_v4.csv"), levers.values(),
              ["lever_id", "lever", "level", "family_id", "family", "group_id", "group", "subpillar", "pillar",
               "lever_full", "joins_when", "joins_not", "n_pathways", "pathway_ids", "pathways", "evidence",
               "risks", "entry_points", "text_cues"])
    write_csv(os.path.join(HERE, "pathways_v4.csv"), paths.values(),
              ["pathway_id", "pathway", "lever_id", "lever", "family_id", "family", "group_id", "group",
               "subpillar", "pillar", "causal_input", "transmission", "outcome", "conditions", "distinction",
               "evidence", "evidence_status", "risks", "conditional_risks", "text_cues", "joins_when",
               "joins_not", "v2_mechanism_id", "v2_mechanism", "added_in", "revised"])
    tree = {"meta": {"version": "v4", "built": BUILT,
                     "levels": ["pillar", "subpillar", "L1 group", "L2 family", "L3 lever",
                                "L4 pathway (literature; optional depth)", "objective", "strategy"],
                     "required_level": "L2", "placement_level": "L3",
                     "depth_rule": "Every strategy that names an action is placed on a lever (L3), judged by meaning "
                                   "with the lever's joins_when and joins_not tests; a summary line with no action "
                                   "stays on its family (L2); a group alone is not a placement. A pathway (L4) is "
                                   "recorded only when the lever has one pathway or the strategy's wording names the "
                                   "channel. The pathways' text cues are an advisory flag, never a veto.",
                     "source": "tree v3 (the reviewer's framework over v2's pathways, deep check of 30 October) with "
                               "the bridge face of 3 November; LEVER_MERGES in build.py", "merged_pathways": merged_away},
            "pillars": v3["pillars"], "subpillars": v3["subpillars"], "holding": v3["holding"],
            "groups": list(groups.values()), "families": list(families.values()),
            "levers": list(levers.values()), "pathways": list(paths.values()),
            "assets": v3["assets"], "risks": v3["risks"], "sdg_goals": v3["sdg_goals"], "sdg_dim": v3["sdg_dim"],
            "target_classes": v3["target_classes"], "instrument_classes": v3["instrument_classes"]}
    with open(os.path.join(HERE, "tree_v4.json"), "w", encoding="utf-8") as fh:
        json.dump(tree, fh, ensure_ascii=False, indent=1)
    per_fam = collections.Counter(len(f["lever_ids"]) for f in families.values())
    print("v4: %d groups, %d families, %d levers over %d pathways (%d levers carry more than one); levers per family %s" % (
        len(groups), len(families), len(levers), len(paths), sum(1 for l in levers.values() if l["n_pathways"] > 1),
        dict(sorted(per_fam.items()))))


if __name__ == "__main__":
    main()
