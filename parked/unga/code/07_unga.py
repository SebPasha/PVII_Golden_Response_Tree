#!/usr/bin/env python3
"""The UNGA statement layer: pull the transcripts, stage 8 through Document Intelligence, publish.

    python3 runbook/07_unga.py --country india                     # held? published?
    python3 runbook/07_unga.py --country india --fetch             # transcripts from the bucket
    python3 runbook/07_unga.py --country india --extract --dry-run # price it, spend nothing
    python3 runbook/07_unga.py --country india --fetch --extract --publish
    python3 runbook/07_unga.py --all --fetch --extract --publish --yes

WHAT THE LAYER IS
Each September a head of state, head of government or foreign minister addresses the General
Debate. Stage 8 reads each statement whole and records, for all 11 structural risks and all 15
HDI categories, what that government told the Assembly, quoted, with the page. Same
vocabularies and salience bands as the plan's grid and the sector grid, so the three sit side
by side. Nothing here holds an amount.

WHAT HAPPENS, IN ORDER, PER COUNTRY
    fetch     support/platform/fetch.py --from-bucket --type unga --sync-config: the
              transcripts from pv2-sources into data/sources/<slug>/unga/, and documents.unga
              in the country config rewritten from what is on disk.
    extract   pv2.extract.run --stages 8: every statement parsed by Azure Document
              Intelligence, then one model call each. Opt-in: stage 8 is not in ALL_STAGES,
              so a default run never pays for it. Only where the outputs are missing, unless
              --force. Without --dry-run this spends, so it needs --country or --yes.
    publish   pv2.publish.unga: the layer into its own tables (migration 0018), keyed by a
              hash of the workbook.

EXIT CODE
    0  every country asked is held (and published, if asked)
    1  a step failed, or nothing is held and nothing was asked for
    2  a step could not run
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # PV2/
WORKFLOW = os.path.join(HERE, "workflow")
PLATFORM = os.path.join(HERE, "support", "platform")
for p in (PLATFORM, WORKFLOW):
    if p not in sys.path:
        sys.path.insert(0, p)
import runlog                                              # noqa: E402
from pv2 import country                                    # noqa: E402
from pv2.extract import stages                             # noqa: E402

SCRIPT = "07_unga"
VERDICT = {0: "PASS", 1: "FAIL", 2: "COULD NOT RUN"}


def registered():
    """Countries with UNGA transcripts in the register, which is what --all fetches."""
    from pv2.publish import db
    rows = db.connect().select_all("source_documents", {
        "select": "country_slug", "doc_type": "eq.unga", "order": "country_slug.asc"})
    return sorted({r["country_slug"] for r in rows})


def held_path(cfg):
    return stages.unga_path(cfg.out("stages"), cfg.slug)


def estimate(lines):
    model = pages = ""
    for line in lines:
        m = re.search(r"Estimated total: \$([\d.]+)", line)
        if m:
            model = "$%s model" % m.group(1)
        m = re.search(r"would parse (\d+) page\(s\) at about \$([\d.]+)", line)
        if m:
            pages = "$%s for %s page(s)" % (m.group(2), m.group(1))
    return ", ".join(x for x in (model, pages) if x) or "no estimate printed"


def main(argv, log):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", action="append", default=[], help="slug; repeatable")
    ap.add_argument("--all", action="store_true", help="every country with registered transcripts")
    ap.add_argument("--fetch", action="store_true", help="pull the transcripts and sync the config")
    ap.add_argument("--extract", action="store_true", help="run stage 8 where missing (spends)")
    ap.add_argument("--force", action="store_true", help="with --extract: redo held outputs")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --extract: price it; with --publish: write the payload only")
    ap.add_argument("--yes", action="store_true", help="with --extract and --all: yes, spend")
    ap.add_argument("--max-cost", type=float, help="with --extract: the cap per country, USD")
    ap.add_argument("--publish", action="store_true", help="load the held layers into Supabase")
    a = ap.parse_args(argv)

    if a.all:
        slugs = registered()
    elif a.country:
        slugs = a.country
    else:
        slugs = [s for s in country.all_slugs() if (country.load(s) or {}) and country.load(s).unga]
    missing = [s for s in slugs if not country.load(s)]
    if missing:
        log.say("  no country config for %s: they cannot be read or published "
                "(the countries table has no row for them either, see W136)" % ", ".join(missing))
        slugs = [s for s in slugs if s not in missing]
    if a.extract and not a.dry_run and a.all and not a.yes:
        ap.error("--extract --all spends on every country not yet held; pass --yes")

    rows, worst = [], 0
    for s in slugs:
        fetched = est = pub = ""
        if a.fetch:
            rc = log.step([os.path.join(PLATFORM, "fetch.py"), "--country", s, "--from-bucket",
                           "--type", "unga", "--sync-config"])
            fetched = VERDICT.get(rc, "exit %d" % rc)
            worst = max(worst, rc)
        cfg = country.load(s)
        held = os.path.exists(held_path(cfg))
        if a.extract and cfg.unga and (not held or a.force):
            rc = log.step(["-m", "pv2.extract.run", "--country", s, "--stages", "8",
                           "--no-panel", "--no-screen", "--yes"]
                          + (["--dry-run"] if a.dry_run else [])
                          + (["--force"] if a.force else [])
                          + (["--max-cost", str(a.max_cost)] if a.max_cost else []))
            if a.dry_run:
                est = estimate(log.last) if rc == 0 else "could not price (exit %d)" % rc
            elif rc:
                worst = max(worst, 1)
                est = "extraction stopped (exit %d)" % rc
            held = os.path.exists(held_path(cfg))
        if a.publish and held:
            rc = log.step(["-m", "pv2.publish.unga", "--country", s]
                          + (["--dry-run"] if a.dry_run else []))
            pub = ("payload written" if a.dry_run else "published") if rc == 0 \
                else VERDICT.get(rc, "exit %d" % rc)
            worst = max(worst, rc)
        rows.append((s, len(cfg.unga), fetched, "yes" if held else "no", pub, est))

    log.say("")
    log.say("  %-18s %5s  %-8s %-5s %-16s %s"
            % ("country", "files", "fetched", "held", "published", "estimate"))
    for r in rows:
        log.say("  %-18s %5d  %-8s %-5s %-16s %s" % r)
    n_held = sum(1 for r in rows if r[3] == "yes")
    if worst == 0 and (n_held or a.dry_run or (a.fetch and not a.extract)):
        log.say("RESULT: PASS - %d of %d country/countries held" % (n_held, len(rows)))
        return 0
    if worst == 0:
        log.say("FAILED - no country holds stage 8 outputs; run with --extract", err=True)
        return 1
    log.say("%s - see the rows above" % VERDICT.get(worst, "FAILED"), err=True)
    return worst


if __name__ == "__main__":
    sys.exit(runlog.main(SCRIPT, main))
