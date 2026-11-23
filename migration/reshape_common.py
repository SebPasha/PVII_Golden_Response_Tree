"""Shared by reshape.py and sources.py: regions, country names, the tree, the strategy columns."""
import csv
import json
import os
import re

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))

REGIONS = {
    "South-East Asia": "brunei cambodia indonesia laos malaysia myanmar philippines thailand timor_leste vietnam",
    "South Asia": "afghanistan bangladesh bhutan india iran maldives nepal pakistan sri_lanka",
    "East Asia": "china mongolia",
    "Pacific": "fiji kiribati marshall_islands nauru palau papua_new_guinea samoa solomon_islands tonga tuvalu vanuatu",
    "Europe and Central Asia": "kazakhstan serbia uzbekistan",
    "Arab States": "egypt morocco",
    "Africa": "ethiopia ghana kenya nigeria rwanda",
    "Latin America and the Caribbean": "brazil colombia jamaica peru",
}
REGION = {s: r for r, ss in REGIONS.items() for s in ss.split()}
NAMES = {"timor_leste": "Timor-Leste", "sri_lanka": "Sri Lanka", "papua_new_guinea": "Papua New Guinea",
         "marshall_islands": "Marshall Islands", "solomon_islands": "Solomon Islands", "laos": "Lao PDR",
         "vietnam": "Viet Nam", "brunei": "Brunei Darussalam"}

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"\.(pdf|docx?|txt)$", "", s.lower())).strip()


def jl(s):
    try:
        v = json.loads(s) if isinstance(s, str) and s.strip() else (s or [])
        return v if isinstance(v, list) else []
    except ValueError:
        return []


def sheet_rows(path, all_sheets=False):
    wb = openpyxl.load_workbook(path, read_only=True)
    for ws in (wb.worksheets if all_sheets else wb.worksheets[:1]):
        it = ws.iter_rows(values_only=True)
        head = list(next(it))
        for r in it:
            yield ws.title, dict(zip(head, r))



tree = json.load(open(os.path.join(HERE, "..", "tree", "v4", "tree_v4.json"), encoding="utf-8"))
LV = {x["lever_id"]: x for x in tree["levers"]}
FAM = {x["family_id"]: x for x in tree["families"]}
GRP = {x["group_id"]: x for x in tree["groups"]}
SUB = {x["code"]: x for x in tree["subpillars"]}
PIL = {x["code"]: x["name"] for x in tree["pillars"]}
HOLD = {x["id"]: x["name"] for x in tree["holding"]}

def place(node):
    """The tree columns for a node id."""
    o = dict(node_id=node, level="", group_id="", group="", family_id="", family="", lever_id="", lever="",
             subpillar="", pillar_rhdr="")
    if node in LV:
        o.update(level="L3", lever_id=node, lever=LV[node]["lever"], family_id=LV[node]["family_id"])
    elif node in FAM:
        o.update(level="L2", family_id=node)
    elif node in GRP:
        o.update(level="L1", group_id=node)
    elif node == "H-GOAL":
        o.update(level="GOAL")
    elif node in HOLD:
        o.update(level="STD")
    if o["family_id"]:
        f = FAM[o["family_id"]]
        o.update(family=f["family"], group_id=f["group_id"])
    if o["group_id"]:
        g = GRP[o["group_id"]]
        sp = SUB[g["subpillar_code"]]
        o.update(group=g["group"], subpillar=sp["name"], pillar_rhdr=PIL[sp["pillar"]])
    return o


COLS = ["strategy_id", "plan_id", "country", "slug", "region", "doc_type", "edition", "plan_title", "period_start",
        "period_end", "published", "name", "objective", "target_group", "instrument", "pillar", "statement_type",
        "related_risks", "n_mentions", "members", "refs", "quote", "quote_check", "named_agencies", "stated_urgency",
        "sdg_targets", "response_orientation", "sector", "institutional_lead", "implementation_status",
        "has_timeline", "has_quantified_target", "has_monitoring", "legal_or_plan_basis", "tree_version", "relation",
        "objective_id", "tree_objective", "node_id", "level", "depth_basis", "group_id", "group", "family_id", "family",
        "lever_id", "lever", "subpillar", "pillar_rhdr", "target_id", "target_label", "instrument_id",
        "instrument_label", "confidence", "reason", "source_strategy_key", "n_editions", "first_edition"]
