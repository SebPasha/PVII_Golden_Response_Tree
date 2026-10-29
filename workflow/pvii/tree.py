"""The mother tree as step M reads it: one released version, read-only.

The tree is built under tree/ and this module only reads its release file. `load()` reads
whichever release is in config.TREE_DIR (tree/v2 unless PVII_TREE says otherwise):

- v3 (tree_v3.json): RHDR pillar, subpillar, group (L1), family (L2, the required level),
  pathway (L3), then objective (L4) and strategy (L5). The reviewer's framework over v2's
  pathways. A family placement is taken as answered; a pathway needs its `text_cues` in the
  strategy's wording; a group alone is a weak placement and is counted.
- v2 (tree_v2.json): pillar, subpillar, family (L1), mechanism (L2), pathway (L3). Depth is
  tested with the mechanism's `plan_words` and the pathway's `text_cues`. Neither v2 nor v3
  holds objectives yet: step M places each strategy on a node and proposes the objective.
- v1 (tree_v1.json): pillar, subpillar, family (L2), mechanism (L3), objective (L4), strategy.
  Targets and instruments come from tree/inputs.

THE DEPTH RULE IS THE TREE'S OWN (README, Rule 7: no invented specificity). A strategy sits at
a mechanism (L3) only when its objective sits there, or when its own wording names exactly
that mechanism, which is tested here with the mechanism's `text_cues` pattern, the same cues
the v1 build deepened 1,277 strategies with. A model answer claiming L3 without that support
is moved back to the family and the reason is written on the row.
"""
import csv
import json
import os
import re

from pvii import config

RELATIONS = ("same", "differs", "new", "placed")   # v1: same/differs/new; v2: placed/new


