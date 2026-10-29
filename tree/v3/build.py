"""Mother tree v3: the reviewer's framework (29 October 2026) laid over tree v2's pathways.

Reads inputs/reviewer_framework.json (the reviewer's PVII_Mother_Tree.html parsed into an
outline: subpillar > group > family > mechanism) and ../v2/tree_v2.json, and writes
groups_v3.csv, families_v3.csv, pathways_v3.csv, sdg_crosswalk.csv, risk_matrix.csv and
tree_v3.json.

Three placement levels under the RHDR subpillars:
  group (L1, 33): the reviewer's groups, each citing a published framework
  family (L2, 58): the reviewer's families, the required mapping level, with plan words
  pathway (L3, 264): the reviewer's mechanisms = v2's 259 pathways (ids kept) plus 5 new ones

The reviewer's structure is taken whole for the governance subpillars (Future-Ready
Governance Index and WDR 2017). Elsewhere the amendments below apply; each is a decision
recorded in the comparison doc (Reviewer framework vs tree v2, 29 October 2026).

Run: python3 build.py
"""
import collections
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(os.path.dirname(HERE), "v2", "tree_v2.json")
REVIEWER = os.path.join(HERE, "inputs", "reviewer_framework.json")

SUBPILLAR_CODE = {"Tackling Structural Exclusion": "TSE", "Enhancing Capabilities": "CAP",
                  "Future Generations": "FUT", "Export-led": "EXP", "Domestic Integration": "DOM",
                  "Growth through Inclusion": "GTI", "Anticipation and Strategic Foresight": "ANT",
                  "Adaptability and Course Correction": "ADA", "Agility and Delivery Capability": "AGI",
                  "Reform Leadership, Coalitions and Civic Engagement": "REF"}
GENERAL = {"General People": "H-SPE", "General Economy": "H-SEC", "General Governance": "H-SGO"}

# ---------------------------------------------------------------- amendments (the decisions)
# A family merged into a sibling: the thinnest People and Economy families (one or two pathways).
MERGE = {"Digital access and use": "Skills for work",
         "Displaced and uprooted populations": "Exclusion from social and political spaces",
         "Public balance sheet": "Subsoil wealth and resource rents"}
RENAME = {"Subsoil wealth and resource rents": "Public wealth: resource rents and the balance sheet",
          "Lagging places and displaced workers": "Displaced workers and local adjustment"}
REDEFINE = {"Public wealth: resource rents and the balance sheet":
            "Exhaustible resource rents and the public balance sheet: whether rents are reinvested and whether debt and fiscal policy shift burdens onto future taxpayers.",
            "Displaced workers and local adjustment":
            "Concentrated shocks to local labour markets from trade and technology, and how displaced workers and places adjust.",
            "Skills for work":
            "Job-relevant skills formed after or alongside schooling, the signals that make them pay, and households' access to and use of digital connectivity."}
# A family moved to another group (and subpillar where the group sits elsewhere).
MOVE_FAMILY = {"Living environment and basic services": "Decent standard of living",
               "Property rights and market rules": "Market rules and property rights"}
# Groups added, with the subpillar they sit under and their basis.
NEW_GROUPS = {"Market rules and property rights": ("Growth through Inclusion",
              "Inclusive Growth Analytics (Ianchovichina and Lundstrom 2009); WDR 2017 on contracts and competition",
              "Security of property, contract enforcement, competition and state ownership rules that decide who captures returns.")}
# A family split: these pathways leave their family for a new family under the group named.
SPLIT = {"Lagging regions and place-based development": {
    "group": "Linkages, clusters and cities", "from": "Lagging places and displaced workers",
    "definition": "Persistent spatial gaps between regions, and the place-based policies that try to close them.",
    "pathways": ["Place-based policy and spatial equilibrium", "Geographic poverty traps"]}}
