"""Write the joining workbook: one plan's strategies joined to tree v4.

    python3 tree/v4/join_xlsx.py <strategies.csv> [proposals.csv] <out.xlsx>

Sheets: Read me; Joins (one row per strategy with its lever, family, group, pathway, reason);
Levers (count per lever); Families (count per family, incl. family-only placements);
Summary (placement counts); Proposals (strategies the tree could not place, if given).
"""
import csv, json, os, sys
from collections import Counter, OrderedDict
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = json.load(open(os.path.join(HERE, "tree_v4.json"), encoding="utf-8"))
LEVERS = {l["lever_id"]: l for l in TREE["levers"]}
FAMILIES = {f["family_id"]: f for f in TREE["families"]}

JOIN_COLS = [
    ("strategy_id", 11), ("name", 34), ("objective", 34), ("target_group", 18), ("instrument", 18),
    ("quote_en", 50), ("relation", 9), ("level", 7), ("pillar_rhdr", 16), ("subpillar", 20),
    ("group_id", 8), ("group", 24), ("family_id", 8), ("family", 30), ("lever_id", 8), ("lever", 34),
    ("joins when", 40), ("pathway_id", 8), ("pathway", 28), ("depth_basis", 18), ("reason", 40),
    ("new_objective", 30), ("confidence", 9), ("target_label", 16), ("instrument_label", 16),
    ("related_risks", 20), ("map_note", 30),
]
HEAD = Font(bold=True)
FILL = PatternFill("solid", fgColor="DDE7F0")


def sheet(wb, name, cols, rows, wrap_from=0):
    ws = wb.create_sheet(name)
    ws.append([c for c, _ in cols])
    for cell in ws[1]:
        cell.font = HEAD; cell.fill = FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([r.get(c, "") for c, _ in cols])
    for i, (c, w) in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    return ws


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    strat_path, out = argv[1], argv[-1]
    prop_path = argv[2] if len(argv) == 4 else ""
    rows = list(csv.DictReader(open(strat_path, encoding="utf-8")))
    for r in rows:
        lv = LEVERS.get(r.get("lever_id", ""))
        r["joins when"] = lv["joins_when"] if lv else ""
    wb = Workbook()
    wb.remove(wb.active)
    plan = rows[0].get("plan_title", "") if rows else ""
    n = len(rows)
    lever = sum(1 for r in rows if r.get("lever_id"))
    path = sum(1 for r in rows if r.get("pathway_id"))
    fam_only = sum(1 for r in rows if r.get("level") == "L2")
    grp_only = sum(1 for r in rows if r.get("level") == "L1")
    general = sum(1 for r in rows if str(r.get("node_id", "")).startswith("H-"))
    new = sum(1 for r in rows if r.get("relation") == "new")
    pct = lambda k: "%d (%.0f%%)" % (k, 100.0 * k / n) if n else "0"
    summary = [
        ("Plan", plan), ("Strategies", n), ("Placed on a lever (L3)", pct(lever)),
        ("of which with a pathway recorded (L4)", pct(path)),
        ("Family only (L2)", pct(fam_only)), ("Group only (L1)", pct(grp_only)),
        ("General branch or goal (H-)", pct(general)), ("Nothing fits (relation new)", pct(new)),
        ("Tree", "v4, %d levers over %d pathways" % (len(TREE["levers"]), len(TREE["pathways"]))),
    ]
    ws = wb.create_sheet("Read me")
    ws["A1"] = "Strategies joined to the PV II mother tree v4"; ws["A1"].font = Font(bold=True, size=13)
    ws.append([])
    for k, v in summary:
        ws.append([k, v])
    ws.append([])
    for line in [
        "Joins: one row per strategy as extracted from the plan, with the node the mapping step chose.",
        "lever_id/lever: the lever (L3) the strategy sits on, judged by meaning against the lever's 'joins when' test.",
        "pathway_id/pathway: recorded only when the lever has one pathway or the strategy names the channel (depth_basis says which).",
        "level L2 with no lever: a summary line or an action no lever of the family describes; 'reason' says what lever is missing.",
        "reason: the words of the strategy that met the test, in the model's phrase. relation new: nothing in the tree fits; see Proposals.",
        "Levers / Families: counts of strategies per node. Family counts include strategies placed on the family's levers.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 44; ws.column_dimensions["B"].width = 60
    sheet(wb, "Joins", JOIN_COLS, rows)

    lc = Counter(r["lever_id"] for r in rows if r.get("lever_id"))
    lp = Counter(r["lever_id"] for r in rows if r.get("lever_id") and r.get("pathway_id"))
    lrows = []
    for lid, l in LEVERS.items():
        lrows.append({"lever_id": lid, "lever": l["lever"], "family_id": l["family_id"], "family": l["family"],
                      "group": l["group"], "subpillar": l["subpillar"], "strategies": lc.get(lid, 0),
                      "with pathway": lp.get(lid, 0), "joins when": l["joins_when"]})
    lrows.sort(key=lambda d: -d["strategies"])
    sheet(wb, "Levers", [("lever_id", 8), ("lever", 36), ("family_id", 8), ("family", 30), ("group", 24),
                         ("subpillar", 20), ("strategies", 10), ("with pathway", 11), ("joins when", 44)], lrows)

    fc = Counter(r["family_id"] for r in rows if r.get("family_id"))
    fo = Counter(r["family_id"] for r in rows if r.get("family_id") and r.get("level") == "L2")
    frows = []
    for fid, f in FAMILIES.items():
        frows.append({"family_id": fid, "family": f["family"], "group": f.get("group", ""),
                      "subpillar": f.get("subpillar", ""), "strategies": fc.get(fid, 0),
                      "family only (no lever)": fo.get(fid, 0), "levers": f.get("n_levers", "")})
    frows.sort(key=lambda d: -d["strategies"])
    sheet(wb, "Families", [("family_id", 8), ("family", 34), ("group", 24), ("subpillar", 20),
                           ("strategies", 10), ("family only (no lever)", 12), ("levers", 7)], frows)

    # what the family lacks, by the model's own reason, for the family-only rows
    miss = [{"family_id": r["family_id"], "family": r["family"], "strategy": r["name"], "reason": r.get("reason", "")}
            for r in rows if r.get("level") == "L2" and r.get("family_id")]
    miss.sort(key=lambda d: d["family_id"])
    sheet(wb, "Family only", [("family_id", 8), ("family", 34), ("strategy", 40), ("reason", 60)], miss)

    if prop_path and os.path.exists(prop_path):
        props = list(csv.DictReader(open(prop_path, encoding="utf-8")))
        if props:
            cols = [(c, 30) for c in props[0].keys()]
            sheet(wb, "Proposals", cols, props)
    wb.save(out)
    print("wrote", out, "rows", n, "lever", lever, "pathway", path, "family-only", fam_only, "new", new)


if __name__ == "__main__":
    main(sys.argv)
