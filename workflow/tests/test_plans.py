"""Step 0: every document carries its own period, and only a complete entry runs.

WHAT THIS ASSERTS
    The plan_id carries the period; a sector plan's title keeps two plans of one period apart;
    a skipped or period-less document never runs and says why; a skipped duplicate never
    shadows the edition it duplicates; the pilot configs give every runnable plan a unique id.

WHAT IT IS BLIND TO
    Whether a period in a config is right. The screener's reading of the document is the check
    on that, and C writes any disagreement into the context file's period_note.
"""
import os

import pytest

from pvii import config, plans as P


@pytest.mark.unit
def test_the_plan_id_carries_the_period(configs):
    ids = [p.plan_id for p in P.load_country("testland")]
    assert ids[:2] == ["testland_ndp_2017-2021", "testland_ndp_2022-2026"]
    assert ids[2] == "testland_sector_2022-2026_health-plan"


@pytest.mark.unit
def test_incomplete_and_skipped_documents_do_not_run_and_say_why(configs):
    ps = {p.title: p for p in P.load_country("testland")}
    assert "unidentified" in ps["mystery"].why_not_runnable()
    assert "period" in ps["Open Plan"].why_not_runnable()
    assert ps["Open Plan"].plan_id == ""
    assert [p.title for p in P.runnable("testland")] == ["Second Plan", "Third Plan", "Health Plan"]
    assert [p.title for p in P.runnable("testland", ("sector",))] == ["Health Plan"]


@pytest.mark.unit
def test_every_row_carries_the_plan_columns(configs):
    row = P.find("testland_ndp_2022-2026").row()
    assert row["period_start"] == 2022 and row["period_end"] == 2026
    assert row["doc_type"] == "ndp" and row["country"] == "Testland"


@pytest.mark.unit
def test_a_skipped_duplicate_never_shadows_its_edition():
    p = P.find("china_ndp_2021-2025", config.CONFIGS_DIR)
    assert p.language == "en" and not p.why_not_runnable()


@pytest.mark.unit
@pytest.mark.parametrize("slug", ["thailand", "china", "india"])
def test_pilot_configs_give_each_runnable_plan_a_unique_id(slug):
    ps = P.runnable(slug, configs_dir=config.CONFIGS_DIR)
    ids = [p.plan_id for p in ps]
    assert ids and len(ids) == len(set(ids))
    for p in P.load_country(slug, config.CONFIGS_DIR):
        assert p.doc_type and p.language, p.file
        assert p.file.startswith("data/sources/%s/" % slug), p.file


@pytest.mark.unit
def test_the_pilot_plan_is_runnable():
    p = P.find("thailand_ndp_2023-2027", config.CONFIGS_DIR)
    assert p.title.startswith("13th") and not p.why_not_runnable()