class TreeV2:
    """tree_v2.json or tree_v3.json. Same interface as Tree, with pathways and no objectives.

    The three placement levels are held as `top` (v2 family / v3 group), `mid` (v2 mechanism /
    v3 family) and `pathways`; `level_names` says what each is called in this release.
    """

    def __init__(self, tree_dir=None):
        tree_dir = tree_dir or config.TREE_DIR
        v3 = os.path.join(tree_dir, "tree_v3.json")
        path = v3 if os.path.exists(v3) else os.path.join(tree_dir, "tree_v2.json")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        meta = d.get("meta") or {}
        self.version = meta.get("version", "v2")
        self.built = meta.get("built", "")
        self.pillars = {p["code"]: p for p in d["pillars"]}
        self.subpillars = {s["code"]: s for s in d["subpillars"]}
        self.sub_by_name = {s["name"]: s["code"] for s in d["subpillars"]}
        if "groups" in d:                                   # v3
            self.level_names = ("group", "family", "pathway")
            self.top = {g["group_id"]: g for g in d["groups"]}
            self.mid = {f["family_id"]: f for f in d["families"]}
            self.required_level = meta.get("required_level", "L2")
            self.test_mid_cues = False                      # a family is taken as answered
        else:                                               # v2
            self.level_names = ("family", "mechanism", "pathway")
            self.top = {f["family_id"]: f for f in d["families"]}
            self.mid = {m["mechanism_id"]: m for m in d["mechanisms"]}
            self.required_level = ""
            self.test_mid_cues = True                       # a mechanism needs its plan words
        self.families, self.mechanisms = self.top, self.mid     # the v2 names, kept for callers
        self.pathways = {p["pathway_id"]: p for p in d["pathways"]}
        self.holding = {h["id"]: h for h in d["holding"]}
        self.objectives = {}
        self.targets = {t["target_id"]: {"label": t["target_label"]} for t in d["target_classes"]}
        self.instruments = {i["instrument_id"]: {"label": i["instrument_label"]}
                            for i in d["instrument_classes"]}
        self._cues = {}
        for nid, n in list(self.mid.items()) + list(self.pathways.items()):
            cue = (n.get("plan_words") or n.get("text_cues") or "").strip()
            if cue:
                try:
                    self._cues[nid] = re.compile(cue, re.I)
                except re.error:
                    pass

    def canonical(self, node_id):
        """A merged pathway's id is the sibling it was merged into."""
        p = self.pathways.get(node_id)
        return p["merged_into"] if p and p.get("merged_into") else node_id

    def level_of(self, node_id):
        if node_id in self.pathways:
            return "L3"
        if node_id in self.mechanisms:
            return "L2"
        if node_id in self.families:
            return "L1"
        if node_id in self.holding:
            return "GOAL" if node_id == "H-GOAL" else "STD"
        return ""

    def _mid_of(self, node):
        return node.get("family_id") if self.level_names[1] == "family" else node.get("mechanism_id")

    def _top_of(self, node):
        return node.get("group_id") if self.level_names[0] == "group" else node.get("family_id")

    def parent_of(self, node_id):
        if node_id in self.pathways:
            return self._mid_of(self.pathways[node_id])
        if node_id in self.mid:
            return self._top_of(self.mid[node_id])
        return ""

    def family_of(self, node_id):
        """The top-level node (v2 family, v3 group) a node sits under."""
        if node_id in self.pathways:
            return self._top_of(self.pathways[node_id])
        if node_id in self.mid:
            return self._top_of(self.mid[node_id])
        if node_id in self.top:
            return node_id
        return ""

    def cue_matches(self, node_id, text):
        rx = self._cues.get(node_id)
        m = rx.search(text or "") if rx else None
        return m.group(0) if m else ""

    def describe(self, node_id):
        """The node's line of ancestors, in the release's own names. v3 fills group and family;
        v2 fills family and mechanism."""
        out = {"group_id": "", "group": "", "family_id": "", "family": "", "mechanism_id": "",
               "mechanism": "", "pathway_id": "", "pathway": "", "subpillar": "", "pillar": ""}
        top_key, mid_key, _ = self.level_names
        if node_id in self.pathways:
            p = self.pathways[node_id]
            out.update(pathway_id=node_id, pathway=p["pathway"])
            node_id = self._mid_of(p)
        if node_id in self.mid:
            m = self.mid[node_id]
            out[mid_key + "_id"], out[mid_key] = node_id, m[mid_key]
            node_id = self._top_of(m)
        if node_id in self.top:
            f = self.top[node_id]
            out[top_key + "_id"], out[top_key] = node_id, f[top_key]
            out.update(subpillar=f["subpillar"], pillar=f["pillar"])
        elif node_id in self.holding:
            # The holding branch's own name is the subpillar (Standard People in v2, General People in v3).
            pil = {"H-SPE": "PFA", "H-SEC": "SMG", "H-SGO": "MCH"}.get(node_id, "")
            out.update(subpillar=self.holding[node_id]["name"] if pil else "",
                       pillar=self.pillars[pil]["name"] if pil in self.pillars else "")
        return out

    def menu(self):
        """The tree as text: each top node, its middle nodes and their pathways."""
        top_key, mid_key, _ = self.level_names
        if top_key == "group":
            lines = ["GROUPS (L1), THEIR FAMILIES (L2, THE REQUIRED LEVEL) AND PATHWAYS (L3)",
                     "A group names a broad area; a family names the development purpose; a pathway names the causal channel.", ""]
        else:
            lines = ["FAMILIES (L1), THEIR MECHANISMS (L2) AND PATHWAYS (L3)",
                     "A family names a domain; a mechanism names the lever; a pathway names the causal channel.", ""]
        for fid, f in sorted(self.top.items()):
            lines.append("%s %s [%s] - %s" % (fid, f[top_key], f.get("subpillar_code", ""),
                                               _short(f.get("meaning") or f.get("definition"), 200)))
            for mid in f.get(mid_key + "_ids") or []:
                m = self.mid[mid]
                if mid_key == "family":
                    lines.append("  %s %s: %s" % (mid, m["family"], _short(m.get("definition"), 160)))
                else:
                    lines.append("  %s %s: moves %s" % (mid, m["mechanism"],
                                                         _short(m.get("intermediate_variable"), 90)))
                for pid in m.get("pathway_ids") or []:
                    p = self.pathways.get(pid)
                    if p and not p.get("merged_into"):
                        lines.append("    %s %s: %s -> %s -> %s" % (
                            pid, p["pathway"], _short(p.get("causal_input"), 50),
                            _short(p.get("transmission"), 70), _short(p.get("outcome"), 50)))
            lines.append("")
        lines.append("GENERAL BRANCHES (no family; standing functions of the state, or goals)")
        for hid, h in sorted(self.holding.items()):
            lines.append("%s %s" % (hid, h["name"]))
        lines += ["", "TARGET GROUPS"]
        lines += ["%s %s" % (k, v["label"]) for k, v in sorted(self.targets.items())]
        lines += ["", "INSTRUMENTS"]
        lines += ["%s %s" % (k, v["label"]) for k, v in sorted(self.instruments.items())]
        return "\n".join(lines)


