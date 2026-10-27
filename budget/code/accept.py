#!/usr/bin/env python3
"""
Is this stage 5 year fit to be mapped? Six rules, run when it is written and offline after.

    python3 -m pv2.extract.accept --country thailand
    python3 -m pv2.extract.accept --all           # every configured country
    python3 -m pv2.extract.accept --workbook data/llm/fiji/fiji_budget_2025.xlsx

WHY THIS EXISTS
Of 172 budget document-years held, 464 of 1,657 head-years (28%) carry programme rows that
exceed their own head, and 15 doc-years are out by a clean factor of a thousand. Nothing
stopped any of them: reconciliation ran, wrote its problems into a list called errors_all
that nothing ever read, and the year went on to be classified, mapped and published like any
other. Everything downstream of stage 5 is paid for per row, so a year that cannot be right
costs money twice, once to extract and once to map.

WHAT IT REFUSES, AND WHAT IT ONLY RECORDS (10 September 2026)
Two rejections and no others, decided after 103 of 116 held
workbooks were refused: a year with NO PRICED PROGRAMME ROW at all, which nothing downstream
can map and which bills 5b, 4, 6 and 6b for an empty list, and a year whose programme rows are
outside 0.2 to 5 times the total the document prints, which is a scale that cannot be repaired
by reading the same book again. EVERYTHING ELSE IS A FINDING: heads that do not sum to the
grand total, programmes that exceed or fall short of their head, a scale mixture nothing
declares, a fiscal year the document does not print, and coverage outside 0.90 to 1.05. A
finding leaves the workbook on the live path and writes its sentences beside it as
<name>.findings.txt, and the run report and errors.json name the year.

The reason for the asymmetry is what each one costs. A year wrongly refused is a country-year
missing from the panel and a re-extraction to get it back; a year wrongly kept is a row in a
table with a findings file beside it, held out of cross-country comparison by
calcs.comparability and the 0.90 coverage floor, which is where incompleteness already
belongs. The price is that a genuine double count now publishes: Thailand FY2024 reads its
book's ministry view on top of its strategy view at 141% of the printed total, and under these
rules it is kept with findings rather than refused.

ONE SCALE FIRST
Rules 2, 3 and 5 compare amounts converted to whole currency by pv2.scale.scale_of_row, the
same conversion the union applies. Brunei prints its grand total as 6.35 "BND billion" over
heads in "BND million", and judging the printed figures reported that as "7 head totals sum to
1,017.5 but the grand total is 6.3", a 160-fold mismatch that is one scale change. What is
left after the conversion is the real gap.

THE RULES, AND WHAT EACH ONE CATCHES
  1 at least one PRICED programme    REJECTS. A workbook of ministry totals and no programme line can
    row                              be mapped to nothing, and 5b, 4, 6 and 6b are billed for
                                    it anyway (11 doc-years). Priced, because sri_lanka 2022
                                    returned all 49 of its amounts as prose ("Rs. 4,000
                                    million"), which every arithmetic rule skips row by row
                                    and which therefore passed all six
  2 heads sum to the grand total    FINDING. The anchor the extraction did not derive from its
                                    own rows, where the document prints one
  3 programmes sum to their head    FINDING. The 28%: a head whose parts exceed it has picked
                                    up rows from another partition of the same book
  4 the rows resolve to one scale   FINDING. A row whose scale nothing declares, beside rows whose
                                    scale is declared, cannot be converted and cannot be
                                    added: the Maldives prints 18 rows labelled "MVR million"
                                    beside 253 labelled "MVR", a factor of about 25,000 inside
                                    one workbook. Two DECLARED scales are not a mixture, they
                                    are a conversion
  5 within 0.90 to 1.05 of the      FINDING inside 0.2 to 5, REJECTS outside it. The only
    screener's printed total        rule whose anchor is outside the extraction altogether:
                                    the text layer's own read of the total, itself often
                                    misread, which is why the refusal band is so much wider
                                    than the finding band
  6 the year is a year the          FINDING. A book whose comparative columns were extracted
    document prints                 instead of its own year

Rules 2 and 3 are schemas.reconcile_stage5, so the arithmetic is written once and the
prompts, the offline sweep and the acceptance gate cannot drift apart on it. The rows a
country records in vocab/patches.json as a line the book does not present as a programme are
dropped before the arithmetic, exactly as the union drops them: Thailand's FY2026 book prints
three budget units under Strategy 6 and judging the raw sheet refused the year for 36,541.7
that no later table carries (W113).

WHAT IT IS NOT
Not a check on the numbers themselves. A year can pass all six and still be a careful
extraction of the wrong table: that is what validate.fidelity and validate.recall are for,
and they need the source document, which this deliberately does not.

A rule whose input is missing is NOT CHECKED and is reported as such, never as a pass. Four
of the six can be suspended: two rest on the screener having profiled the document, and two
on the extraction having produced a grand total and a head total to compare against. A
year-file the config names and this machine does not hold is reported the same way, in
neither the numerator nor the denominator of the accepted count: 36 of the 137 year-files the
configs name are absent, and "7 of 101 accepted" was a statement about 101 of 137.

EXIT CODE
    0  every year judged was accepted with nothing to report
    1  at least one year was rejected, or accepted with findings
    2  could not run (no such country, no workbook, nothing to judge)

A finding exits 1 as a rejection does. The exit code answers "is every year judged clean",
which is the question the negative controls in pv2.validate.tamper ask of this gate: three of
the four defects they inject (an inflated head total, a missing chunk, one row relabelled at
another scale) land as findings under D19, and an exit code blind to a finding would report
those three gates as blind. What the code does NOT say is where the workbook went; the RESULT
line and the verdict column say that.
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import sys

from pv2 import config_patches as patches
from pv2 import country, scale
from pv2.extract import config, schemas, writer

# The band the extracted programme rows are REPORTED against: outside it the year carries a
# finding, and it is refused only outside the far wider ABSURD band below. Wider below than
# above because an extraction that missed a section is a known and visible failure, while one
# that exceeds the printed total is double counting, which is not. Declared once, here, and
# imported by pv2.calcs.calcs, which applies the same band to a country-year's share against
# its own denominator: the two ratios are different quantities and share a band on purpose,
# so they are one number rather than two that agree today.
COVERAGE_FLOOR, COVERAGE_CEILING = 0.90, 1.05
REJECTED_DIR = "rejected"                       # under data/llm/<slug>/
REASONS_SUFFIX = ".reasons.txt"
FINDINGS_SUFFIX = ".findings.txt"

# The multipliers the screener's printed total might be on. It records a bare number read off
# a line ("Total expenditure 6,193.6") with no unit beside it, while the rows have just been
# converted to whole currency, so the two are on unknown relative scales and Rwanda read as
# 91,871,355,564% of its own budget. Powers of a thousand, plus whatever scale the rows
# themselves declare, because the total is printed on the same pages as the rows: `lakh` and
# `crore` are a factor of ten from `million` and `crore` from `billion`, so admitting the
# whole vocabulary unconditionally would let a sixfold over-extraction pass as a 0.6 under.
# See _aligned.
PRINTED_SCALES = (1.0, 1e3, 1e6, 1e9, 1e12)

# Outside this, and only outside this, the programme rows against the printed total are a
# rejection. 0.2 to 5 is not a tolerance, it is the point past which no reading of the same
# book fixes the answer: a factor of five is beyond any partition of a budget and the next
# scale word up is a factor of a thousand away, so nothing between 0.2 and 5 is a scale error
# and everything outside it is either that or a table read from another document.
ABSURD_LOW, ABSURD_HIGH = 0.2, 5.0


def in_one_scale(rows):
    """(rows with every amount in whole currency, the rule 4 rejection or None).

    Copies, never the caller's rows: judging a year must not change the workbook the caller is
    about to write. A row whose scale nothing declares is left as it stands, which is right
    only when no row declares one; where some do, the file cannot be resolved and rule 4 says
    so instead.
    """
    out, resolved, bare = [], {}, 0
    for r in rows:
        amount = schemas._num(r.get("amount"))
        word, value = scale.scale_of_row(r)
        if amount is not None:
            if word:
                resolved.setdefault(word, str(r.get("currency_unit") or "").strip() or word)
            else:
                bare += 1
        out.append(dict(r, amount=amount * value) if amount is not None and value else r)
    named = {w: la for w, la in resolved.items() if w != "unit"}
    if bare and named:
        return out, ("%d priced row(s) declare no scale, beside row(s) declaring %s, so the "
                     "file cannot be resolved to one scale"
                     % (bare, "; ".join("%s (%s)" % (w, la) for w, la in sorted(named.items()))))
    return out, None


def _aligned(got, printed, declared=()):
    """(the printed total on the scale that best matches `got`, the multiplier used).

    The candidates are three orders of magnitude apart, so a real over- or under-extraction
    stays where it is (1.41 stays 1.41; the alternatives are 1,410 and 0.00141) and a pure
    scale difference collapses to about 1. `declared` adds the multipliers the rows themselves
    name, which is how an Indian book printing its total in crore is matched at all.

    Three things this cannot see, and each is somebody else's gate. A whole-file error of one
    vocabulary factor: L4 totals. A ratio of about ten where the rows declare lakh or crore,
    since those sit a factor of ten from million and billion: nothing, and it is the price of
    reading Indian books at all. And it never scales the anchor DOWN, so a screener that read
    "1,949,381,651,743 100%" as one number (Rwanda FY2017) leaves the year at 0% coverage,
    which is a finding and not a refusal, which is where an unusable anchor belongs.
    """
    candidates = set(PRINTED_SCALES) | {m for m in declared if m}
    best = min(sorted(candidates), key=lambda m: abs(math.log(printed * m / got)))
    return printed * best, best


def judge(rows, printed_total=None, fy_labels=None, exclude=None):
    """(rejections, findings, not_checked) for one year's rows. All three empty means clean.

    A rejection puts the workbook where nothing downstream reads it, and there are two of
    them: no priced programme row, and a programme sum outside ABSURD_LOW to ABSURD_HIGH of
    the printed total. Everything else is a finding, written beside a workbook that stays on
    the live path. See the D19 paragraph at the top of this module for why.

    printed_total is the screener's own read of the document's grand total, and fy_labels the
    fiscal years it prints, as (start, end) pairs. Either being None means the document was
    never profiled, which suspends the rule that rests on it rather than passing it.
    `exclude` is {(fiscal_year, program_code)} the country records in vocab/patches.json as a
    row the book does not present as a programme.
    """
    rejections, findings, not_checked = [], [], []
    exclude = exclude or set()

    # Rule 4 first, because it decides whether the arithmetic below is arithmetic at all. It
    # is a finding and not a rejection: where the mixture does real damage the programme sum
    # lands outside the absurd band and rule 5 refuses the year on the money.
    rows, mixture = in_one_scale(rows)
    if mixture:
        findings.append("two scales in one file: " + mixture)

    programmes = [r for r in rows
                  if str(r.get("line_type") or "") == "program"
                  and (str(r.get("fiscal_year") or ""),
                       str(r.get("program_code") or "").strip()) not in exclude]
    priced = [r for r in programmes if schemas._num(r.get("amount")) is not None]
    if not programmes:
        rejections.append("no programme row: %d row(s), none of them a programme line"
                          % len(rows))
    elif not priced:
        # 100% unparseable is a fact about the extraction, not an absence of data. Every
        # arithmetic rule below skips a row whose amount does not parse, so a year whose
        # amounts all came back as prose closes every sum vacuously and is accepted.
        rejections.append("no programme row carries an amount that parses: %d programme "
                          "row(s), the first reading %r"
                          % (len(programmes), str(programmes[0].get("amount"))[:40]))

    problems, suspended = schemas.reconcile_stage5(rows, exclude)
    findings += [str(pr) for pr in problems]
    not_checked += suspended

    # Rule 5, the one anchor outside the extraction altogether.
    got = sum(schemas._num(r.get("amount")) or 0.0 for r in programmes)
    if printed_total in (None, "", 0):
        not_checked.append("the screener read no printed total for this document")
    elif not got:
        not_checked.append("the programme rows carry no amount to compare with the total")
    else:
        declared = {scale.scale_of_row(r)[1] for r in programmes}
        want, factor = _aligned(got, float(printed_total), declared)
        ratio = got / want
        said = ("the programme rows are %.0f%% of the total the document prints (%s against "
                "%s%s)" % (100 * ratio, format(got, ",.1f"), format(want, ",.1f"),
                           "" if factor == 1.0 else
                           " read at %s, the scale that fits it best" % format(factor, ",.0f")))
        if not ABSURD_LOW <= ratio <= ABSURD_HIGH:
            rejections.append(said + ", which no second reading of this book can repair")
        elif not COVERAGE_FLOOR <= ratio <= COVERAGE_CEILING:
            findings.append(said)

    years = {str(r.get("fiscal_year") or "").strip() for r in rows}
    years.discard("")
    if not fy_labels:
        not_checked.append("the screener read no fiscal year off this document")
    else:
        printed = {str(y) for pair in fy_labels for y in pair}
        stray = sorted(y for y in years if y not in printed)
        if stray:
            findings.append("fiscal year %s is not a year this document prints (it prints "
                            "%s)" % (", ".join(stray), ", ".join(sorted(printed))))
    return rejections, findings, not_checked


def year_of(filename):
    """The fiscal year in a stage workbook's name, or None."""
    m = re.search(r"_(\d{4})\.xlsx$", filename)
    return m.group(1) if m else None


