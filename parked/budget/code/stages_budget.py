"""Budget stages 5, 5c, 5b, 6 and 6b, lifted unchanged from PV2 workflow/pv2/extract/stages.py.

Parked: kept here for reference until the budget lane is rebuilt on mother-tree nodes.
This file imports the old pv2 package and does not run in this repo as it stands.
"""
"""The prompt stages: prompt assembly, fan-out, validation, merge, one xlsx per stage."""
import collections
import json
import os
import re

from pv2 import config_patches as patches
from pv2 import country
from pv2.calcs import panel_helpers as H
from pv2.extract import accept, config, provenance, schemas, writer
from pv2.parse.parse import clean_markdown, mark_pages, markdown_page_chunks

SEP = "\n\n" + "=" * 70 + "\n"


# ---------------------------------------------------------------- helpers

# ---- lines 255-613 of the original
def _judge_year(client, rows, year, slug, accept_context):
    """(rejections, findings, not_checked) for one year, writing nothing.

    Split out of `_write_year` so a refusal can be answered with a second attempt before
    anything reaches disk: writing the rejection first would retire the year's superseded
    workbook and leave the reasons file behind even when the retry is accepted.
    """
    ctx = accept_context or {}
    # A fragment is a deliberate extract of part of a book (the one-page replay fixture): its
    # heads cannot sum to a national total because most of them are not in the file. A dry run
    # has no rows to judge at all.
    why_not = ("the acceptance gate: a dry run judges nothing"
               if getattr(client, "dry_run", False)
               else "the acceptance gate: this year is a fragment of its book"
               if str(year) in (ctx.get("fragment_years") or ()) else "")
    if why_not:
        return [], [], [why_not]
    printed, labels = (ctx.get("years") or {}).get(str(year), (None, None))
    return accept.judge(rows, printed, labels, patches.excluded_budget_lines(slug))


# One refused answer can name a hundred heads. The whole list would crowd the document out of
# the prompt and says nothing the first twenty do not, since they are the same rule repeated.
MAX_RETRY_REASONS = 20


def what_went_wrong(reasons, hint=""):
    """The block appended to a year's prompt on the one retry after the gate refuses it.

    The gate's own sentences, not a paraphrase: they name the head, the figure and the size of
    the gap, which is the whole of what the second read has to fix. The structure hint is
    restated under it because the first answer was produced with that hint already in the
    prompt and ignored it, and a rule the model has just broken is worth putting twice.
    """
    if not reasons:
        return ""
    out = (f"{SEP}WHAT WENT WRONG LAST TIME\n"
           "A first read of this document was refused because its arithmetic does not close. "
           "Every line below is a check that failed on that answer. Read the document again "
           "and return an answer that does not repeat them.\n")
    for r in reasons[:MAX_RETRY_REASONS]:
        out += f"  - {r}\n"
    if len(reasons) > MAX_RETRY_REASONS:
        out += (f"  - and {len(reasons) - MAX_RETRY_REASONS} more of the same kind, all of "
                "them heads whose programmes do not sum to the head\n")
    if hint:
        out += f"\nThe partition, restated, because the refused answer did not honour it:\n{hint}\n"
    return out



def _one_retry(client, stage, items, build, collect, rows, errors, year, slug,
               accept_context, name, label):
    """Ask once more for a year the acceptance gate refuses, with its reasons in the prompt.

    Returns (rows, errors, verdict) where verdict is the (reasons, not_checked) `_write_year`
    is to act on, so the caller judges the year exactly once whichever answer it keeps.

    ONE retry, never a loop. The failure this catches is a read that took two tables where the
    document has one, and a model that repeats itself on the second ask will repeat itself on
    the tenth while billing for each. The second ask is a different prompt, so it is a genuine
    second call and not a cache hit on the first.

    Where the retry is refused too, the year keeps the FIRST answer and the FIRST reasons, with
    a line recording that a second attempt was made and what it was refused for. Swapping in
    the second answer would make the workbook in `rejected/` change from run to run for a year
    that is refused either way, and the reasons file is the record of a verdict, not a diary.
    """
    reasons, findings, not_checked = _judge_year(client, rows, year, slug, accept_context)
    if not reasons or getattr(client, "dry_run", False):
        return rows, errors, (reasons, findings, not_checked)
    _log(f"stage {stage}: {name} was refused by the acceptance gate; asking once more with "
         f"the {len(reasons)} reason(s) in the prompt")
    answers, retry_errors = client.map(stage, items,
                                       lambda item: build(item, refused=reasons),
                                       label=label, concurrency=2, expect="array")
    retry_rows, _dropped = collect(answers, note=" (retry)")
    retry_reasons, retry_findings, retry_not_checked = _judge_year(client, retry_rows, year,
                                                                   slug, accept_context)
    if not retry_reasons:
        _log(f"stage {stage} -> {name} accepted on the second read ({len(retry_rows)} lines)")
        return retry_rows, errors + retry_errors, ([], retry_findings, retry_not_checked)
    _log(f"stage {stage}: the second read of {name} was refused too "
         f"({len(retry_reasons)} reason(s)); keeping the first answer")
    told = "; ".join(retry_reasons[:3]) + ("; …" if len(retry_reasons) > 3 else "")
    kept = list(reasons) + ["asked again with these reasons in the prompt, and the second "
                            "answer was refused too: " + told]
    return rows, errors + retry_errors, (kept, findings, not_checked)