class Tree:
    def __init__(self, tree_dir=None, inputs_dir=None):
        tree_dir = tree_dir or config.TREE_DIR
        inputs_dir = inputs_dir or config.TREE_INPUTS
        with open(os.path.join(tree_dir, "tree_v1.json"), encoding="utf-8") as f:
            d = json.load(f)
        self.version = (d.get("meta") or {}).get("version", "v1")
        self.built = (d.get("meta") or {}).get("built", "")
        self.pillars = {p["code"]: p for p in d["pillars"]}
        self.subpillars = {s["code"]: s for s in d["subpillars"]}
        self.sub_by_name = {s["name"]: s["code"] for s in d["subpillars"]}
        self.families = {f["family_id"]: f for f in d["families"]}
        self.mechanisms = {m["mechanism_id"]: m for m in d["mechanisms"]}
        self.holding = {h["id"]: h for h in d["holding"]}
        self.objectives = {o["objective_id"]: o for o in d["objectives"]}
        self.targets = _labels(os.path.join(inputs_dir, "targets.csv"), "target_id")
        self.instruments = _labels(os.path.join(inputs_dir, "instruments.csv"), "instrument_id")
        self._cues = {}
        for mid, m in self.mechanisms.items():
            cue = (m.get("text_cues") or "").strip()
            if cue:
                try:
                    self._cues[mid] = re.compile(cue, re.I)
                except re.error:
                    pass

    # ------------------------------------------------------------ nodes
    def node_of_objective(self, oid):
        """(node_id, level) where an existing objective sits."""
        o = self.objectives[oid]
        if o.get("holding"):
            return o["holding"], ("GOAL" if o["holding"] == "H-GOAL" else "STD")
        if o.get("mechanism_id"):
            return o["mechanism_id"], "L3"
        return o.get("family_id") or "", "L2"

    def level_of(self, node_id):
        if node_id in self.mechanisms:
            return "L3"
        if node_id in self.families:
            return "L2"
        if node_id in self.holding:
            return "GOAL" if node_id == "H-GOAL" else "STD"
        return ""

    def family_of(self, node_id):
        if node_id in self.mechanisms:
            return self.mechanisms[node_id]["family_id"]
        if node_id in self.families:
            return node_id
        return ""

    def cue_matches(self, mechanism_id, text):
        rx = self._cues.get(mechanism_id)
        m = rx.search(text or "") if rx else None
        return m.group(0) if m else ""

    def describe(self, node_id):
        """{family_id, family, mechanism_id, mechanism, subpillar, pillar} for a node."""
        out = {"family_id": "", "family": "", "mechanism_id": "", "mechanism": "",
               "subpillar": "", "pillar": ""}
        if node_id in self.mechanisms:
            m = self.mechanisms[node_id]
            out.update(mechanism_id=node_id, mechanism=m["mechanism"])
            node_id = m["family_id"]
        if node_id in self.families:
            f = self.families[node_id]
            out.update(family_id=node_id, family=f["family"], subpillar=f["subpillar"],
                       pillar=f["pillar"])
        elif node_id in self.holding:
            h = self.holding[node_id]
            sub = self.subpillars.get(h.get("sub") or "")
            pil = self.pillars.get(sub["pillar"]) if sub else None
            out.update(subpillar=sub["name"] if sub else "", pillar=pil["name"] if pil else "")
        return out

    # ------------------------------------------------------------ the menu step M reads
    def menu(self):
        """The tree as text, grouped by family so each objective sits beside its mechanisms."""
        objs_by_family, objs_by_holding = {}, {}
        for oid, o in sorted(self.objectives.items()):
            node, level = self.node_of_objective(oid)
            label = "%s %s" % (oid, o["objective"])
            if level in ("STD", "GOAL"):
                objs_by_holding.setdefault(node, []).append(label)
            else:
                at = " @" + node if level == "L3" else ""
                objs_by_family.setdefault(o["family_id"], []).append(label + at)
        lines = ["FAMILIES (L2), THEIR MECHANISMS (L3) AND EXISTING OBJECTIVES (L4)",
                 "An objective marked @L3-xxx sits at that mechanism; unmarked, it sits on the family.", ""]
        for fid, f in sorted(self.families.items()):
            sub = self.sub_by_name.get(f["subpillar"], "")
            lines.append("%s %s [%s] - %s" % (fid, f["family"], sub, _short(f["definition"], 220)))
            for mid, m in sorted(self.mechanisms.items()):
                if m["family_id"] == fid:
                    lines.append("  %s %s: %s -> %s -> %s" % (
                        mid, m["mechanism"], _short(m.get("causal_input"), 60),
                        _short(m.get("transmission"), 80), _short(m.get("outcome"), 60)))
            if objs_by_family.get(fid):
                lines.append("  objectives: " + " | ".join(objs_by_family[fid]))
            lines.append("")
        lines.append("HOLDING BRANCHES (no mechanism; visible, dropped from reporting)")
        for hid, h in sorted(self.holding.items()):
            lines.append("%s %s - %s" % (hid, h["name"], _short(h["definition"], 220)))
            if objs_by_holding.get(hid):
                lines.append("  objectives: " + " | ".join(objs_by_holding[hid]))
        lines += ["", "TARGET GROUPS"]
        lines += ["%s %s" % (k, v["label"]) for k, v in sorted(self.targets.items())]
        lines += ["", "INSTRUMENTS"]
        lines += ["%s %s - %s" % (k, v["label"], _short(v.get("definition"), 120))
                  for k, v in sorted(self.instruments.items())]
        return "\n".join(lines)


def _short(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _labels(path, key):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {r[key]: r for r in csv.DictReader(f)}


_TREE = None


def load():
    global _TREE
    if _TREE is None:
        newer = any(os.path.exists(os.path.join(config.TREE_DIR, f)) for f in ("tree_v3.json", "tree_v2.json"))
        _TREE = TreeV2() if newer else Tree()
    return _TREE