def retire_derived(out_dir, year):
    """Move the mapping and coverage workbooks for a rejected year out of mappings/.

    Stage 6 and 6b write one workbook per year from that year's budget rows. When the year is
    then rejected its budget workbook moves to rejected/, but the mappings it produced stayed
    in mappings/, describing money no longer on the live path. Nothing downstream read them,
    because union keys off the budget rows, so no published figure was ever wrong. What they
    did do is sit in the currency audit for ever: stage 6 only runs for years that HAVE a
    budget, so a mapping whose year has none can never be re-made and can never stop being
    reported as older than the prompt that would now produce it. Six countries carried twelve
    such files on 10 September 2026, against 57 stale outputs in 15 countries at that hour, so
    about a fifth of what the gate was failing on and none of it reachable by spending. This
    fires on a fresh rejection only; the twelve already on disk were retired by a one-off pass
    the same day.
    """
    src = os.path.join(out_dir, "mappings")
    if not year or not os.path.isdir(src):
        return []
    dest = os.path.join(out_dir, REJECTED_DIR, "mappings")
    moved = []
    for p in sorted(glob.glob(os.path.join(src, "*_%s.xlsx" % year))):
        os.makedirs(dest, exist_ok=True)
        target = os.path.join(dest, os.path.basename(p))
        if os.path.exists(target):
            os.remove(target)
        os.replace(p, target)
        moved.append(target)
    return moved