def _write_year(client, out_dir, filename, rows, year, accept_context, stage, slug,
                verdict=None):
    """Write one year's stage 5 output, to the rejected folder where it is not fit to be mapped.

    Returns (path, accepted, reasons, findings, not_checked). Accepted covers a year kept
    with findings: the workbook is on the live path and its findings sit beside it as
    <name>.findings.txt, because D19 refuses wrong data and records incomplete data.

    A dry run judges nothing: it has no rows
    to judge, and a reasons file written for a year nobody extracted would read as a verdict
    on the year already on disk.

    An accepted year is stamped here, as it is written, rather than once after all of them: a
    stamp is believed only within STAMP_TOLERANCE_S of the file it names, and Thailand's five
    years took 2,434 s while Maldives has sixteen, so the first years of a long run read as
    unstamped and every later reader treated them as unattributable. A rejected year is not
    stamped: its workbook is in the rejected folder, and a stamp would record it as this
    prompt's accepted output for the year.
    """
    reasons, findings, not_checked = (verdict if verdict is not None
                                      else _judge_year(client, rows, year, slug,
                                                       accept_context))
    if reasons:
        path = accept.write_rejected(out_dir, filename, rows, schemas.STAGE5_COLUMNS, reasons)
        # The year this run refused replaced one an earlier run accepted, and that one is
        # still on the path every later stage globs. A gate that refuses a year and leaves
        # it where _budget_rows_from_files, write_country_config and the union all read it
        # has refused nothing, while pv2/run.py reports it as "excluded from every table
        # below". Moved aside beside the refusal, not deleted: nothing is thrown away.
        accept.retire_superseded(out_dir, filename)
        _log("NOT ACCEPTED %s -> %s" % (filename,
                                        os.path.join(accept.REJECTED_DIR, filename)))
        for r in reasons:
            _log("    ! %s" % r)
        return path, False, reasons, findings, not_checked
    # Named here rather than read back out of _write: every other stage names its own path,
    # and the stamp below needs one whether the write happened or was a dry run.
    path = os.path.join(out_dir, filename)
    _write(client, path, rows, schemas.STAGE5_COLUMNS)
    # A reasons file outlives the verdict it records unless the acceptance clears it: the run
    # report and errors.json both read the folder, so a year rejected once and re-extracted
    # cleanly went on being reported as rejected for ever.
    if not getattr(client, "dry_run", False):
        accept.clear_rejection(out_dir, filename)
        # Written on every accepted year, including a clean one, because write_findings
        # clears the file an earlier run left when there is nothing to record: a findings
        # file outliving its verdict is the same fault the reasons file had.
        accept.write_findings(out_dir, filename, findings)
    if findings:
        _log("ACCEPTED WITH FINDINGS %s -> %s"
             % (filename, filename + accept.FINDINGS_SUFFIX))
        for r in findings:
            _log("    ? %s" % r)
    stamp_outputs(client, out_dir, stage, [path], slug)
    return path, True, [], findings, not_checked


