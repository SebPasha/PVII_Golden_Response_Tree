"""The closed lists step E answers from, and the lookups and rules applied to its answers.

Lifted from PV2: hdi_framework_text, sector_canonical, sdg_dimension_of and canonical from
workflow/pv2/vocab.py; the clamps and the risk pairing from extract/schemas.py
(validate_stage4, _pair_risks); maturity from calcs/panel.py; the primary-dimension vote from
calcs/panel.py. The lists are vocab/rhdr_2026_10.json (the amended RHDR framework the Work in
progress tab is built on) and vocab/sdg_target_dimensions.json, both copied unchanged.
"""
import collections
import json
import os

from pvii.config import RISKS

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vocab")
with open(os.path.join(_DIR, "rhdr_2026_10.json"), encoding="utf-8") as _f:
    _V = json.load(_f)
with open(os.path.join(_DIR, "sdg_target_dimensions.json"), encoding="utf-8") as _f:
    SDG_TARGET_DIMENSIONS = json.load(_f)

HDI_FAMILIES = [(f["name"], f["categories"]) for f in _V["hdi_families"]]
HDI = [c for _, cats in HDI_FAMILIES for c in cats]
HDI_PILLAR = {c: fam for fam, cats in HDI_FAMILIES for c in cats}
SDG_GOALS = list(_V["sdg_goals"])
_SECTOR_MAP = dict(_V["sector_canonical"]["map"])

# PV2's values and, for each, the default an answer outside the list falls to (validate_stage4).
ORIENTATIONS = {"bau": "BAU", "inactive": "BAU", "reactive": "BAU",
                "proactive": "proactive", "transformative": "transformative"}
STATUSES = ("operational", "planned", "aspiration")          # strongest first
BASES = ("law", "plan", "strategy", "none")                  # strongest first
URGENCIES = ("high", "medium", "low")                        # highest first
MAX_RISKS = 3


def canonical(value, choices):
    """The list entry matching `value` case-insensitively, or None."""
    key = str(value or "").strip().lower()
    for c in choices:
        if c.lower() == key:
            return c
    return None


def hdi_framework_text():
    """The categories as the prompt gives them, put in at <<INSERT_HDI_FRAMEWORK_HERE>>.

    A category with no definition raises, because a prompt with a hole in it still runs.
    """
    fw = _V["hdi_framework"]
    defs = fw.get("categories") or {}
    lines = []
    for family, names in HDI_FAMILIES:
        lines.append(family)
        for name in names:
            if not (defs.get(name) or {}).get("definition"):
                raise KeyError("hdi_framework has no definition for %r" % name)
            lines.append("  %s: %s" % (name, defs[name]["definition"]))
            lines += ['    For example: "%s"' % e for e in defs[name].get("examples") or []]
    rules = fw.get("rules") or []
    if rules:
        lines += ["", "Overlaps and tie-breaks, applied in this order:"]
        lines += ["%d. %s" % (i, r) for i, r in enumerate(rules, 1)]
    return "\n".join(lines)


def sector_canonical(value):
    """The canonical sector for a sector string, or '' where none maps (shown as unmapped)."""
    return _SECTOR_MAP.get(str(value or "").strip().lower(), "")


def sdg_dimension_of(target):
    """The 5P primary dimension for a target code, or '' where the code is not official."""
    return (SDG_TARGET_DIMENSIONS.get(str(target or "").strip()) or {}).get("primary_dimension", "")


def primary_dimension(targets):
    """Majority vote over the targets' dimensions, ties to the first target named."""
    dims = [d for d in (sdg_dimension_of(t) for t in targets) if d]
    if not dims:
        return ""
    counts = collections.Counter(dims)
    top = max(counts.values())
    return next(d for d in dims if counts[d] == top)


def pair_risks(risks, evidence, found):
    """(risks, quotes) aligned and capped: a risk whose quote is blank or not found is dropped.

    Paired by POSITION on the raw lists, before anything is dropped: compacting either list
    first slides every later quote onto an earlier risk (PV2 W74). `found(quote)` says whether
    the quote is in the text the model was shown.
    """
    out, seen, dropped = [], set(), []
    for i, r in enumerate(risks):
        r = str(r).strip()
        q = str(evidence[i]).strip() if i < len(evidence) else ""
        if r not in RISKS or r in seen:
            continue
        if not q or not found(q):
            dropped.append(r)
            continue
        seen.add(r)
        out.append((r, q))
        if len(out) == MAX_RISKS:
            break
    return [r for r, _ in out], [q for _, q in out], dropped


def maturity(status, has_timeline, has_target, funded=False, has_monitor=False, legal="",
             persistence=0.0):
    """PV2's maturity subtype. Until the budget lane returns nothing is funded, so only the
    three unfunded subtypes (planned_specific, planned, aspirational) can come out."""
    if funded:
        if status == "operational" and (legal == "law" or has_monitor):
            return "operational_funded"
        return "partial_operation" if persistence < 0.5 else "operational_programme"
    if status == "planned" and has_target and has_timeline:
        return "planned_specific"
    return "planned" if status == "planned" else "aspirational"

