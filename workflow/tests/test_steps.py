"""Steps C, E, F and M on one plan, each against a stand-in client.

WHAT THIS ASSERTS
    C: a context file that exists is never re-read; a level link with no quoted sentence is
       dropped; a period that disagrees with the register is written down, not hidden.
    E: only commitment and ongoing rows are kept, and the rest are written beside them; a risk
       outside the eleven is refused; related_risks keeps only the eleven; a target year gets
       its horizon; every quote is checked against its own paragraph.
    F: rows fold within the plan only; an id is used once; out-of-range ids are ignored; every
       row lands in exactly one strategy.
    M: the tree's depth rule. An existing objective keeps its node unless the strategy's own
       wording carries the mechanism's cue; a NEW objective claiming a mechanism without the
       cue is held at the family; an unknown node is a proposal; a missing answer is unmapped.

WHAT IT IS BLIND TO
    Whether the model's answers are right. That is the pilot's spot check on the Thai plan.
"""
import json
import os

import pytest

from pvii import io, plans as P, steps, tree as T
from conftest import FakeClient, FakeDoc, para


@pytest.fixture
def plan(configs):
    return P.find("testland_ndp_2022-2026")


def _context_answer(_prompt):
    return {"period": {"start": 2022, "end": 2026, "quote": "The Third Plan covers 2022 to 2026."},
            "structure": [{"level": "goal", "number": "1", "name": "Productive farms", "parent": ""},
                          {"level": "strategy", "number": "1.1", "name": "Mechanise",
                           "parent": "1", "parent_quote": ""}],
            "headline_targets": [], "risk_framing": {"summary": "Climate shocks.", "risks_named":
                                                     ["Climate Change"], "quotes": []},
            "vocabulary": [{"term": "BCG", "gloss": "bio-circular-green economy"}]}


@pytest.mark.unit
def test_context_is_written_once_and_never_overwritten(plan, data, tmp_path):
    doc = FakeDoc([para(1, "The Third Plan covers 2022 to 2026. Farms will be mechanised.")])
    out = str(tmp_path / "out")
    os.makedirs(out)
    c = FakeClient({"C": _context_answer})
    ctx = steps.context(c, plan, doc, out)
    assert ctx["structure"][1]["parent"] == "", "a link with no quoted sentence must be dropped"
    assert ctx["quote_checks"] == {"verbatim": 1}
    assert os.path.exists(os.path.join(out, "context.md"))
    edited = dict(ctx, vocabulary=[{"term": "edited", "gloss": "by hand"}])
    io.write_json(os.path.join(out, "context.json"), edited)
    c2 = FakeClient({"C": lambda p: pytest.fail("C must not be called again")})
    assert steps.context(c2, plan, doc, out)["vocabulary"][0]["term"] == "edited"


@pytest.mark.unit
def test_context_records_a_period_the_register_disagrees_with(plan, tmp_path):
    doc = FakeDoc([para(1, "This plan runs 2023 to 2027.")])
    ans = _context_answer(None)
    ans["period"] = {"start": 2023, "end": 2027, "quote": "This plan runs 2023 to 2027."}
    ctx = steps.context(FakeClient({"C": ans}), plan, doc, str(tmp_path))
    assert "2023-2027" in ctx["period_note"] and "2022-2026" in ctx["period_note"]


EXTRACT = {
    "section_type": "strategy",
    "risks": [{"risk": "Climate Change", "framing": "threat",
               "quote": "droughts threaten farm incomes", "quote_en": ""},
              {"risk": "Road Deaths", "framing": "threat", "quote": "x", "quote_en": ""}],
    "strategies": [
        {"statement_type": "commitment", "name": "Farm Mechanisation Programme",
         "objective": "Raise farm productivity", "target_group": "smallholder farmers",
         "instrument": "machinery subsidies", "pillar": "1.1",
         "related_risks": ["Climate Change", "Road Deaths"], "target_year": 2030,
         "target_year_quote": "by 2030", "place": "national",
         "quote": "The Government will subsidise machinery for smallholder farmers by 2030",
         "quote_en": ""},
        {"statement_type": "completed", "name": "Irrigation Canals", "objective": "Irrigate",
         "target_group": "", "instrument": "", "quote": "Canals were built in 2019."}]}

TEXT = ("Because droughts threaten farm incomes, the Government will subsidise machinery for "
        "smallholder farmers by 2030. Canals were built in 2019.")


@pytest.mark.unit
def test_extract_keeps_commitments_and_checks_every_quote(plan, tmp_path):
    doc = FakeDoc([para(1, TEXT, section="Agriculture")])
    r = steps.extract(FakeClient({"E": EXTRACT}), plan, doc, {}, str(tmp_path))
    assert [x["name"] for x in r["rows"]] == ["Farm Mechanisation Programme"]
    assert [x["statement_type"] for x in r["dropped"]] == ["completed"]
    row = r["rows"][0]
    assert row["related_risks"] == ["Climate Change"]
    assert row["horizon"] == "long" and row["target_year"] == 2030
    assert row["quote_check"] == "verbatim" and row["period_end"] == 2026
    assert [x["risk"] for x in r["risks"]] == ["Climate Change"]
    assert r["invalid"] and "Road Deaths" in r["invalid"][0][1]
    on_disk = io.read_csv(os.path.join(tmp_path, "strategy_rows.csv"))
    assert on_disk[0]["row_id"] == "testland_ndp_2022-2026#r1.1"
    assert os.path.exists(os.path.join(tmp_path, "strategy_rows_dropped.csv"))