def run_stage5c(client, budget_docs, out_dir, slug, hint="", retry_empty=None,
                accept_context=None):
    """Budget speech, one call per document; same output shape as stage 5, fewer lines.

    `retry_empty` names the documents the screen found money lines in. An empty answer for
    one of those gets a second, differently worded call before it is written: China's four
    speeches came back empty in August and 24 to 30 rows each on a re-run with the same
    prompt (W94), and the cache would have returned the empty answer forever.
    """
    prompt = config.load_prompt("5c")
    retry_empty = retry_empty or set()
    outputs = []
    for doc, year in budget_docs:
        body = prompt + (f"{SEP}COUNTRY-SPECIFIC NOTES\n{hint}\n" if hint else "")
        # Mark before cleaning: mark_pages numbers the pages by the very comments
        # clean_markdown strips, so the other order silently numbers nothing and every
        # source_page comes back blank. Same trap as chunking, named at stage 5 below.
        text = clean_markdown(mark_pages(doc.markdown))
        _log(f"stage 5c: {doc.name} (FY{year}), {doc.page_count} pages, 1 call")

        def build(_item, again=False, refused=()):
            return (f"{body}{SEP}FISCAL YEAR FOR THIS RUN: {year}\n"
                    f"Return only rows whose figures belong to FY{year}.\n"
                    + ("A first read of this document returned no allocation at all, and the "
                       "document states money figures. Read it again, the partition first, "
                       "and return every allocation it states.\n" if again else "")
                    + what_went_wrong(refused, hint)
                    + f"{SEP}DOCUMENT\n{text}\n")

        results, errors = client.map("5c", [year], build, label="document", expect="array")

        def collect(answers, note=""):
            out = []
            for res in answers:
                if res is not None:
                    out.extend(schemas.validate_stage5(res, year,
                                                       ctx=f"{doc.name} FY{year}{note}"))
            return out, 0

        rows, _ = collect(results)
        if not rows and not errors and os.path.basename(doc.path) in retry_empty:
            _log(f"stage 5c: {doc.name} returned no allocation though the screen found "
                 f"money lines; one second attempt")
            results, errors2 = client.map("5c", [year], lambda it: build(it, again=True),
                                          label="document", expect="array")
            errors += errors2
            for res in results:
                if res is not None:
                    rows.extend(schemas.validate_stage5(res, year, ctx=f"{doc.name} FY{year} (2)"))
        name = f"{slug}_budget_{year}.xlsx"
        stated = sum(1 for r in rows if r.get("line_type") == "grand_total")
        _log(f"stage 5c -> {name} ({len(rows)} lines, "
             f"{'a' if stated else 'NO'} grand total, {len(errors)} errors)")
        rows, errors, verdict = _one_retry(client, "5c", [year],
                                           lambda it, refused=(): build(it, refused=refused),
                                           collect, rows, errors, year, slug, accept_context,
                                           name, "document")
        path, ok, reasons, findings, unchecked = _write_year(
            client, out_dir, name, rows, year, accept_context, "5c", slug, verdict=verdict)
        outputs.append({"year": year, "path": path, "rows": rows, "errors": errors,
                        "accepted": ok, "reasons": reasons, "findings": findings,
                        "not_checked": unchecked})
    return outputs


def run_stage5(client, budget_docs, out_dir, slug, chunk_tokens=60000, hint="",
               program_code_pattern="", program_code_take="", accept_context=None):
    """Budget extraction from page-aligned markdown chunks; tables stay intact."""
    prompt = config.load_prompt("5")
    outputs = []
    for doc, year in budget_docs:
        # Chunk the raw markdown first: cleaning strips the page marker the chunker splits on.
        pieces = [clean_markdown(p) for p in
                  markdown_page_chunks(doc.markdown, max_tokens=chunk_tokens, with_pages=True)]
        pieces = [p for p in pieces if p.strip()]
        _log(f"stage 5: {doc.name} (FY{year}), {doc.page_count} pages, {len(pieces)} call(s)")

        def build(piece, refused=()):
            return (f"{prompt}"
                    + (f"{SEP}HOW THIS COUNTRY'S BUDGET IS STRUCTURED\n{hint}\n" if hint else "")
                    + what_went_wrong(refused, hint)
                    + f"{SEP}FISCAL YEAR of this document: {year}\n"
                    f"Put this value in the fiscal_year field of every record.\n\n"
                    f"BUDGET DOCUMENT (extracted with layout; tables preserved)\n{piece}\n")

        results, errors = client.map("5", pieces, build, label="section", concurrency=2,
                                     expect="array")
        # Which codes are programmes is a fact about the document; a regex cannot be argued with.
        keep_code = re.compile(program_code_pattern) if program_code_pattern else None

        def take(code):
            c = str(code or "")
            if program_code_take == "last":
                return c.rsplit(".", 1)[-1].strip()
            if program_code_take == "first":
                return c.split(".", 1)[0].strip()
            return c

        def collect(answers, note=""):
            rows, seen, dropped = [], set(), 0
            for res in answers:
                for row in schemas.validate_stage5(res, year, ctx=f"{doc.name} FY{year}{note}"):
                    if program_code_take and row.get("program_code"):
                        row["program_code"] = take(row["program_code"])
                    if (keep_code and row.get("line_type") == "program"
                            and not keep_code.match(str(row.get("program_code") or ""))):
                        dropped += 1
                        continue
                    key = (row["strategy_code"], row["program_code"], row["line_type"])
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(row)
            rows.sort(key=lambda r: (_codekey(r["strategy_code"]),
                                     r["line_type"] != "strategy_total",
                                     _codekey(r["program_code"])))
            return rows, dropped

        rows, dropped = collect(results)
        name = f"{slug}_budget_{year}.xlsx"
        _log(f"stage 5 -> {name} ({len(rows)} lines"
             + (f", {dropped} row(s) dropped by program_code_pattern)" if dropped else ")"))
        rows, errors, verdict = _one_retry(client, "5", pieces, build, collect, rows, errors,
                                           year, slug, accept_context, name, "section")
        path, ok, reasons, findings, unchecked = _write_year(
            client, out_dir, name, rows, year, accept_context, "5", slug, verdict=verdict)
        outputs.append({"year": year, "path": path, "rows": rows, "errors": errors,
                        "accepted": ok, "reasons": reasons, "findings": findings,
                        "not_checked": unchecked})
    return outputs


