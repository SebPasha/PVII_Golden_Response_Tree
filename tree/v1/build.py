"""Build PV II mother tree v1 from the literature layer and the objective placement.

Inputs (read-only): ../inputs/objectives.csv, ../inputs/strategy_decomposition.csv,
  ../inputs/union_strategies.csv (PV2 data/union/strategies.csv as of 3 October 2026)
Outputs (this folder): families.csv, mechanisms.csv, objectives_v1.csv, strategy_nodes.csv, causal_network.csv,
  country_node_matrix.csv, admission_tests.csv, empty_nodes.csv, tree_v1.json, VALIDATION.md
"""
import csv, json, re, sys, os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lit_families import FAMILIES, HOLDING, SUBPILLARS, SUB, PILLARS, RISKS
from lit_mechanisms import MECH

GT = os.path.join(os.path.dirname(HERE), "inputs")      # tree/inputs (was support/golden_tree)
OBJ = os.path.join(GT, "objectives.csv")
DEC = os.path.join(GT, "strategy_decomposition.csv")
STR = os.path.join(GT, "union_strategies.csv")          # was PV2 data/union/strategies.csv
for p in (OBJ, DEC, STR):
    assert os.path.exists(p), p

def w(name, rows, cols):
    with open(os.path.join(HERE, name), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow(r)

# ---------------------------------------------------------------- L2 and L3 ids
SUB_ORDER = [c for c, *_ in SUBPILLARS]
fams = sorted(FAMILIES, key=lambda f: SUB_ORDER.index(f["sub"]))
# Stable ids: frozen in ids.json so review registers keep pointing at the same node. New nodes get the next free id;
# a removed node's id is retired, never reused.
IDS_PATH = os.path.join(HERE, "ids.json")
IDS = json.load(open(IDS_PATH)) if os.path.exists(IDS_PATH) else {"families": {}, "mechanisms": {}}
def next_id(table, prefix, width):
    used = [int(v.split("-")[1]) for v in IDS[table].values()] + IDS.get("retired_" + table, [])
    return f"{prefix}-{(max(used) if used else 0) + 1:0{width}d}"
FAM = {}
for f in fams:
    if f["id"] not in IDS["families"]:
        IDS["families"][f["id"]] = next_id("families", "L2", 2)
    f["fid"] = IDS["families"][f["id"]]
    FAM[f["id"]] = f
name_of = {f["id"]: f["name"] for f in fams}
def clean_excl(s):  # exclusion text: names only
    return re.sub(r"\(F\d+[A-Z]? ", "(", s)

MECHS, MK = [], {}
n = 0
for f in fams:
    ms = MECH.get(f["id"], [])
    assert ms, f"family without mechanisms {f['id']}"
    for m in ms:
        m = dict(m)
        k = f"{f['id']}.{m['key']}"
        if k not in IDS["mechanisms"]:
            IDS["mechanisms"][k] = next_id("mechanisms", "L3", 3)
        m["mid"] = IDS["mechanisms"][k]
        m["fam"] = f["id"]
        m["fid"] = f["fid"]
        m["sub"] = f["sub"]
        m["re"] = re.compile(r"\b(?:" + m["cues"] + ")", re.I) if m["cues"] else None  # cues anchored at a word start
        key = f"{f['id']}.{m['key']}"
        assert key not in MK, key
        MK[key] = m
        MECHS.append(m)
for table, live in (("families", {f["id"] for f in fams}), ("mechanisms", set(MK))):
    for k in [k for k in IDS[table] if k not in live]:
        IDS.setdefault("retired_" + table, []).append(int(IDS[table].pop(k).split("-")[1]))
json.dump(IDS, open(IDS_PATH, "w"), indent=1, sort_keys=True)
HOLD = {h[0]: dict(hid=h[0], sub=h[1], name=h[2], definition=h[3]) for h in HOLDING}

# ---------------------------------------------------------------- source verification status
CRL = list(csv.DictReader(open(os.path.join(HERE, "conditional_risk_links.csv"))))
BASE = {r["mechanism_id"] for r in csv.DictReader(open(os.path.join(HERE, "baseline_mechanisms.csv")))}
VER = {}
vdir = os.path.join(HERE, "verification")
for fn in sorted(os.listdir(vdir)):
    if fn.startswith("conditions_verified") and fn.endswith(".csv"):
        for r in csv.DictReader(open(os.path.join(vdir, fn))):
            if r["decision"].startswith("REVISE_AND_ACCEPT") or r["decision"].startswith("ACCEPT"):
                VER[r["mechanism_id"]] = f"source-verified: condition and citations ({fn[:-4].split('_')[-1]})"
for m in MECHS:
    m["evidence_status"] = VER.get(m["mid"], "cited, not yet independently verified")
    crl = [c for c in CRL if c["mechanism_id"] == m["mid"]]
    if m["mid"] in BASE:
        m["risk_status"] = "baseline: no macro-risk derivation, by design"
    elif m["risks"]:
        m["risk_status"] = "tagged from the review notes; tag not yet source-verified"
    else:
        m["risk_status"] = "untagged"
    m["conditional_risks"] = " | ".join(f"{c['risk']} ({c['decision'].lower()}): {c['applies_when']}" for c in crl if c["decision"] != "REJECT")
    m["rejected_risks"] = " | ".join(f"{c['risk']}: {c['finding']}" for c in crl if c["decision"] == "REJECT")
    m["crl"] = [(c["risk"], re.compile(r"\b(?:" + c["trigger"] + ")", re.I)) for c in crl if c["decision"] != "REJECT" and c["trigger"]]

# ---------------------------------------------------------------- admission tests
VERBS = ("promote", "expand", "improve", "strengthen", "develop", "build", "increase", "reduce", "support", "enhance")
tests = []
for m in MECHS:
    f = FAM[m["fam"]]
    sibs = [x for x in MECHS if x["fam"] == m["fam"] and x is not m]
    q1 = not m["name"].lower().startswith(VERBS)
    q2 = all(m[k].strip() for k in ("input", "transmission", "outcome"))
    q3 = bool(re.search(r"\b(1[89]\d\d|20\d\d)\b", m["evidence"]))
    q4 = m["distinction"].startswith("vs ") or not sibs
    q5 = bool(f["definition"]) and not f["name"].lower().startswith(VERBS)
    tests.append(dict(mechanism_id=m["mid"], mechanism=m["name"], family=f["name"],
                      q1_causal_not_action=q1, q2_input_transmission_outcome=q2,
                      q3_citation_present=q3, q4_distinct_from_sibling=q4, q5_family_shared_process=q5,
                      passes_all=all((q1, q2, q3, q4, q5)), evidence_status=m["evidence_status"]))
assert all(t["passes_all"] for t in tests), [t for t in tests if not t["passes_all"]]

# ---------------------------------------------------------------- objectives and placement
objs = {r["objective_id"][1:]: r for r in csv.DictReader(open(OBJ))}
place = {}
for line in open(os.path.join(HERE, "placement.txt")):
    line = line.split("#")[0].rstrip() if line.startswith("#") else line.rstrip()
    if not line.strip():
        continue
    head, _, note = line.partition(";")
    parts = head.split()
    oid, node = parts[0], parts[1]
    bau = "BAU" in parts[2:]
    assert oid not in place, f"duplicate {oid}"
    place[oid] = dict(node=node, bau=bau, note=note.strip())
missing = set(objs) - set(place)
extra = set(place) - set(objs)
assert not missing and not extra, (missing, extra)

MERGES = {
    "M01": dict(label="Strengthen sector governance and regulation", node="F51R.reg_capacity",
                definition="Reforming the governance, regulation, planning and institutions of a sector (agriculture, energy, forests, water, tourism, culture, transport). Sector is a tag. Excludes regulation of digital technology, which sits under Regulatory updating for technological change.",
                why="Same mechanism (sector regulatory capacity) in different sectors; sector kept as a tag."),
    "M02": dict(label="Digitise public services", node="F48.digital_deliv",
                definition="Moving government, education, health, sector and transport services and records onto digital systems. Excludes connectivity and digital public infrastructure as such.",
                why="Same mechanism (service delivery cost and reach through digital systems)."),
}
merge_members = defaultdict(list)
for oid, p in place.items():
    if p["node"] in MERGES:
        merge_members[p["node"]].append(oid)

def text_of(o):
    return " ".join([o["label"], o["aliases"].replace("|", ";"), o["definition"]])

def node_parts(node):
    """Return (level, family_key, mech_key_or_None, holding_or_None)."""
    if node.startswith("H-GOAL"):
        fam = node.split(">")[1] if ">" in node else None
        return ("GOAL", fam, None, "H-GOAL")
    if node.startswith("H-"):
        return ("STD", None, None, node)
    if "." in node:
        fk, mk = node.split(".", 1)
        assert node in MK, node
        return ("L3", fk, node, None)
    assert node in FAM, node
    return ("L2", node, None, None)

L4 = []
for oid in sorted(objs):
    o, p = objs[oid], place[oid]
    if p["node"] in MERGES:
        continue
    L4.append(dict(oid=f"O{oid}", label=o["label"], definition=o["definition"], aliases=o["aliases"],
                   node=p["node"], bau=p["bau"], note=p["note"], members=[f"O{oid}"],
                   n_strategies=int(o["n_strategies"]), family_src=o["family"], text=text_of(o),
                   merge_history=""))
for mid, mm in MERGES.items():
    mem = sorted(merge_members[mid])
    L4.append(dict(oid=mid, label=mm["label"], definition=mm["definition"], aliases=" | ".join(objs[x]["label"] for x in mem),
                   node=mm["node"], bau=False, note=mm["why"], members=[f"O{x}" for x in mem],
                   n_strategies=sum(int(objs[x]["n_strategies"]) for x in mem),
                   family_src=" | ".join(sorted({objs[x]["family"] for x in mem})),
                   text=" ".join(text_of(objs[x]) for x in mem),
                   merge_history="merged " + ", ".join(f"O{x} {objs[x]['label']}" for x in mem) + f". {mm['why']}"))
member_to_l4 = {}
for r in L4:
    for mem in r["members"]:
        member_to_l4[mem] = r["oid"]

def fam_mechs(fk):
    return [m for m in MECHS if m["fam"] == fk]

def cue_hit(m, text):
    if not m["re"]:
        return None
    x = m["re"].search(text)
    return x.group(0) if x else None

for r in L4:
    lvl, fk, mk, hk = node_parts(r["node"])
    r["level"] = lvl
    r["family_key"] = fk
    r["mech_key"] = mk
    r["holding"] = hk
    if lvl == "L3":
        m = MK[mk]
        hit = cue_hit(m, r["label"] + " " + r["aliases"].replace("|", ";"))
        r["basis"] = "plan wording" if hit else "convention"
        r["confidence"] = "high" if hit else "medium"
        r["depth_reason"] = (f"The objective's wording names the channel ('{hit}'); no sibling mechanism in the family carries it."
                             if hit else f"Option C convention: {m['name']} is the channel the objective's definition describes, and no sibling fits it.")
        r["candidates"] = ""
    elif lvl == "L2":
        ms = fam_mechs(fk)
        hits = [m for m in ms if cue_hit(m, r["text"])]
        cands = hits if len(hits) >= 2 else ms
        r["basis"] = "plan wording"
        r["confidence"] = "high"
        r["depth_reason"] = ("The plan commits to the family's process without naming a channel; "
                             f"its wording is consistent with {len(cands)} mechanisms.")
        r["candidates"] = " | ".join(f"{m['mid']} {m['name']}" for m in cands)
    elif lvl == "GOAL":
        r["basis"] = "triage"
        r["confidence"] = "low"
        r["depth_reason"] = ("Goal-shaped: an outcome, not a change sought. Held outside the tree; each strategy is re-read "
                             f"and re-homed where its wording names a channel. Nearest family: {name_of.get(fk, '')}.")
        r["candidates"] = ""
    else:
        r["basis"] = "convention"
        r["confidence"] = "high"
        r["depth_reason"] = "No mechanism in the risk literature; routine function filed in the Standard holding branch, dropped from reporting."
        r["candidates"] = ""
    if r["note"]:
        r["depth_reason"] += f" Note: {r['note']}."
    if fk:
        r["sub"] = FAM[fk]["sub"]
    else:
        r["sub"] = HOLD[hk]["sub"] or ""

# sibling test (Rule 2): an L3 objective whose own text also matches a sibling mechanism must be adjudicated
KEEP = json.load(open(os.path.join(HERE, "adjudicated_keep.json")))
unadjudicated = []
for r in L4:
    if r["level"] != "L3" or r["oid"].startswith("M"):
        continue
    o = objs[r["oid"][1:]]
    txt = o["label"] + " | " + o["aliases"] + " | " + re.split(r"\bExcludes\b", o["definition"])[0]
    sib = [m["name"] for m in fam_mechs(r["family_key"]) if f"{m['fam']}.{m['key']}" != r["mech_key"] and cue_hit(m, txt)]
    r["sibling_check"] = "challenged, kept: " + KEEP[r["oid"][1:]] if sib and r["oid"][1:] in KEEP else ("passed" if not sib else "")
    if sib and r["oid"][1:] not in KEEP:
        unadjudicated.append((r["oid"], r["label"], sib))
assert not unadjudicated, unadjudicated

# secondary RHDR at objective level, only where the definition names an excluded group
EXCL = re.compile(r"\b(women|girls|disab|minorit|indigenous|youth|rural (households|communities)|marginali|vulnerable|poor)\w*", re.I)
for r in L4:
    sec = []
    if r["sub"] and r["sub"] != "TSE":
        hit = EXCL.search(r["definition"] + " " + r["note"])
        if hit:
            sec.append(f"TSE: definition targets an excluded group ('{hit.group(0)}')")
    r["secondary_rhdr"] = " | ".join(sec)

# ---------------------------------------------------------------- strategies
dec = list(csv.DictReader(open(DEC)))
sinfo = {r["strategy_key"]: r for r in csv.DictReader(open(STR))}
# Cue matches too generic to move a goal across families (they name a sector, not a channel)
GENERIC = {"education", "livelihood", "livelihoods", "management", "consumption", "restructur", "regulat", "credit", "loan",
           "access", "coverage", "research", "planning", "digiti", "saving", "transfer", "grant", "return", "efficien",
           "standard", "label", "input", "seed", "pest", "disease", "competition", "monitoring", "evaluation", "budget",
           "waste", "association", "volunteer", "recover", "relief", "election", "coordinat", "pilot", "registration",
           "competit", "accountab", "polic", "lending", "financ", "secur", "storage", "participat", "community development",
           "infrastructure development", "industrial polic", "awareness", "campaign", "processing", "supplier", "value chain",
           "supply chain", "linkage", "rehabilit", "restor", "loss", "tariff", "pricing", "subsid", "generat", "grid"}
SPLIT = {"O0221": (re.compile(r"secur|self-?suffic|import (dependen|substitut)|strategic|essential", re.I), "F39.input_conc")}
OLDMAP = {"Enhancing Capabilities in Education, Skills, Digital, Health": "CAP", "Human Security": "CAP",
          "Strategic Planning (Anticipation)": "ANT", "Growth through Inclusion": "GTI",
          "Tackling Structural Exclusion": "TSE", "Political Will": "REF", "Collaborative Leadership": "REF",
          "Civic Engagement": "REF", "Export-led": "EXP", "Domestic Integration": "DOM",
          "Efficient Action (Agility)": "AGI", "Future Generations": "FUT", "Changing Plans (Adaptability)": "ADA"}
L4BY = {r["oid"]: r for r in L4}
srows = []
for d in dec:
    oid = d["objective_id"]
    l4 = L4BY[member_to_l4[oid]]
    s = sinfo.get(d["strategy_key"], {})
    ev = " ; ".join(x for x in (d["strategy"], d["objective_phrase"], d["target_phrase"], d["instrument_phrase"]) if x)
    node, level, basis, evid, status = l4["node"], l4["level"], "inherited from objective", "", "placed"
    fam_key = l4["family_key"]
    if oid in SPLIT and SPLIT[oid][0].search(ev):
        node = SPLIT[oid][1]; level = "L3"; fam_key = node.split(".")[0]
        basis = "split by plan wording"; evid = SPLIT[oid][0].search(ev).group(0); status = "split"
    elif l4["level"] == "L2":
        hits = [(m, cue_hit(m, ev)) for m in fam_mechs(fam_key)]
        hits = [(m, h) for m, h in hits if h]
        if len(hits) == 1:
            m, h = hits[0]
            node = f"{m['fam']}.{m['key']}"; level = "L3"; basis = "deepened by strategy wording"; evid = h; status = "deepened"
    elif l4["level"] == "GOAL":
        hits = [(m, cue_hit(m, ev)) for m in MECHS]
        hits = [(m, h) for m, h in hits if h and h.lower().strip() not in GENERIC]
        fams_hit = {m["fam"] for m, _ in hits}
        if len(hits) == 1:
            m, h = hits[0]
            node = f"{m['fam']}.{m['key']}"; level = "L3"; fam_key = m["fam"]
            basis = "goal triage: disguised objective, re-homed by strategy wording"; evid = h; status = "re-homed"
        elif len(fams_hit) == 1:
            fk = fams_hit.pop()
            node = fk; level = "L2"; fam_key = fk
            basis = "goal triage: disguised objective, re-homed to family by strategy wording"
            evid = "; ".join(h for _, h in hits); status = "re-homed"
        else:
            status = "held" if not hits else "held (ambiguous)"
            basis = "goal triage: held outside the tree"
            evid = "; ".join(sorted({h for _, h in hits}))[:120]
    condr = ""
    if node in MK:
        condr = " | ".join(r for r, rx in MK[node]["crl"] if rx.search(ev))
    sub = FAM[fam_key]["sub"] if fam_key and level != "GOAL" else (HOLD[l4["holding"]]["sub"] if l4["holding"] else "")
    if level == "GOAL":
        sub = ""
    old = OLDMAP.get(s.get("HDICategory", ""), "")
    srows.append(dict(strategy_key=d["strategy_key"], country=d["slug"], strategy=d["strategy"], sector=d["sector"],
                      objective_id=oid, l4_id=l4["oid"], l4_label=l4["label"], node=node, level=level,
                      family_id=FAM[fam_key]["fid"] if fam_key and level in ("L2", "L3") else "",
                      family=name_of.get(fam_key, "") if level in ("L2", "L3") else "",
                      mechanism_id=MK[node]["mid"] if node in MK else "",
                      mechanism=MK[node]["name"] if node in MK else "",
                      holding=l4["holding"] if level in ("STD", "GOAL") else "",
                      subpillar=sub, depth_basis=basis, evidence=evid, triage_status=status if l4["level"] == "GOAL" else status,
                      bau=("yes" if (l4["bau"] or s.get("response_orientation") == "BAU") else "no"),
                      response_orientation=s.get("response_orientation", ""),
                      related_risks=s.get("related_risks", ""), old_hdi=s.get("HDICategory", ""), old_hdi_mapped=old,
                      conditional_risks=condr, target=d["target"], instrument=d["instrument"]))

# ---------------------------------------------------------------- causal network
edges = []
for r in L4:
    own = r["mech_key"]
    if r["level"] == "L2":
        for c in r["candidates"].split(" | "):
            mid = c.split()[0]
            edges.append(dict(objective=r["oid"], objective_label=r["label"], mechanism_id=mid,
                              mechanism=c[len(mid) + 1:], relation="candidate within canonical family",
                              evidence="family process committed; channel not named", confidence="medium"))
    for m in MECHS:
        if m["fam"] == r["family_key"] or f"{m['fam']}.{m['key']}" == own:
            continue
        h = cue_hit(m, r["label"] + " " + r["definition"])
        if h:
            edges.append(dict(objective=r["oid"], objective_label=r["label"], mechanism_id=m["mid"], mechanism=m["name"],
                              relation="causal link outside canonical family", evidence=f"objective wording: '{h}'",
                              confidence="low"))
EXPLICIT = [("O0209", "F52.surge", "vaccine and medicine production capacity feeds surge capacity"),
            ("O0235", "F21.adversity", "protection-framed labour migration strategies"),
            ("O0101", "F09.reliability", "security of supply is also physical reliability"),
            ("O0094", "F09.reliability", "renewables change system reliability"),
            ("O0325", "F24.smoothing", "reviewer reconstruction"), ("O0325", "F24.adverse_coping", "reviewer reconstruction"),
            ("O0325", "F24.exante_risk", "reviewer reconstruction"),
            ("O0292", "F17.backlash", "regional equity is the populism channel")]
for o, mk, why in EXPLICIT:
    m = MK[mk]
    edges.append(dict(objective=o, objective_label=L4BY[o]["label"], mechanism_id=m["mid"], mechanism=m["name"],
                      relation="causal link (reviewed)", evidence=why, confidence="medium"))

# ---------------------------------------------------------------- counts
cnt_obj_mech = Counter(r["mech_key"] for r in L4 if r["level"] == "L3")
cnt_obj_fam = Counter(r["family_key"] for r in L4 if r["level"] in ("L2", "L3"))
cnt_str_node = Counter(s["node"] for s in srows)
cnt_str_fam = Counter(s["family_id"] for s in srows if s["family_id"])
str_risk = defaultdict(Counter)
for s in srows:
    for rk in re.findall(r"'([^']+)'", s["related_risks"]):
        str_risk[s["node"]][rk] += 1

for m in MECHS:
    k = f"{m['fam']}.{m['key']}"
    m["n_objectives"] = cnt_obj_mech.get(k, 0)
    m["n_strategies"] = cnt_str_node.get(k, 0)
    m["n_deepened"] = sum(1 for s in srows if s["node"] == k and s["depth_basis"] != "inherited from objective")
    m["n_countries"] = len({s["country"] for s in srows if s["node"] == k})
    m["suitability"] = ("distinguishable in plan evidence" if m["n_objectives"] or m["n_deepened"]
                        else "untested: no plan evidence yet (empty node)")
    rnames = [RISKS[x] for x in m["risks"]]
    obs = str_risk.get(k, Counter())
    m["risk_tags"] = " | ".join(rnames)
    m["risk_justification"] = m["risk_note"] or (f"literature in the {', '.join(rnames)} review notes" if rnames else "")
    m["observed_risk_tags"] = " | ".join(f"{a} ({b})" for a, b in obs.most_common(4))
for t, m in zip(tests, MECHS):
    t["q6_classification_suitability"] = m["suitability"]

# ---------------------------------------------------------------- write tables
fam_rows = []
for f in fams:
    fam_rows.append(dict(family_id=f["fid"], family=f["name"], pillar=PILLARS[SUB[f["sub"]][0]], subpillar=SUB[f["sub"]][1],
                         definition=f["definition"], core_variables=f["core"], inclusion_rule=f["include"],
                         exclusion_rule=clean_excl(f["exclude"]), literature=f["lit"],
                         primary_rhdr=SUB[f["sub"]][1], primary_reason=f["why"],
                         secondary_rhdr=" | ".join(f"{SUB[s][1]}: {why}" for s, why in f["sec"]),
                         risks=" | ".join(RISKS[x] for x in f["risks"]),
                         n_mechanisms=len(fam_mechs(f["id"])), n_objectives=cnt_obj_fam.get(f["id"], 0),
                         n_objectives_at_l2=sum(1 for r in L4 if r["level"] == "L2" and r["family_key"] == f["id"]),
                         n_strategies=cnt_str_fam.get(f["fid"], 0)))
w("families.csv", fam_rows, list(fam_rows[0].keys()))

mech_rows = []
for m in MECHS:
    f = FAM[m["fam"]]
    mech_rows.append(dict(mechanism_id=m["mid"], mechanism=m["name"], family_id=f["fid"], family=f["name"],
                          subpillar=SUB[f["sub"]][1], causal_input=m["input"], transmission=m["transmission"],
                          outcome=m["outcome"], conditions=m["conditions"], distinction=m["distinction"],
                          evidence=m["evidence"], risks=m["risk_tags"], risk_justification=m["risk_justification"],
                          primary_rhdr=SUB[f["sub"]][1], primary_reason=f["why"],
                          secondary_links=" | ".join(f"{SUB[s][1]}: {why}" for s, why in f["sec"]),
                          evidence_status=m["evidence_status"], risk_status=m["risk_status"],
                          conditional_risks=m["conditional_risks"], rejected_risks=m["rejected_risks"],
                          text_cues=m["cues"], n_objectives=m["n_objectives"], n_strategies=m["n_strategies"],
                          n_strategies_deepened=m["n_deepened"], n_countries=m["n_countries"],
                          classification_suitability=m["suitability"], observed_risk_tags=m["observed_risk_tags"]))
w("mechanisms.csv", mech_rows, list(mech_rows[0].keys()))
w("admission_tests.csv", tests, list(tests[0].keys()))

obj_rows = []
for r in sorted(L4, key=lambda r: r["oid"]):
    m = MK.get(r["mech_key"]) if r["mech_key"] else None
    f = FAM.get(r["family_key"]) if r["family_key"] else None
    sstr = [s for s in srows if s["l4_id"] == r["oid"]]
    obj_rows.append(dict(objective_id=r["oid"], objective=r["label"], definition=r["definition"],
                         level={"L3": "L3 mechanism", "L2": "L2 family", "STD": "Standard holding", "GOAL": "Goal held outside"}[r["level"]],
                         pillar=PILLARS[SUB[r["sub"]][0]] if r["sub"] else "", subpillar=SUB[r["sub"]][1] if r["sub"] else "",
                         family_id=f["fid"] if f and r["level"] != "GOAL" else "", family=f["name"] if f and r["level"] != "GOAL" else "",
                         mechanism_id=m["mid"] if m else "", mechanism=m["name"] if m else "",
                         holding=HOLD[r["holding"]]["name"] if r["holding"] else "",
                         depth_reason=r["depth_reason"], candidate_mechanisms=r["candidates"],
                         classification_basis=r["basis"], confidence=r["confidence"],
                         sibling_check=r.get("sibling_check", ""), secondary_rhdr=r["secondary_rhdr"], bau_flag="yes" if r["bau"] else "",
                         source_objective_ids=" | ".join(r["members"]), source_families=r["family_src"],
                         merge_history=r["merge_history"], aliases=r["aliases"],
                         n_strategies=len(sstr), n_countries=len({s["country"] for s in sstr}),
                         n_strategies_deeper=sum(1 for s in sstr if s["level"] == "L3" and r["level"] != "L3"),
                         sector_tags=" | ".join(sorted({s["sector"] for s in sstr if s["sector"]}))))
w("objectives_v1.csv", obj_rows, list(obj_rows[0].keys()))
w("strategy_nodes.csv", srows, list(srows[0].keys()))
w("causal_network.csv", edges, list(edges[0].keys()))
empty = [r for r in mech_rows if r["n_strategies"] == 0]
w("empty_nodes.csv", empty, ["mechanism_id", "mechanism", "family", "subpillar", "evidence", "risks", "causal_input", "outcome"])

# country x family matrix with depth shares
cm = defaultdict(lambda: Counter())
for s in srows:
    if s["family_id"]:
        cm[(s["country"], s["family_id"])][s["level"]] += 1
cm_rows = [dict(country=c, family_id=fid, family=next(f["name"] for f in fams if f["fid"] == fid),
                n_l2=v["L2"], n_l3=v["L3"], share_l3=round(v["L3"] / (v["L2"] + v["L3"]), 3)) for (c, fid), v in sorted(cm.items())]
w("country_node_matrix.csv", cm_rows, list(cm_rows[0].keys()))

# ---------------------------------------------------------------- JSON for the viewer
tree = dict(
    meta=dict(version="mother tree v1 (draft for sign-off)", built="2026-10-20", n_strategies=len(srows),
              n_countries=len({s["country"] for s in srows})),
    pillars=[dict(code=k, name=v) for k, v in PILLARS.items()],
    subpillars=[dict(code=c, pillar=p, name=l, standard=s) for c, p, l, s in SUBPILLARS],
    families=fam_rows, mechanisms=mech_rows,
    holding=[dict(id=h["hid"], sub=h["sub"], name=h["name"], definition=h["definition"]) for h in HOLD.values()],
    objectives=obj_rows,
    strategies=[{k: s[k] for k in ("strategy_key", "country", "strategy", "sector", "l4_id", "level", "family_id",
                                   "mechanism_id", "holding", "subpillar", "depth_basis", "evidence", "bau",
                                   "target", "instrument", "triage_status")} for s in srows],
    edges=edges, risks=list(RISKS.values()))
json.dump(tree, open(os.path.join(HERE, "tree_v1.json"), "w"), ensure_ascii=False)

# ---------------------------------------------------------------- validation report
N = len(srows)
lv = Counter(s["level"] for s in srows)
olv = Counter(r["level"] for r in L4)
deep = Counter(s["depth_basis"] for s in srows)
goal_s = [s for s in srows if L4BY[s["l4_id"]]["level"] == "GOAL"]
goal_status = Counter(s["triage_status"] for s in goal_s)
mapped = [s for s in srows if s["old_hdi_mapped"] and s["subpillar"]]
agree = sum(1 for s in mapped if s["old_hdi_mapped"] == s["subpillar"])
big = sorted([m for m in mech_rows if m["n_objectives"] >= 5], key=lambda m: -m["n_objectives"])
one_child = [f for f in fam_rows if f["n_mechanisms"] < 2]
lines = []
P = lines.append
P("# Mother tree v1: validation\n")
P(f"Built {tree['meta']['built']}. {len(fam_rows)} families, {len(mech_rows)} mechanisms, {len(L4)} objectives after consolidation "
  f"(from {len(objs)}), {N} strategies in {tree['meta']['n_countries']} countries.\n")
P("## Coverage, both directions\n")
P(f"- Objective side: {len(objs)} of {len(objs)} source objectives placed exactly once (exclusive and exhaustive).")
P(f"- Strategy side: {N} of {N} strategies resolve to a node.")
P(f"- Literature side: {sum(1 for m in mech_rows if m['n_strategies'])} mechanisms hold strategies; {len(empty)} are empty nodes, kept with their literature (empty_nodes.csv).")
P(f"- Every mechanism passes the structural form of the five-question admission test ({sum(t['passes_all'] for t in tests)} of {len(tests)}): "
  "named as a relationship, input, transmission and outcome stated, a citation present, a sibling distinction stated, a family process stated. "
  "That is not evidence that each paper supports the claim. Source verification is tracked separately below.\n")
P("## Source verification\n")
ev = Counter(m["evidence_status"].split(":")[0] for m in MECHS)
rs = Counter(m["risk_status"].split(":")[0].split(";")[0] for m in MECHS)
P(f"- Evidence: {ev.get('source-verified', 0)} mechanisms source-verified, {ev.get('cited, not yet independently verified', 0)} cited but not yet independently verified.")
P(f"- Risk tags: {rs.get('tagged from the review notes', 0)} tagged from the review notes and not yet source-verified; {rs.get('baseline', 0)} baseline mechanisms with no risk tag by design.")
nc = sum(1 for c in CRL if c["decision"] != "REJECT"); nr = sum(1 for c in CRL if c["decision"] == "REJECT")
P(f"- Conditional risk links: {nc} accepted as conditional. They apply to a strategy only when its wording meets the stated scope, and never enter the mechanism × risk matrix. {nr} were rejected.")
P(f"- Strategies carrying a conditional risk link: {sum(1 for s in srows if s['conditional_risks'])}.\n")
P("## Depth\n")
P("| | Objectives | Strategies |\n|---|---|---|")
for k, lab in (("L3", "L3 mechanism"), ("L2", "L2 family"), ("STD", "Standard holding"), ("GOAL", "Goal held outside")):
    P(f"| {lab} | {olv.get(k,0)} ({olv.get(k,0)/len(L4):.0%}) | {lv.get(k,0)} ({lv.get(k,0)/N:.0%}) |")
P("")
P("How strategies got their depth:\n")
for k, v in deep.most_common():
    P(f"- {k}: {v}")
P("")
P("## Goal triage\n")
P(f"{olv.get('GOAL',0)} goal-shaped objectives hold {len(goal_s)} strategies.\n")
for k, v in goal_status.most_common():
    P(f"- {k}: {v}")
P("")
P("## Standard holding branches\n")
for h in ("H-SPE", "H-SEC", "H-SGO"):
    k = sum(1 for s in srows if s["holding"] == h)
    P(f"- {HOLD[h]['name']}: {k} strategies ({k/N:.1%})")
P("")
P("## Diagnostic against the earlier RHDR coding\n")
P(f"On the {len(mapped)} strategies whose earlier HDICategory maps onto an amended subpillar, the tree's primary subpillar agrees on {agree} ({agree/len(mapped):.0%}). "
  "Agreement is a diagnostic, not a target: the earlier coding was by strategy and by the old framework, the tree is by mechanism.\n")
P("## Second coder and sibling test\n")
qk = {r["objective_id"]: r for r in csv.DictReader(open(os.path.join(HERE, "qa", "recode_first_pass.csv")))}
qc = {r["objective_id"]: r for r in csv.DictReader(open(os.path.join(HERE, "qa", "recode_coder2.csv")))}
LVQ = {"L3 mechanism": "L3", "L2 family": "L2", "Standard holding": "STD", "Goal held outside": "GOAL"}
HQ = {"Standard People holding branch": "H-SPE", "Standard Economy holding branch": "H-SEC", "Standard Governance holding branch": "H-SGO", "Goals held outside the tree": "H-GOAL"}
def nd(r, first):
    f = r["family_id"] or (HQ.get(r["holding"], r["holding"]) if first else r["holding"])
    return f, (r["mechanism_id"] or f), (LVQ[r["level"]] if first else r["level"])
agf = sum(nd(qk[k], 1)[0] == nd(qc[k], 0)[0] for k in qk); agn = sum(nd(qk[k], 1)[1] == nd(qc[k], 0)[1] for k in qk)
final = {r["oid"]: r for r in L4}
agn2 = sum(1 for k in qk if k in final and (final[k]["mech_key"] and MK[final[k]["mech_key"]]["mid"] or (FAM[final[k]["family_key"]]["fid"] if final[k]["family_key"] and final[k]["level"] != "GOAL" else final[k]["holding"])) == nd(qc[k], 0)[1])
P(f"A second coder placed a stratified 10% sample ({len(qk)} objectives) blind, from the family and mechanism definitions only. "
  f"First pass against coder 2: same family {agf} ({agf/len(qk):.0%}), same node {agn} ({agn/len(qk):.0%}). "
  f"Of the {len(qk) - agn} disagreements, {agn2 - agn} were resolved toward coder 2 and {len(qk) - agn2} kept with a reason (ADJUDICATION.md). "
  "Agreement after adjudication is not a validation statistic; the first-pass figures are.\n")
nchal = sum(1 for r in L4 if r.get("sibling_check", "").startswith("challenged"))
P(f"Sibling test: every L3 objective is checked for a sibling mechanism that its own wording also matches. {nchal} were challenged and kept with a reason; none is unadjudicated.\n")
P("## Flags for review\n")
P("Mechanisms holding five or more objectives (review for a split only if the literature names a distinct channel):\n")
for m in big:
    P(f"- {m['mechanism']} ({m['family']}): {m['n_objectives']} objectives, {m['n_strategies']} strategies")
P("")
if one_child:
    P("Families with one mechanism: " + ", ".join(f["family"] for f in one_child))
open(os.path.join(HERE, "VALIDATION.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