def retire_programme_class(out_dir):
    """Retire <slug>_programme_class.xlsx once the country has no accepted budget year left.

    Stage 5b classifies the programmes of every year at once, so its output is a country-level
    file rather than a per-year one and `retire_derived` cannot reach it. A country whose every
    year is rejected keeps a classification of programmes that are no longer on the live path,
    and stage 5b can never rewrite it, because it has no budget rows to read: the same trap as
    the mappings, one level up. Kenya was in exactly that state on 10 September 2026 with all
    three of its years refused (W124).
    """
    slug = os.path.basename(os.path.normpath(out_dir))
    if glob.glob(os.path.join(out_dir, "%s_budget_*.xlsx" % slug)):
        return []                                  # a year survives; 5b is rebuilt, not retired
    src = os.path.join(out_dir, "%s_programme_class.xlsx" % slug)
    if not os.path.exists(src):
        return []
    dest_dir = os.path.join(out_dir, REJECTED_DIR)
    os.makedirs(dest_dir, exist_ok=True)
    target = os.path.join(dest_dir, os.path.basename(src))
    if os.path.exists(target):
        os.remove(target)
    os.replace(src, target)
    return [target]


def write_rejected(out_dir, filename, rows, columns, reasons):
    """Put a rejected year where nothing downstream looks, with the reasons beside it.

    Never into the country's own folder: _budget_rows_from_files, write_country_config and
    the union's budget_year_files all read a year by the name of its workbook, so a rejected
    year left there is mapped, classified and published exactly like an accepted one. The
    mappings an earlier run already built from it go the same way, for the reason
    `retire_derived` gives.
    """
    dest_dir = os.path.join(out_dir, REJECTED_DIR)
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, filename)
    writer.write_results(path, rows, columns)
    retire_derived(out_dir, year_of(filename))
    retire_programme_class(out_dir)
    with open(path + REASONS_SUFFIX, "w", encoding="utf-8") as f:
        f.write("%s was not accepted:\n\n" % filename)
        for r in reasons:
            f.write("  - %s\n" % r)
        f.write("\nRe-extract the year, or fix what the reasons name. Nothing downstream "
                "reads this folder.\n")
    return path