# Pathways the reviewer added. Fields the reviewer did not give (text cues, risks) are set here
# and marked as assigned at the v3 build, not source-verified.
NEW_PATHWAYS = {
    "Extension of contributory social insurance to informal workers": {
        "text_cues": r"informal (workers?|sector|economy|employ).{0,60}(insurance|pension|social (security|protection))|(insurance|pension|social (security|protection)).{0,60}informal",
        "risks": ["Demographic Shifts"]},
    "Household digital access and effective use": {
        "text_cues": r"digital (access|inclusion|literacy|divide|skills for (all|citizens))|internet access|affordable (internet|connectivity|devices|broadband)|households?.{0,40}(internet|broadband|connectivity)",
        "risks": ["Technological Change"]},
    "Local labour-market adjustment to decarbonisation": {
        "text_cues": r"just transition|coal (phase|transition|closure|mine|region)|fossil[- ]fuel (workers|communities|regions|dependent)|decarboni[sz]ation.{0,40}(workers|jobs|communities|regions)",
        "risks": ["Climate Change", "Resource and Energy Pressures"]},
    "Interoperability and data sharing across agencies": {
        "text_cues": r"data (sharing|exchange|interoperab)|interoperab|shared (data|registr|database)|data governance|open data|integrated (database|data platform|information system)",
        "risks": ["Technological Change"]},
    "Crisis and emergency risk communication": {
        "text_cues": r"risk communication|crisis communication|emergency communication|public (warning|alert)|communicat.{0,40}(crisis|emergenc|disaster|outbreak)",
        "risks": ["Pandemics", "Climate Change"]},
}
# SDG targets for families whose pathways came from no single v2 lever (the one-pathway
# governance families); every other family rolls its targets up from the v2 mechanisms.
FAMILY_SDG = {"Scenario and futures work": ["16.6"], "Development planning": ["17.14", "16.6"],
              "Statistics and data sharing": ["17.18", "17.19", "16.6"], "Policy experimentation": ["16.6"],
              "Participatory decision-making": ["16.7"], "Delegated management autonomy": ["16.6"],
              "Crisis and risk communication": ["16.6", "13.3", "3.d"]}
NEW_PATHWAY_NOTE = "assigned at the v3 build from the reviewer's note; not source-verified"


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def chain(text):
    """'Works when X · How A → B · Result C' -> conditions, causal_input, transmission, outcome."""
    out = {"conditions": "", "causal_input": "", "transmission": "", "outcome": ""}
    for part in (text or "").split(" · "):
        part = part.strip()
        if part.startswith("Works when "):
            out["conditions"] = part[len("Works when "):]
        elif part.startswith("How "):
            a, _, b = part[len("How "):].partition(" → ")
            out["causal_input"], out["transmission"] = a, b
        elif part.startswith("Result "):
            out["outcome"] = part[len("Result "):]
    return out


def read_reviewer():
    """The outline as groups and families, each family with its pathway names in order."""
    out = json.load(open(REVIEWER, encoding="utf-8"))
    groups, families, sub = [], [], None
    grp = fam = None
    for kind, n in out:
        if kind == "l1":
            sub = n["name"]
        elif kind == "g2":
            grp = {"group": n["name"], "subpillar": sub, "basis": n.get("basis", ""),
                   "definition": n.get("def", ""), "why": n.get("rule", "")}
            groups.append(grp)
        elif kind == "l2":
            fam = {"family": n["name"], "group": grp["group"], "definition": n.get("def", ""),
                   "examples": n.get("ex", ""), "pathways": []}
            families.append(fam)
        elif kind == "l3" and fam is not None:
            fam["pathways"].append({"name": n["name"], "chain": n.get("chain", ""), "cite": n.get("cite", "")})
    return groups, families


