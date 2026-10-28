"""Build mother tree v2 from structure_v2.py + mechanisms_v2.py and the v1 pathway file.

Run from this folder: python3 build.py

Reads  ../v1/mechanisms.csv (the 259 pathways: causal chain, evidence, risk tags, text cues),
       ../v1/families.csv (old family names), ../v1/conditional_risk_links.csv, ../v1/baseline_mechanisms.csv,
       ../inputs/targets.csv, ../inputs/instruments.csv, ../../workflow/vocab/sdg_target_dimensions.json
Writes families_v2.csv, mechanisms_v2.csv, pathways_v2.csv, the crosswalk tables (rhdr_clauses.csv,
       sdg_crosswalk.csv, risk_matrix.csv, asset_matrix.csv, target_classes.csv, instrument_classes.csv,
       old_family_default.csv) and tree_v2.json, the one file step M will read.

Fails if a pathway is missing or placed twice, a target or instrument label is unclassified, a merge
points outside the tree, or a plan-word pattern does not compile.
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import structure_v2 as S  # noqa: E402

V1 = os.path.join(HERE, "..", "v1")
INPUTS = os.path.join(HERE, "..", "inputs")
VOCAB = os.path.join(HERE, "..", "..", "workflow", "vocab", "sdg_target_dimensions.json")
RISKS = ["Climate Change", "Pandemics", "Biodiversity Loss", "Environmental Degradation and Pollution",
         "Resource and Energy Pressures", "Shifts in Globalisation", "Technological Change", "Demographic Shifts",
         "Democratic Backsliding", "Growing Populism", "Increased Polarisation"]
SDG_GOALS = ["No Poverty", "Zero Hunger", "Good Health and Well-Being", "Quality Education", "Gender Equality",
             "Clean Water and Sanitation", "Affordable and Clean Energy", "Decent Work and Economic Growth",
             "Industry, Innovation and Infrastructure", "Reduced Inequalities", "Sustainable Cities and Communities",
             "Responsible Consumption and Production", "Climate Action", "Life Below Water", "Life on Land",
             "Peace, Justice and Strong Institutions", "Partnerships for the Goals"]


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (" | ".join(v) if isinstance(v, list) else v) for k, v in r.items()})


def pid(n):
    return "L3-%03d" % n


def main():
    sub = {c: {"code": c, "pillar": p, "name": n, "definition": d} for c, p, n, d in S.SUBPILLARS}
    pillar = dict(S.PILLARS)
    sdg_dim = json.load(open(VOCAB, encoding="utf-8"))
    v1_mech = {r["mechanism_id"]: r for r in read_csv(os.path.join(V1, "mechanisms.csv"))}
    v1_fam = {r["family_id"]: r for r in read_csv(os.path.join(V1, "families.csv"))}
    cond = collections.defaultdict(list)
    for r in read_csv(os.path.join(V1, "conditional_risk_links.csv")):
        if r["decision"] in ("CONDITIONAL", "SUPPORTED_CONDITIONAL"):
            cond[r["mechanism_id"]].append({"risk": r["risk"], "trigger": r["trigger"], "applies_when": r["applies_when"]})
    baseline = {r["mechanism_id"] for r in read_csv(os.path.join(V1, "baseline_mechanisms.csv"))}

    fams = collections.OrderedDict()
    for fid, sp, name, meaning, lit, clause in S.FAMILIES:
        fams[fid] = {"family_id": fid, "family": name, "level": "L1", "pillar": pillar[sub[sp]["pillar"]],
                     "pillar_code": sub[sp]["pillar"], "subpillar": sub[sp]["name"], "subpillar_code": sp,
                     "meaning": meaning, "literature": lit, "rhdr_clause": clause,
                     "mechanism_ids": [], "sdg_targets": [], "risks": [], "assets": [], "old_families": []}

    mechs = collections.OrderedDict()
    for mid, fid, name, variable, words, sdg, assets, pws in S.MECHANISMS:
        re.compile(words, re.I)
        f = fams[fid]
        mechs[mid] = {"mechanism_id": mid, "mechanism": name, "level": "L2", "family_id": fid, "family": f["family"],
                      "pillar": f["pillar"], "subpillar": f["subpillar"], "subpillar_code": f["subpillar_code"],
                      "intermediate_variable": variable, "plan_words": words, "sdg_targets": list(sdg),
                      "assets": list(assets), "pathway_ids": [pid(p) for p in pws], "risks": [],
                      "conditional_risks": [], "risk_sources": {}}
        f["mechanism_ids"].append(mid)

    # pathways: every v1 mechanism exactly once
    seen = collections.Counter()
    paths = collections.OrderedDict()
    for mid, m in mechs.items():
        for p in m["pathway_ids"]:
            seen[p] += 1
            v = v1_mech[p]
            n = int(p[3:])
            merged = pid(S.MERGES[n]) if n in S.MERGES else ""
            old_sub = v["subpillar"]
            paths[p] = {"pathway_id": p, "pathway": v["mechanism"], "level": "L3", "mechanism_id": mid,
                        "mechanism": m["mechanism"], "family_id": m["family_id"], "family": m["family"],
                        "subpillar": m["subpillar"], "pillar": m["pillar"],
                        "old_family_id": v["family_id"], "old_family": v["family"], "old_subpillar": old_sub,
                        "subpillar_changed": "yes" if old_sub != m["subpillar"] else "",
                        "merged_into": merged,
                        "causal_input": v["causal_input"], "transmission": v["transmission"], "outcome": v["outcome"],
                        "conditions": v["conditions"], "distinction": v["distinction"], "evidence": v["evidence"],
                        "risks": [x.strip() for x in v["risks"].split("|") if x.strip()],
                        "risk_justification": v["risk_justification"],
                        "conditional_risks": cond.get(p, []), "baseline": "yes" if p in baseline else "",
                        "evidence_status": v["evidence_status"], "risk_status": v["risk_status"],
                        "text_cues": v["text_cues"]}
            if v["family_id"] not in fams[m["family_id"]]["old_families"]:
                fams[m["family_id"]]["old_families"].append(v["family_id"])
    missing = [pid(n) for n in range(1, 260) if seen[pid(n)] == 0]
    dup = [p for p, c in seen.items() if c > 1]
    if missing or dup or len(paths) != 259:
        sys.exit("pathway coverage broken: missing %s duplicated %s" % (missing, dup))
    for n, t in S.MERGES.items():
        if pid(t) not in paths or paths[pid(t)]["merged_into"]:
            sys.exit("merge %s -> %s points outside the tree or at a merged pathway" % (n, t))
        if paths[pid(n)]["mechanism_id"] != paths[pid(t)]["mechanism_id"]:
            sys.exit("merge %s -> %s crosses mechanisms" % (n, t))

    # roll-ups: risks (with the pathways that carry each), SDG, assets
    for p in paths.values():
        m = mechs[p["mechanism_id"]]
        for r in p["risks"]:
            m["risk_sources"].setdefault(r, []).append(p["pathway_id"])
        for c in p["conditional_risks"]:
            m["conditional_risks"].append({"risk": c["risk"], "pathway_id": p["pathway_id"], "trigger": c["trigger"]})
    for m in mechs.values():
        m["risks"] = [r for r in RISKS if r in m["risk_sources"]]
        m["n_pathways"] = len(m["pathway_ids"])
        m["sdg_primary_dimension"] = _profile(m["sdg_targets"], sdg_dim)
        f = fams[m["family_id"]]
        for t in m["sdg_targets"]:
            if t not in f["sdg_targets"]:
                f["sdg_targets"].append(t)
        for r in m["risks"]:
            if r not in f["risks"]:
                f["risks"].append(r)
        for a in m["assets"]:
            if a not in f["assets"]:
                f["assets"].append(a)
    for f in fams.values():
        f["risks"] = [r for r in RISKS if r in f["risks"]]
        f["n_mechanisms"] = len(f["mechanism_ids"])
        f["n_pathways"] = sum(mechs[m]["n_pathways"] for m in f["mechanism_ids"])
        f["sdg_primary_dimension"] = _profile(f["sdg_targets"], sdg_dim)
        f["old_families"] = sorted(set(f["old_families"]) | {k for k, v in S.OLD_FAMILY_DEFAULT.items() if v == f["family_id"]})

    # lookups
    targets = read_csv(os.path.join(INPUTS, "targets.csv"))
    tclass = {}
    for cls, ids in S.TARGET_CLASSES.items():
        for t in ids:
            tclass.setdefault(t, cls)
    unclassified = [t["target_id"] for t in targets if t["target_id"] not in tclass]
    if unclassified:
        sys.exit("targets without a class: %s" % unclassified)
    instruments = read_csv(os.path.join(INPUTS, "instruments.csv"))
    bad = [i["instrument_id"] for i in instruments if i["instrument_id"] not in S.INSTRUMENT_CLASSES]
    if bad:
        sys.exit("instruments without a class: %s" % bad)
    target_rows = [{"target_id": t["target_id"], "target_label": t["label"], "target_family": t["family"],
                    "target_class": tclass[t["target_id"]]} for t in targets]
    instr_rows = [{"instrument_id": i["instrument_id"], "instrument_label": i["label"], "instrument_family": i["family"],
                   "instrument_class": S.INSTRUMENT_CLASSES[i["instrument_id"]],
                   "class_note": S.INSTRUMENT_CLASS_NOTE[S.INSTRUMENT_CLASSES[i["instrument_id"]]]} for i in instruments]

    # ---------------------------------------------------------------- write
    fam_cols = ["family_id", "family", "level", "pillar", "subpillar", "subpillar_code", "meaning", "literature", "rhdr_clause",
                "n_mechanisms", "n_pathways", "mechanism_ids", "sdg_targets", "sdg_primary_dimension", "risks", "assets", "old_families"]
    write_csv(os.path.join(HERE, "families_v2.csv"), list(fams.values()), fam_cols)
    mech_rows = []
    for m in mechs.values():
        r = dict(m)
        r["conditional_risks"] = ["%s (%s): %s" % (c["risk"], c["pathway_id"], c["trigger"]) for c in m["conditional_risks"]]
        r["risk_sources"] = ["%s: %s" % (k, ", ".join(v)) for k, v in m["risk_sources"].items()]
        mech_rows.append(r)
    mech_cols = ["mechanism_id", "mechanism", "level", "family_id", "family", "pillar", "subpillar", "intermediate_variable",
                 "plan_words", "n_pathways", "pathway_ids", "sdg_targets", "sdg_primary_dimension", "risks", "risk_sources",
                 "conditional_risks", "assets"]
    write_csv(os.path.join(HERE, "mechanisms_v2.csv"), mech_rows, mech_cols)
    path_rows = []
    for p in paths.values():
        r = dict(p)
        r["conditional_risks"] = ["%s: %s" % (c["risk"], c["trigger"]) for c in p["conditional_risks"]]
        path_rows.append(r)
    path_cols = ["pathway_id", "pathway", "level", "mechanism_id", "mechanism", "family_id", "family", "subpillar", "pillar",
                 "old_family_id", "old_family", "old_subpillar", "subpillar_changed", "merged_into", "causal_input", "transmission",
                 "outcome", "conditions", "distinction", "evidence", "risks", "risk_justification", "conditional_risks", "baseline",
                 "evidence_status", "risk_status", "text_cues"]
    write_csv(os.path.join(HERE, "pathways_v2.csv"), path_rows, path_cols)

    # crosswalks
    write_csv(os.path.join(HERE, "rhdr_clauses.csv"),
              [{"family_id": f["family_id"], "family": f["family"], "pillar": f["pillar"], "subpillar": f["subpillar"],
                "rhdr_clause": f["rhdr_clause"], "subpillar_definition": sub[f["subpillar_code"]]["definition"]} for f in fams.values()],
              ["family_id", "family", "pillar", "subpillar", "rhdr_clause", "subpillar_definition"])
    sdg_rows = []
    for m in mechs.values():
        for t in m["sdg_targets"]:
            g = int(t.split(".")[0])
            sdg_rows.append({"mechanism_id": m["mechanism_id"], "mechanism": m["mechanism"], "family_id": m["family_id"],
                             "family": m["family"], "subpillar": m["subpillar"], "sdg_target": t, "sdg_goal": g,
                             "sdg_goal_name": SDG_GOALS[g - 1], "primary_dimension": sdg_dim.get(t, {}).get("primary_dimension", ""),
                             "secondary_dimensions": [d for d in sdg_dim.get(t, {}).get("secondary_dimensions", []) if d != "None"]})
    write_csv(os.path.join(HERE, "sdg_crosswalk.csv"), sdg_rows,
              ["mechanism_id", "mechanism", "family_id", "family", "subpillar", "sdg_target", "sdg_goal", "sdg_goal_name",
               "primary_dimension", "secondary_dimensions"])
    risk_rows = []
    for m in mechs.values():
        for r in RISKS:
            srcs = m["risk_sources"].get(r, [])
            conds = [c for c in m["conditional_risks"] if c["risk"] == r]
            if srcs or conds:
                risk_rows.append({"mechanism_id": m["mechanism_id"], "mechanism": m["mechanism"], "family_id": m["family_id"],
                                  "family": m["family"], "risk": r, "link": "tagged" if srcs else "conditional",
                                  "pathways": srcs or [c["pathway_id"] for c in conds],
                                  "trigger": " | ".join(c["trigger"] for c in conds)})
    write_csv(os.path.join(HERE, "risk_matrix.csv"), risk_rows,
              ["mechanism_id", "mechanism", "family_id", "family", "risk", "link", "pathways", "trigger"])
    asset_rows = []
    anames = {a: n for a, n, _ in S.ASSETS}
    for m in mechs.values():
        for a in m["assets"]:
            asset_rows.append({"asset_id": a, "asset": anames[a], "mechanism_id": m["mechanism_id"], "mechanism": m["mechanism"],
                               "family_id": m["family_id"], "family": m["family"]})
    write_csv(os.path.join(HERE, "asset_matrix.csv"), asset_rows, ["asset_id", "asset", "mechanism_id", "mechanism", "family_id", "family"])
    write_csv(os.path.join(HERE, "target_classes.csv"), target_rows, ["target_id", "target_label", "target_family", "target_class"])
    write_csv(os.path.join(HERE, "instrument_classes.csv"), instr_rows,
              ["instrument_id", "instrument_label", "instrument_family", "instrument_class", "class_note"])
    write_csv(os.path.join(HERE, "old_family_default.csv"),
              [{"old_family_id": k, "old_family": v1_fam[k]["family"], "family_id": v, "family": fams[v]["family"],
                "subpillar": fams[v]["subpillar"]} for k, v in S.OLD_FAMILY_DEFAULT.items()],
              ["old_family_id", "old_family", "family_id", "family", "subpillar"])

    tree = {"meta": {"version": "v2", "built": "2026-10-28",
                     "levels": ["pillar", "subpillar", "L1 family", "L2 mechanism", "L3 pathway", "L4 objective", "L5 strategy"],
                     "depth_rule": "A strategy sits at the deepest level its whole wording supports: the family when it names only the domain, the mechanism when it names the lever (plan_words), the pathway when it names the causal channel (text_cues) and no sibling. No invented specificity.",
                     "merges": {pid(k): pid(v) for k, v in S.MERGES.items()}},
            "pillars": [{"code": c, "name": n} for c, n in S.PILLARS],
            "subpillars": list(sub.values()),
            "holding": [{"id": h, "name": n} for h, n in S.HOLDING],
            "families": list(fams.values()), "mechanisms": list(mechs.values()), "pathways": list(paths.values()),
            "assets": [{"asset_id": a, "asset": n, "why": w} for a, n, w in S.ASSETS],
            "risks": RISKS, "sdg_goals": SDG_GOALS,
            "sdg_dim": {t: sdg_dim[t]["primary_dimension"] for t in sorted({t for m in mechs.values() for t in m["sdg_targets"]} & set(sdg_dim))},
            "target_classes": target_rows, "instrument_classes": instr_rows,
            "old_family_default": S.OLD_FAMILY_DEFAULT}
    with open(os.path.join(HERE, "tree_v2.json"), "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=1)

    print("families %d  mechanisms %d  pathways %d (merged %d)  sdg links %d  risk links %d  asset links %d" % (
        len(fams), len(mechs), len(paths), len(S.MERGES), len(sdg_rows), len(risk_rows), len(asset_rows)))
    changed = sum(1 for p in paths.values() if p["subpillar_changed"])
    print("pathways whose RHDR category changes: %d" % changed)
    cnt = collections.Counter(r for m in mechs.values() for r in m["risks"])
    print("mechanisms per risk:", dict(cnt))


def _profile(targets, sdg_dim):
    c = collections.Counter(sdg_dim.get(t, {}).get("primary_dimension", "") for t in targets)
    c.pop("", None)
    return ", ".join("%s %d" % (k, v) for k, v in c.most_common())


if __name__ == "__main__":
    main()