def write_findings(out_dir, filename, findings):
    """Record what is wrong with a year that is KEPT, beside the year itself.

    Same shape as the reasons file so `rejected_years` and `findings_years` read one format,
    and in the country's own folder rather than rejected/ because the workbook it describes is
    on the live path and a finding that travels away from its workbook is a finding nobody
    reads. Returns the path, or None where there is nothing to record (and clears any file an
    earlier run left, which is the fault `clear_rejection` exists for, one suffix over).
    """
    path = os.path.join(out_dir, filename + FINDINGS_SUFFIX)
    if not findings:
        if os.path.exists(path):
            os.remove(path)
        return None
    os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("%s was accepted with findings:\n\n" % filename)
        for r in findings:
            f.write("  - %s\n" % r)
        f.write("\nThe year is on the live path and its own tables carry it. Every finding "
                "above is a sum that falls SHORT of what it is measured against, which is "
                "incompleteness: calcs.comparability and the %.2f coverage floor are what "
                "keep an incomplete year out of cross-country comparison.\n" % COVERAGE_FLOOR)
    return path


SUPERSEDED_SUFFIX = ".superseded"


def retire_superseded(out_dir, filename):
    """Move the accepted year this refused one replaces off the live path, keeping the bytes.

    Returns the path it was moved to, or None where there was nothing there. Everything
    downstream reads a year by the name of its workbook, so the workbook a refusal leaves
    behind is served to 5b, 6, 6b, the union and the publisher exactly as an accepted year is.
    """
    live = os.path.join(out_dir, filename)
    if not os.path.exists(live):
        return None
    dest_dir = os.path.join(out_dir, REJECTED_DIR)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, filename + SUPERSEDED_SUFFIX)
    if os.path.exists(dest):
        os.remove(dest)
    os.replace(live, dest)
    return dest