def main():
    v2 = json.load(open(V2, encoding="utf-8"))
    v2_paths = {norm(p["pathway"]): p for p in v2["pathways"]}
    v2_mechs = {m["mechanism_id"]: m for m in v2["mechanisms"]}
    sub_by_name = {s["name"]: s for s in v2["subpillars"]}
    pillar_name = {p["code"]: p["name"] for p in v2["pillars"]}
    groups_in, families_in = read_reviewer()
    groups_in = [g for g in groups_in if g["subpillar"] not in GENERAL]      # General branches are holding nodes

    # ---- amendments on the reviewer's structure
    for name, (sub, basis, definition) in NEW_GROUPS.items():
        groups_in.append({"group": name, "subpillar": sub, "basis": basis, "definition": definition, "why": ""})
    fam_by_name = {f["family"]: f for f in families_in}
    for new, spec in SPLIT.items():
        src = fam_by_name[spec["from"]]
        moved = [p for p in src["pathways"] if p["name"] in spec["pathways"]]
        src["pathways"] = [p for p in src["pathways"] if p["name"] not in spec["pathways"]]
        families_in.append({"family": new, "group": spec["group"], "definition": spec["definition"],
                            "examples": "", "pathways": moved})
        fam_by_name[new] = families_in[-1]
    for src, dst in MERGE.items():
        fam_by_name[dst]["pathways"] += fam_by_name[src]["pathways"]
        families_in.remove(fam_by_name[src])
    for f in families_in:
        if f["family"] in MOVE_FAMILY:
            f["group"] = MOVE_FAMILY[f["family"]]
        if f["family"] in RENAME:
            f["family"] = RENAME[f["family"]]
        if f["family"] in REDEFINE:
            f["definition"] = REDEFINE[f["family"]]
    used = {f["group"] for f in families_in}
    groups_in = [g for g in groups_in if g["group"] in used]

    # ---- ids: groups in subpillar order, families in group order, pathways keep v2 ids
    sub_order = list(SUBPILLAR_CODE)
    groups_in.sort(key=lambda g: sub_order.index(g["subpillar"]))
    groups = {}
    for i, g in enumerate(groups_in, 1):
        code = SUBPILLAR_CODE[g["subpillar"]]
        gid = "G-%02d" % i
        groups[gid] = {"group_id": gid, "group": g["group"], "level": "L1",
                       "pillar": pillar_name[sub_by_name[g["subpillar"]]["pillar"]],
                       "pillar_code": sub_by_name[g["subpillar"]]["pillar"], "subpillar": g["subpillar"],
                       "subpillar_code": code, "basis": g["basis"], "definition": g["definition"],
                       "family_ids": [], "sdg_targets": [], "risks": [], "assets": [], "n_families": 0, "n_pathways": 0}
    gid_of = {g["group"]: gid for gid, g in groups.items()}
    families_in.sort(key=lambda f: list(groups).index(gid_of[f["group"]]))
    families, pathways = {}, {}
    next_new = 260
    for i, f in enumerate(families_in, 1):
        fid = "F-%02d" % i
        g = groups[gid_of[f["group"]]]
        fam = {"family_id": fid, "family": f["family"], "level": "L2", "group_id": g["group_id"],
               "group": g["group"], "pillar": g["pillar"], "subpillar": g["subpillar"],
               "subpillar_code": g["subpillar_code"], "definition": f["definition"],
               "examples": f["examples"].replace("Examples from plans ", ""), "plan_words": "",
               "pathway_ids": [], "v2_mechanisms": [], "sdg_targets": [], "assets": [], "risks": [],
               "conditional_risks": [], "n_pathways": 0}
        families[fid] = fam
        g["family_ids"].append(fid)
        for p in f["pathways"]:
            old = v2_paths.get(norm(p["name"]))
            if old:
                row = dict(old)
                row.update(family_id=fid, family=fam["family"], group_id=g["group_id"], group=g["group"],
                           subpillar=g["subpillar"], pillar=g["pillar"],
                           v2_mechanism_id=old["mechanism_id"], v2_mechanism=old["mechanism"],
                           v2_family_id=old["family_id"], v2_family=old["family"],
                           subpillar_changed=("from %s" % old["subpillar"]) if old["subpillar"] != g["subpillar"] else "")
                for k in ("mechanism_id", "mechanism"):
                    row.pop(k, None)
            else:
                spec = NEW_PATHWAYS[p["name"]]
                pid = "L3-%03d" % next_new
                next_new += 1
                row = dict(pathway_id=pid, pathway=p["name"], level="L3", family_id=fid, family=fam["family"],
                           group_id=g["group_id"], group=g["group"], subpillar=g["subpillar"], pillar=g["pillar"],
                           old_family_id="", old_family="", old_subpillar="", subpillar_changed="", merged_into="",
                           **chain(p["chain"]), distinction="", evidence=p["cite"],
                           risks=list(spec["risks"]), risk_justification=NEW_PATHWAY_NOTE, conditional_risks=[],
                           baseline="", evidence_status="cited by the reviewer, not yet independently verified",
                           risk_status=NEW_PATHWAY_NOTE, text_cues=spec["text_cues"],
                           v2_mechanism_id="", v2_mechanism="", v2_family_id="", v2_family="", added_in="v3")
            pathways[row["pathway_id"]] = row
            fam["pathway_ids"].append(row["pathway_id"])

    # ---- plan words, SDG targets and assets: from the v2 mechanisms whose pathways landed here
    for fam in families.values():
        own = [pathways[p] for p in fam["pathway_ids"]]
        share = collections.Counter(p["v2_mechanism_id"] for p in own if p.get("v2_mechanism_id"))
        words, sdg, assets = [], [], []
        for mid, n in share.most_common():
            m = v2_mechs[mid]
            total = len([p for p in m["pathway_ids"] if not v2_paths_by_id(v2)[p].get("merged_into")]) or len(m["pathway_ids"])
            if n * 2 >= total:                      # most of this lever's channels are here
                words.append(m["plan_words"])
                fam["v2_mechanisms"].append(mid)
                sdg += [t for t in m["sdg_targets"] if t not in sdg]
                assets += [a for a in m["assets"] if a not in assets]
        for p in own:                               # channels whose lever sits elsewhere, or new ones
            if p.get("v2_mechanism_id") not in fam["v2_mechanisms"] and p.get("text_cues"):
                words.append(p["text_cues"])
        fam["plan_words"] = "|".join(w for w in words if w)
        re.compile(fam["plan_words"], re.I)
        fam["sdg_targets"] = sdg or list(FAMILY_SDG.get(fam["family"], []))
        fam["assets"] = assets
        risks = collections.OrderedDict()
        for p in own:
            if p.get("merged_into"):
                continue
            for r in p.get("risks") or []:
                risks.setdefault(r, []).append(p["pathway_id"])
            for c in p.get("conditional_risks") or []:
                fam["conditional_risks"].append(dict(c, pathway_id=p["pathway_id"]) if isinstance(c, dict) else {"pathway_id": p["pathway_id"], "risk": c})
        fam["risks"] = list(risks)
        fam["risk_sources"] = {r: ps for r, ps in risks.items()}
        fam["n_pathways"] = len([p for p in own if not p.get("merged_into")])
    for g in groups.values():
        for fid in g["family_ids"]:
            f = families[fid]
            g["sdg_targets"] += [t for t in f["sdg_targets"] if t not in g["sdg_targets"]]
            g["risks"] += [r for r in f["risks"] if r not in g["risks"]]
            g["assets"] += [a for a in f["assets"] if a not in g["assets"]]
            g["n_pathways"] += f["n_pathways"]
        g["n_families"] = len(g["family_ids"])

    # ---- checks
    missing = [p["pathway"] for p in v2["pathways"] if p["pathway_id"] not in pathways]
    assert not missing, "v2 pathways not placed: %s" % missing
    assert len(pathways) == 264, len(pathways)
    assert all(f["plan_words"] for f in families.values()), [f["family"] for f in families.values() if not f["plan_words"]]
    assert all(f["sdg_targets"] for f in families.values()), [f["family"] for f in families.values() if not f["sdg_targets"]]
    # v2 merged seven pathways into siblings. Where the reviewer places the two under different
    # families they are distinct channels after all, so the merge is undone and said so.
    unmerged = []
    for p in pathways.values():
        dst = p.get("merged_into")
        if dst and pathways[dst]["family_id"] != p["family_id"]:
            p["merged_into"] = ""
            p["distinction"] = ("unmerged in v3: v2 merged it into %s, which the reviewer places under %s. "
                                % (dst, pathways[dst]["family"]) + (p.get("distinction") or "")).strip()
            unmerged.append(p["pathway_id"])
    merges = {p["pathway_id"]: p["merged_into"] for p in pathways.values() if p.get("merged_into")}

    for fam in families.values():
        fam["n_pathways"] = len([p for p in fam["pathway_ids"] if not pathways[p].get("merged_into")])
    for g in groups.values():
        g["n_pathways"] = sum(families[f]["n_pathways"] for f in g["family_ids"])

    # ---- defaults from v2 for re-mapping: v2 mechanism -> v3 family that holds most of its pathways
    mech_default = {}
    for mid, m in v2_mechs.items():
        c = collections.Counter(pathways[p]["family_id"] for p in m["pathway_ids"] if p in pathways)
        mech_default[mid] = c.most_common(1)[0][0] if c else ""
    fam_default = {}
    for f in v2["families"]:
        c = collections.Counter(families[mech_default[m]]["group_id"] for m in f["mechanism_ids"] if mech_default.get(m))
        fam_default[f["family_id"]] = c.most_common(1)[0][0] if c else ""

    # ---- write
    def write_csv(path, rows, columns):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
    write_csv(os.path.join(HERE, "groups_v3.csv"), groups.values(),
              ["group_id", "group", "level", "pillar", "subpillar", "subpillar_code", "basis", "definition",
               "n_families", "n_pathways", "family_ids", "sdg_targets", "risks", "assets"])
    write_csv(os.path.join(HERE, "families_v3.csv"), families.values(),
              ["family_id", "family", "level", "group_id", "group", "pillar", "subpillar", "subpillar_code", "definition",
               "examples", "plan_words", "n_pathways", "pathway_ids", "v2_mechanisms", "sdg_targets", "risks", "assets"])
    write_csv(os.path.join(HERE, "pathways_v3.csv"), pathways.values(),
              ["pathway_id", "pathway", "level", "family_id", "family", "group_id", "group", "subpillar", "pillar",
               "v2_mechanism_id", "v2_mechanism", "v2_family_id", "v2_family", "subpillar_changed", "merged_into",
               "causal_input", "transmission", "outcome", "conditions", "distinction", "evidence", "risks",
               "conditional_risks", "evidence_status", "risk_status", "text_cues", "added_in"])
    sdg_rows = [{"family_id": f["family_id"], "family": f["family"], "group": f["group"], "subpillar": f["subpillar"],
                 "sdg_target": t, "sdg_dimension": v2["sdg_dim"].get(t, "")}
                for f in families.values() for t in f["sdg_targets"]]
    write_csv(os.path.join(HERE, "sdg_crosswalk.csv"), sdg_rows,
              ["family_id", "family", "group", "subpillar", "sdg_target", "sdg_dimension"])
    risk_rows = [{"family_id": f["family_id"], "family": f["family"], "group": f["group"], "subpillar": f["subpillar"],
                  "risk": r, "pathways": ps, "conditional": any(c.get("risk") == r for c in f["conditional_risks"])}
                 for f in families.values() for r, ps in f["risk_sources"].items()]
    write_csv(os.path.join(HERE, "risk_matrix.csv"), risk_rows,
              ["family_id", "family", "group", "subpillar", "risk", "pathways", "conditional"])
    tree = {"meta": {"version": "v3", "built": "2026-10-29",
                     "levels": ["pillar", "subpillar", "L1 group", "L2 family", "L3 pathway", "L4 objective", "L5 strategy"],
                     "required_level": "L2",
                     "depth_rule": "Every strategy is placed on a family (L2), the required level; a group alone is not a placement. "
                                   "A pathway (L3) only when the strategy's wording names that causal channel (text_cues) and no sibling. "
                                   "A standing function of the state with no family goes to the subpillar's General branch.",
                     "source": "The reviewer's framework of 27 October 2026 (inputs/reviewer_framework.json) over tree v2's pathways; "
                               "amendments in build.py", "merges": merges},
            "pillars": v2["pillars"], "subpillars": v2["subpillars"],
            "holding": [{"id": "H-SPE", "name": "General People"}, {"id": "H-SEC", "name": "General Economy"},
                        {"id": "H-SGO", "name": "General Governance"}, {"id": "H-GOAL", "name": "Goals held outside the tree"}],
            "groups": list(groups.values()), "families": list(families.values()), "pathways": list(pathways.values()),
            "assets": v2["assets"], "risks": v2["risks"], "sdg_goals": v2["sdg_goals"], "sdg_dim": v2["sdg_dim"],
            "target_classes": v2["target_classes"], "instrument_classes": v2["instrument_classes"],
            "v2_mechanism_default": mech_default, "v2_family_default": fam_default}
    with open(os.path.join(HERE, "tree_v3.json"), "w", encoding="utf-8") as fh:
        json.dump(tree, fh, ensure_ascii=False, indent=1)
    by_sub = collections.Counter(g["subpillar_code"] for g in groups.values())
    print("v3: %d groups, %d families, %d pathways (%d merged, %d unmerged from v2, %d new); groups per subpillar %s" % (
        len(groups), len(families), len(pathways), len(merges), len(unmerged), 264 - 259, dict(by_sub)))
    thin = [(f["family"], f["n_pathways"]) for f in families.values() if f["n_pathways"] <= 1]
    print("one-pathway families:", thin)


_BY_ID = {}


def v2_paths_by_id(v2):
    if not _BY_ID:
        _BY_ID.update({p["pathway_id"]: p for p in v2["pathways"]})
    return _BY_ID


if __name__ == "__main__":
    main()