# ---------------------------------------------------------------- stage 5b
def run_stage5b(client, budget_by_year, out_path, slug, batch_tokens=12000):
    """Programme class, once per distinct (head, programme, code), not per year."""
    prompt = config.load_prompt("5b")
    first, programs = {}, []
    for year in sorted(budget_by_year):
        for r in budget_by_year[year]:
            if r["line_type"] != "program":
                continue
            key = (str(r.get("strategy_name") or ""), str(r.get("program_name") or ""),
                   schemas._digits_or_text(r.get("program_code")))
            # One call per distinct programme, but the answer belongs to every year's row of
            # it: the ids are collected here so attach_programme_class can join on them
            # instead of on three strings that only sometimes match.
            if key not in first:
                first[key] = dict(r)
                first[key]["budget_row_ids"] = []
                programs.append(first[key])
            first[key]["budget_row_ids"].append(schemas.budget_row_id(slug, r))
    if not programs:
        _log("stage 5b: no programme rows to classify")
        return {"path": out_path, "rows": [], "dropped": [], "errors": []}
    for p in programs:
        p["budget_row_ids"] = "; ".join(p["budget_row_ids"])
    # The description says what the programme is for, which is the question this stage asks;
    # the column is sent whether or not the country's budget prints one, because 5b's prompt
    # names five columns and a table that does not match it is worse than a blank cell. The
    # byte-identity that Phase 2 protected here is gone either way: the prompt file itself
    # moved, so every recorded 5b call is re-recorded before the next run.
    cols = ["strategy_code", "strategy_name", "program_code", "program_name",
            "program_description"]
    batches = _batch_by_tokens(
        programs, lambda p: _render_rows([p], cols, max_chars=DESCRIPTION_CAP), batch_tokens)
    _log(f"stage 5b: {len(programs)} distinct programme(s) in {len(batches)} batch(es)")

    def build(batch):
        return (f"{prompt}{SEP}BUDGET PROGRAMMES TO CLASSIFY "
                f"({len(batch)} rows; return exactly {len(batch)} records, same order)\n"
                + _render_rows(batch, cols, max_chars=DESCRIPTION_CAP) + "\n")

    results, errors = client.map("5b", batches, build, label="batch", expect="array")
    rows, dropped = [], []
    for batch, res in zip(batches, results):
        ok, bad = schemas.validate_stage5b(res, batch, ctx=f"batch of {len(batch)}")
        rows.extend(ok)
        dropped.extend(bad)
    _write(client, out_path, rows, schemas.STAGE5B_FIELDS)
    _log(f"stage 5b -> {os.path.basename(out_path)} ({len(rows)} classified, {len(dropped)} "
         f"dropped, {len(errors)} errors)")
    _log(f"    {dict(collections.Counter(r['programme_class'] for r in rows))}")
    for code, why in sorted(set(dropped))[:20]:
        _log(f"    ! dropped {code!r}: {why}")
    return {"path": out_path, "rows": rows, "dropped": dropped, "errors": errors}