@pytest.mark.unit
def test_extract_carries_the_context_into_every_call(plan, tmp_path):
    c = FakeClient({"E": {"section_type": "other", "risks": [], "strategies": []}})
    ctx = _context_answer(None)
    steps.extract(c, plan, FakeDoc([para(1, "a"), para(2, "b")]), ctx, str(tmp_path))
    assert len(c.prompts["E"]) == 2 and all("bio-circular-green" in p for p in c.prompts["E"])


def _rows(n, pillar="1"):
    return [{"row_id": "p#r%d.1" % i, "name": "Strategy %d" % i, "objective": "Objective %d" % i,
             "target_group": "", "instrument": "", "pillar": pillar, "ref": "ref %d" % i,
             "statement_type": "commitment" if i % 2 else "ongoing", "related_risks": [],
             "target_year": 2030 if i == 2 else None, "place": "", "quote": "q%d" % i,
             "quote_en": "", "quote_check": "verbatim"} for i in range(1, n + 1)]


@pytest.mark.unit
def test_fold_merges_within_the_plan_and_uses_each_row_once(plan, tmp_path):
    rows = _rows(4)
    ans = [{"merge_ids": [1, 2, 99], "name": "Merged", "objective": "Merged objective",
            "target_group": "farmers", "instrument": "loans"},
           {"merge_ids": [2, 3], "name": "Reuses row 2"}]
    out, _ = steps.fold(FakeClient({"F": ans}), plan, rows, str(tmp_path))
    assert [s["name"] for s in out] == ["Merged", "Strategy 3", "Strategy 4"]
    merged = out[0]
    assert merged["members"] == ["p#r1.1", "p#r2.1"] and merged["n_mentions"] == 2
    assert merged["statement_type"] == "commitment" and merged["target_year"] == 2030
    assert sorted(m for s in out for m in s["members"]) == sorted(r["row_id"] for r in rows)
    assert merged["strategy_id"] == "testland_ndp_2022-2026#s1"


@pytest.mark.unit
def test_shards_follow_the_pillar_and_respect_the_cap():
    rows = _rows(130, pillar="2") + _rows(3, pillar="")
    sizes = [len(s) for s in steps.shards(rows)]
    assert max(sizes) <= steps.FOLD_SHARD_MAX and sum(sizes) == 133


def _strategy(name, quote_en=""):
    return {"strategy_id": "s", "name": name, "objective": name, "target_group": "MSMEs",
            "instrument": "loans", "quote": "", "quote_en": quote_en, "plan_id": "p"}


@pytest.mark.unit
def test_map_follows_the_trees_depth_rule():
    t = T.load()
    s = steps.resolve(_strategy("Modernise farming"), {"objective_id": "O0006",
                                                       "node_id": "L2-33"}, t)
    assert (s["relation"], s["node_id"], s["level"]) == ("same", "L2-33", "L2")

    s = steps.resolve(_strategy("Subsidise tractors and farm machinery"),
                      {"objective_id": "O0006", "node_id": "L3-162"}, t)
    assert (s["node_id"], s["depth_basis"]) == ("L3-162", "deepened by strategy wording")

    s = steps.resolve(_strategy("Support farmers"), {"objective_id": "O0006",
                                                     "node_id": "L3-162"}, t)
    assert s["node_id"] == "L2-33" and "refused" in s["map_note"]

    s = steps.resolve(_strategy("Support farmers"), {"objective_id": "NEW", "node_id": "L3-162",
                                                     "new_objective": "Support farmers"}, t)
    assert (s["relation"], s["node_id"]) == ("differs", "L2-33")

    s = steps.resolve(_strategy("Something else"), {"objective_id": "NEW", "node_id": "L9-999"}, t)
    assert (s["relation"], s["node_id"]) == ("new", "") and s["proposal"]

    s = steps.resolve(_strategy("Unanswered"), None, t)
    assert s["relation"] == "unmapped"


@pytest.mark.unit
def test_map_normalises_target_and_instrument_and_writes_proposals(plan, tmp_path):
    t = T.load()
    strategies = [_strategy("Credit for small firms"), _strategy("Odd one")]
    ans = [{"id": 1, "objective_id": "O0006", "node_id": "L2-33", "target_id": "T0007",
            "instrument_id": "I0001", "confidence": "high"},
           {"id": 2, "objective_id": "NEW", "node_id": "", "new_objective": "Do odd things",
            "proposal": "a node for odd things"}]
    out, props, _ = steps.map_to_tree(FakeClient({"M": ans}), plan, strategies, {}, t, str(tmp_path))
    assert (out[0]["target_label"], out[0]["instrument_label"]) == ("MSMEs", "Loan or guarantee")
    assert out[0]["tree_version"].startswith("mother tree v1")
    assert [p["proposal"] for p in props] == ["a node for odd things"]
    assert io.read_csv(os.path.join(tmp_path, "proposals.csv"))[0]["relation"] == "new"


@pytest.mark.unit
def test_the_tree_menu_names_every_node_once():
    t = T.load()
    menu = t.menu()
    for nid in list(t.families) + list(t.mechanisms) + list(t.holding):
        assert menu.count(nid + " ") >= 1, nid
    assert len(menu) < 120000, "the menu is sent with every M call; keep it near 20k tokens"
