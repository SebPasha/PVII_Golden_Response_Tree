"""Two editions of one country, end to end, then stacked into the country and the globe.

WHAT THIS ASSERTS
    run_plan writes every plan file; step E's guards hold (a risk or a proactive or
    transformative score whose quote is not in the paragraph is dropped, an unofficial SDG
    target is dropped, an out-of-list value is clamped) and its fields reach strategies.csv;
    stacking loses no row from plan to country to global;
    every row keeps its plan's period; the edition table finds the node carried from the
    second plan to the third, the one dropped and the one new; a dry run writes nothing.

WHAT IT IS BLIND TO
    The parse (a stand-in document) and the model (a stand-in client).
"""
import os

import pytest

from pvii import config, io, parse, plans as P, run, stack
from conftest import FakeClient, FakeDoc, para

CONTEXT = {"period": {}, "structure": [], "headline_targets": [], "risk_framing": {},
           "vocabulary": []}


def _extract(names):
    def answer(prompt):
        chunk = prompt.rsplit("Heading:", 1)[1]
        for n in names:
            if n.lower() in chunk.lower():
                return {"section_type": "strategy",
                        "risks": [{"risk": "Climate Change", "framing": "threat",
                                   "quote": n, "quote_en": ""}],
                        "strategies": [{"statement_type": "commitment", "name": n,
                                        "objective": n, "target_group": "", "instrument": "",
                                        "quote": n, "quote_en": "",
                                        "related_risks": ["Climate Change", "Pandemics"],
                                        "risk_evidence": [n, "words from another page"],
                                        "RHDRCategory": "domestic integration",
                                        "response_orientation": "transformative",
                                        "response_evidence": n if n != "Digitise services"
                                        else "words from another page",
                                        "sdg_targets": ["2.3", "99.9"], "stated_urgency": "HIGH",
                                        "sector": "Agriculture", "implementation_status": "planned",
                                        "has_timeline": "Y", "has_quantified_target": "yes",
                                        "legal_or_plan_basis": "decree"}]}
        return {"section_type": "other", "risks": [], "strategies": []}
    return answer


def _map(objective_for):
    def answer(prompt):
        lines = prompt.rsplit("STRATEGIES\n", 1)[1].strip().splitlines()
        out = []
        for line in lines:
            i, name = line.split(" | ")[:2]
            out.append({"id": int(i), "objective_id": objective_for[name], "node_id": ""})
        return out
    return answer


@pytest.fixture
def world(configs, data, tmp_path, monkeypatch):
    src = tmp_path / "sources"
    monkeypatch.setattr(config, "SOURCES_ROOT", str(src))
    for f in ("plan_a.pdf", "plan_b.pdf"):
        (src / "sources" / "testland").mkdir(parents=True, exist_ok=True)
        (src / "sources" / "testland" / f).write_text("pdf")
    docs = {"plan_a.pdf": FakeDoc([para(1, "Mechanise farming"), para(2, "Digitise services")]),
            "plan_b.pdf": FakeDoc([para(1, "Mechanise farming"), para(2, "Protect fisheries"),
                                   para(3, "Background only")])}
    monkeypatch.setattr(parse, "parse_document", lambda path, **_: docs[os.path.basename(path)])
    return docs


OBJ = {"Mechanise farming": "O0006", "Digitise services": "M02", "Protect fisheries": "O0004"}


@pytest.mark.contract
def test_two_editions_stack_without_loss_and_show_what_carried(world, data):
    client = FakeClient({"C": CONTEXT, "E": _extract(list(OBJ)), "F": [], "M": _map(OBJ)})
    for pid in ("testland_ndp_2017-2021", "testland_ndp_2022-2026"):
        run.run_plan(P.find(pid), client)
        d = P.plan_dir(pid)
        for f in ("context.json", "context.md", "risks.csv", "strategy_rows.csv",
                  "strategies.csv", "proposals.csv", "run.json", "cost_report.md"):
            assert os.path.exists(os.path.join(d, f)), f
    s = {r["name"]: r for r in io.read_csv(os.path.join(
        P.plan_dir("testland_ndp_2017-2021"), "strategies.csv"))}
    farm, digi = s["Mechanise farming"], s["Digitise services"]
    assert io.as_list(farm["related_risks"]) == ["Climate Change"]
    assert io.as_list(farm["risk_evidence"]) == ["Mechanise farming"]
    assert (farm["response_orientation"], digi["response_orientation"]) == ("transformative", "BAU")
    assert digi["response_evidence"] == ""
    assert (farm["RHDRCategory"], farm["rhdr_pillar"]) == ("Domestic Integration", "Smarter Growth")
    assert io.as_list(farm["sdg_targets"]) == ["2.3"] and farm["sdg_primary_dimension"]
    assert (farm["stated_urgency"], farm["legal_or_plan_basis"]) == ("high", "none")
    assert farm["tree_rhdr"]
    guards = io.read_json(os.path.join(P.plan_dir("testland_ndp_2017-2021"), "run.json"))[
        "extract"]["guards"]
    assert guards == {"risk dropped: no quote found": 2, "SDG target not official": 2,
                      "response set to BAU: no quote found": 1}
    c = stack.stack_country("testland")
    assert len(c["strategies"]) == 2 + 2 and len(c["risks"]) == 4
    assert {s["period_start"] for s in c["strategies"]} == {"2017", "2022"}
    status = {(e["node_id"], e["status"]) for e in c["editions"]}
    assert ("L2-33", "carried") in status
    assert ("L3-227", "dropped") in status and ("L3-074", "new") in status
    runs = {p["plan_id"]: p["status"] for p in c["plans"]}
    assert runs["testland_ndp_2017-2021"] == "run"
    assert runs["testland_sector_2022-2026_health-plan"] == "not run"
    g = stack.stack_global(["testland"])
    assert len(g["strategies"]) == 4
    assert sum(int(r["n_strategies"]) for r in g["coverage"]) == 4
    assert io.read_csv(os.path.join(stack.global_dir(), "editions.csv"))


@pytest.mark.contract
def test_a_dry_run_writes_nothing(world, data):
    client = FakeClient({"C": None, "E": None, "F": None, "M": None}, dry_run=True)
    run.run_plan(P.find("testland_ndp_2017-2021"), client)
    d = P.plan_dir("testland_ndp_2017-2021")
    assert not [f for f in os.listdir(d) if f.endswith((".csv", ".json"))]