def clear_rejection(out_dir, filename):
    """Drop the reasons file for a year this run has just accepted, if there is one."""
    reasons = os.path.join(out_dir, REJECTED_DIR, filename + REASONS_SUFFIX)
    if os.path.exists(reasons):
        os.remove(reasons)
        return reasons
    return None


def restore_rejected(out_dir, filename):
    """Put a workbook the gate now accepts back on the live path, keeping its findings file.

    The re-judge path (`--rejudge --restore`), not the run path: an extraction writes to the
    live path itself. Returns the path it was restored to, or None where there is nothing in
    rejected/ or something is already live under that name, which is a newer extraction and
    is not overwritten.
    """
    src_path = os.path.join(out_dir, REJECTED_DIR, filename)
    live = os.path.join(out_dir, filename)
    if not os.path.exists(src_path) or os.path.exists(live):
        return None
    os.replace(src_path, live)
    clear_rejection(out_dir, filename)
    return live


def _sidecar_years(directory, suffix):
    """[(fiscal year, [sentences])] from every <name><suffix> in one directory."""
    if not os.path.isdir(directory):
        return []
    out = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(suffix):
            continue
        year = name.split("_budget_")[-1].split(".")[0] if "_budget_" in name else name
        with open(os.path.join(directory, name), encoding="utf-8") as f:
            lines = [ln.strip()[2:] for ln in f if ln.strip().startswith("- ")]
        out.append((year, lines))
    return out