def attach_programme_class(budget_by_year, class_path, slug):
    """Stamp budget rows with their class, on the row id where 5b recorded one. Rows stamped.

    The join was three normalised strings and lost 8,710 of 12,853 programme rows, because the
    name 5b returns is the name it was given and the code is not always written the same way
    twice. A workbook from before this carries no ids and falls back to those strings, which
    is why the two keys both live in schemas rather than one replacing the other.
    """
    if not class_path or not os.path.exists(class_path):
        return 0
    index = schemas.programme_class_index(writer.read_rows(class_path))
    n = 0
    for rows in budget_by_year.values():
        for r in rows:
            cls = schemas.class_of(index, slug, r)
            if cls:
                r["programme_class"] = cls
                n += 1
    if n and not index["by_id"]:
        _log("stage 5b: %s carries no budget row ids, so the class was joined on names; "
             "re-run 5b to join on ids" % os.path.basename(class_path))
    return n


# ---------------------------------------------------------------- stage 4a

# ---- lines 1184-1330 of the original
def merge_same_names(rows):
    """(rows with every set the union would key alike folded into one, the count folded away).

    A row can sit in its sector's shard and in a name shard, and two shards can each return a
    group under the same canonical name. The union keys a strategy on its normalised,
    twin-folded name, so it kept the first such row and dropped the other's tags, and
    strategy_year kept the last: 21 rows in five countries on 29 September 2026, hidden until
    then by the stage 4c fold. `rows` are merge_groups rows (lists parsed, `members` set).
    """
    alias = H.twin_aliases([r["intervention_name"] for r in rows])
    by_key = collections.defaultdict(list)
    for i, r in enumerate(rows):
        name = r["intervention_name"]
        by_key[H.norm(alias.get(H.norm(name), name))].append(i)
    groups = [("", sorted(ids, key=lambda i: -len(rows[i]["source_chunks"])))
              for ids in by_key.values() if len(ids) > 1]
    out, _away = merge_groups(rows, groups)
    return out, len(rows) - len(out)


# ---------------------------------------------------------------- stage 6
BUDGET_COLS = ["strategy_code", "strategy_name", "program_code", "program_name", "line_type",
               "amount", "currency_unit"]
# The strategy's own plan text, not just its name and tags: the call used to decide a match
# from two names, one on each side. component_interventions and risk_evidence are what stage 4
# already holds. What they cost per call is a fact about a country's own strategies and moves
# with every re-extraction, so it is measured off the workbook rather than typed here; on
# thailand_strategyclean.xlsx it is tens of tokens, not hundreds.
STRATEGY_COLS = ["intervention_name", "ndp_milestone", "HDICategory", "sector",
                 "related_risks", "response_orientation", "sdg_targets", "stated_urgency",
                 "component_interventions", "risk_evidence"]


def budget_block(rows):
    """One year's budget as the mapping prompts see it."""
    cols = _columns_present(BUDGET_COLS, rows, ("programme_class", "program_description"))
    return _render_rows(rows, cols, max_chars=DESCRIPTION_CAP)