def rejected_years(out_dir):
    """[(fiscal year, [reasons])] a country holds, newest write last. The run report reads this."""
    return _sidecar_years(os.path.join(out_dir, REJECTED_DIR), REASONS_SUFFIX)


def findings_years(out_dir):
    """[(fiscal year, [findings])] a country holds on the LIVE path. The run report reads this."""
    return _sidecar_years(out_dir, FINDINGS_SUFFIX)


# ------------------------------------------------------------------ the offline sweep
def context(slug, cfg=None, out_dir=None):
    """{fiscal year: (printed total, fy labels)} from the screener's profile for one country.

    The pairing is the config's own: documents.budget says which file is which year, and the
    profile is keyed by file. A year the config does not name gets no context and its two
    document-side rules go unchecked rather than being judged against another year's page.
    """
    c = cfg or country.load(slug)
    if not c:
        return {}
    path = os.path.join(out_dir or os.path.join(config.FILES_DIR, "llm", slug),
                        "profile.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        profiles = json.load(f)
    by_file = {p.get("file"): p for p in profiles}
    out = {}
    for year, doc in (c.budget or {}).items():
        p = by_file.get(os.path.basename(doc))
        if not p:
            continue
        nt = p.get("national_total") or {}
        out[str(year)] = (nt.get("value"), p.get("fy_labels") or [])
    return out


def workbook_year(path):
    """The fiscal year a stage 5 workbook is named for, or ''."""
    base = os.path.basename(path)
    return base.split("_budget_")[-1].split(".")[0] if "_budget_" in base else ""


def judge_workbook(path, ctx=None, slug=None):
    """(year, rejections, findings, not_checked, rows) for one workbook on disk."""
    rows = writer.read_rows(path)
    year = workbook_year(path)
    printed, labels = (ctx or {}).get(year, (None, None))
    exclude = patches.excluded_budget_lines(slug) if slug else set()
    rejections, findings, not_checked = judge(rows, printed, labels, exclude)
    return year, rejections, findings, not_checked, rows


def judge_country(slug):
    """[(path, year, reasons, not_checked, rows)] for every year-file the config names.

    A year-file the config names and this machine does not hold is returned with rows None,
    which is neither an acceptance nor a rejection. Filtering it out silently made the RESULT
    line a statement about the files that happened to be there: 36 of the 137 named across the
    corpus are absent, five countries hold none of theirs at all and vanished entirely.
    """
    c = country.load(slug)
    if not c:
        return []
    ctx = context(slug, c)
    out = []
    for rel in (c.get("outputs") or {}).get("budget_year_files") or []:
        path = config.resolve(rel)
        if os.path.exists(path):
            out.append((path,) + judge_workbook(path, ctx, slug))
        else:
            out.append((path, workbook_year(path), [], [],
                        ["the year-file the config names is not on this machine, so no rule "
                         "ran over it"], None))
    return out


def rejudge_country(slug):
    """[(path, year, rejections, findings, not_checked, rows)] for the rejected folder.

    D19 changed what the rules refuse, so every workbook an earlier run put in rejected/ is
    holding a verdict taken under the old rules. This re-reads them from disk and judges them
    again; no model is called and no file is touched. `.superseded` copies are skipped: they
    are the vintage a refusal retired, not a year anybody asked about.
    """
    out_dir = os.path.join(config.FILES_DIR, "llm", slug)
    dest = os.path.join(out_dir, REJECTED_DIR)
    if not os.path.isdir(dest):
        return []
    ctx = context(slug)
    out = []
    for name in sorted(os.listdir(dest)):
        if not name.endswith(".xlsx") or "_budget_" not in name:
            continue
        path = os.path.join(dest, name)
        out.append((path,) + judge_workbook(path, ctx, slug))
    return out


REUSE_COLUMNS = ["slug", "fiscal_year", "workbook", "verdict", "rows", "programmes",
                 "reason", "finding", "not_checked"]


def write_reuse(path, records):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REUSE_COLUMNS)
        w.writeheader()
        for r in records:
            w.writerow(r)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", action="append", default=[], help="slug; repeatable")
    ap.add_argument("--all", action="store_true", help="every country with a config")
    ap.add_argument("--workbook", help="judge one stage 5 workbook and exit")
    ap.add_argument("--rejudge", action="store_true",
                    help="judge what is in data/llm/<slug>/rejected/ instead of the years the "
                         "config names, so a verdict taken under older rules can be re-read")
    ap.add_argument("--restore", action="store_true",
                    help="with --rejudge, put a workbook the rules now accept back on the "
                         "live path and write its findings beside it")
    ap.add_argument("--out", help="where to write the verdicts "
                                  "(default data/monitor/reuse.csv)")
    ap.add_argument("--quiet", action="store_true", help="only print the RESULT line")
    args = ap.parse_args(argv)
    if args.restore and not args.rejudge:
        print("COULD NOT RUN: --restore only means anything with --rejudge", file=sys.stderr)
        return 2

    records, rejected, with_findings = [], 0, 0
    if args.workbook:
        if not os.path.exists(args.workbook):
            print("COULD NOT RUN: no workbook at %s" % args.workbook, file=sys.stderr)
            return 2
        slug = os.path.basename(os.path.dirname(args.workbook))
        pairs = [(slug, (args.workbook,)
                  + judge_workbook(args.workbook, context(slug), slug))]
    else:
        slugs = args.country or (sorted(country.all_slugs()) if args.all else [])
        if not slugs:
            print("COULD NOT RUN: one of --country, --all or --workbook is required",
                  file=sys.stderr)
            return 2
        judge_one = rejudge_country if args.rejudge else judge_country
        pairs = [(s, r) for s in slugs for r in judge_one(s)]

    not_held = 0
    for slug, (path, year, reasons, findings, not_checked, rows) in pairs:
        moved = None
        if rows is None:
            verdict = "not held"
            not_held += 1
        elif reasons:
            verdict = "reject"
            rejected += 1
        elif findings:
            verdict = "keep with findings"
            with_findings += 1
        else:
            verdict = "keep"
        if args.restore and rows is not None and not reasons:
            out_dir = os.path.dirname(os.path.dirname(path))
            moved = restore_rejected(out_dir, os.path.basename(path))
            if moved:
                write_findings(out_dir, os.path.basename(path), findings)
        records.append({"slug": slug, "fiscal_year": year,
                        "workbook": config.unresolve(moved or path), "verdict": verdict,
                        "rows": "" if rows is None else len(rows),
                        "programmes": "" if rows is None else
                        sum(1 for r in rows
                            if str(r.get("line_type") or "") == "program"),
                        "reason": "; ".join(reasons),
                        "finding": "; ".join(findings),
                        "not_checked": "; ".join(not_checked)})
        if not args.quiet:
            print("  %-18s %-16s FY%-6s %s"
                  % (verdict, slug, year, "; ".join(reasons or findings)[:100] or "-"))
            if moved:
                print("         RESTORED to %s" % config.unresolve(moved))
            for n in not_checked:
                print("         NOT CHECKED: %s" % n)

    if not records:
        print("COULD NOT RUN: no stage 5 workbook on this machine for the countries asked "
              "for. Nothing was judged, which is not a pass.", file=sys.stderr)
        return 2
    out = args.out or os.path.join(config.FILES_DIR, "monitor", "reuse.csv")
    write_reuse(out, records)
    # judged, not len(records): a year-file nobody holds belongs in neither side of the
    # accepted count, and is printed on its own line so it cannot be read as either.
    judged = len(records) - not_held
    print("RESULT: %d of %d year(s) accepted, %d of them with findings -> %s"
          % (judged - rejected, judged, with_findings, config.unresolve(out)))
    if not_held:
        print("        %d year-file(s) the configs name are not on this machine and were "
              "not judged" % not_held)
    if not judged:
        print("COULD NOT RUN: not one of the %d year-file(s) asked for is on this machine. "
              "Nothing was judged, which is not a pass." % not_held, file=sys.stderr)
        return 2
    return 1 if rejected or with_findings else 0


if __name__ == "__main__":
    sys.exit(main())