def run_stage6(client, strategies, budget_by_year, out_dir, slug, stage_dir):
    """Mapping, one call per (year, strategy); the year's budget is a stable prefix for caching.

    `out_dir` is the mappings folder written into; `stage_dir` is the country's stage folder,
    which is where provenance.json lives and what a stamped path is relative to.
    """
    prompt = config.load_prompt("6")
    os.makedirs(out_dir, exist_ok=True)
    outputs = []
    for year in sorted(budget_by_year):
        rows = budget_by_year[year]
        programs = schemas.build_programme_index(rows)
        if not programs["code"]:
            # A year with no programme line cannot be mapped, and skipping it silently left
            # any mapping an earlier run had written sitting in mappings/ for ever: stage 6
            # skips the year on every future run too, so nothing can rewrite it and the
            # currency audit reports it as older than its prompt with no way to clear. Fiji's
            # FY2018 is a budget SPEECH read through stage 5c, which yields no programme line,
            # and its mapping survived from 08:59 through a --force re-run of the whole
            # country. Retired with the year, the way accept.py retires a rejected one (W133).
            from pv2.extract import accept
            gone = accept.retire_derived(stage_dir, str(year))
            _log(f"stage 6: FY{year} has no programme lines, skipped"
                 + (f"; retired {len(gone)} mapping(s) it can never rewrite" if gone else ""))
            continue
        shared = sum(1 for v in programs["code"].values() if len(v) > 1)
        if shared:
            _log(f"stage 6: FY{year} has {shared} programme code(s) under more than one "
                 f"budget strategy; an edge citing one must name its strategy too")
        body = prompt.replace("<<INSERT_FISCAL_YEAR>>", str(year))
        prefix = f"{body}{SEP}BUDGET FOR FISCAL YEAR {year}\n{budget_block(rows)}\n{SEP}"
        _log(f"stage 6: FY{year}, {len(strategies)} strategies x {len(programs['pair'])} programmes")

        def build(s):
            return prefix + ("STRATEGY TO MAP (this run considers ONLY this strategy)\n"
                             + _render_rows([s], STRATEGY_COLS) + "\n")

        results, errors = client.map("6", strategies, build, label="strategy", expect="array")
        mapped, rejected = [], []
        for s, res in zip(strategies, results):
            if res is None:
                continue
            ok, bad = schemas.validate_stage6(res, s, year, programs, ctx=s["intervention_name"])
            mapped.extend(ok)
            rejected.extend(bad)
        path = os.path.join(out_dir, f"{slug}_mapping_{year}.xlsx")
        _write(client, path, mapped, schemas.STAGE6_FIELDS)
        _log(f"stage 6 -> {os.path.basename(path)} ({len(mapped)} matches, {len(rejected)} "
             f"rejected, {len(errors)} errors)")
        for code, why in sorted(set(rejected)):
            _log(f"    ! rejected {code!r}: {why}")
        stamp_outputs(client, stage_dir, "6", [path], slug)    # per year; see 5c above
        outputs.append({"year": year, "path": path, "rows": mapped, "rejected": rejected,
                        "errors": errors})
    return outputs


def run_stage6b(client, strategies, budget_by_year, out_dir, slug, stage_dir):
    """Coverage, the reverse pass: one call per (year, programme). `stage_dir` as in stage 6."""
    prompt = config.load_prompt("6b")
    os.makedirs(out_dir, exist_ok=True)
    outputs = []
    index = schemas.build_strategy_index(s["intervention_name"] for s in strategies)
    if index["ambiguous"]:
        _log(f"stage 6b: {len(index['ambiguous'])} strategy name(s) are shared by more than "
             f"one inventory entry and can only be joined exactly")
    inv_cols = ["intervention_name", "HDICategory", "sector", "related_risks",
                "response_orientation", "ndp_milestone"]
    for year in sorted(budget_by_year):
        programs = [r for r in budget_by_year[year] if r["line_type"] == "program"]
        if not programs:
            continue
        body = prompt.replace("<<INSERT_FISCAL_YEAR>>", str(year))
        prefix = f"{body}{SEP}STRATEGY INVENTORY\n{_render_rows(strategies, inv_cols)}\n{SEP}"
        _log(f"stage 6b: FY{year}, {len(programs)} programmes")
        # The description goes on the programme line, never into the inventory: the inventory
        # is repeated in every one of the year's calls and is the largest block in the prompt,
        # by an order of magnitude between the smallest country and the largest.
        # Decided once for the year, so every call of the year has the same shape.
        pcols = _columns_present(["strategy_code", "strategy_name", "program_code",
                                  "program_name"], programs, ("program_description",))

        def build(p):
            return prefix + ("BUDGET PROGRAMME TO MAP (this run considers ONLY this programme)\n"
                             + _render_rows([p], pcols, max_chars=DESCRIPTION_CAP) + "\n")

        results, errors = client.map("6b", programs, build, label="programme", expect="array")
        edges, dropped = [], []
        for p, res in zip(programs, results):
            if res is None:
                continue
            ok, bad = schemas.validate_stage6b(res, p, year, index, ctx=p["program_code"])
            edges.extend(ok)
            dropped.extend(bad)
        path = os.path.join(out_dir, f"{slug}_coverage_{year}.xlsx")
        _write(client, path, edges, schemas.STAGE6B_FIELDS)
        _log(f"stage 6b -> {os.path.basename(path)} ({len(edges)} edges, {len(dropped)} dropped, "
             f"{len(errors)} errors)")
        for name, why in sorted(set(dropped)):
            _log(f"    ! dropped {name!r}: {why}")
        stamp_outputs(client, stage_dir, "6b", [path], slug)   # per year; see 5c above
        outputs.append({"year": year, "path": path, "rows": edges, "dropped": dropped,
                        "errors": errors})
    return outputs


# ---------------------------------------------------------------- stage 7
# The sector supplement never touches the budget: no amount, no programme, no panel row.
