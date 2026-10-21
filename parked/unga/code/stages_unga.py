"""UNGA stage 8, lifted unchanged from PV2 workflow/pv2/extract/stages.py (lines 1462 on).

Parked: UNGA speeches will run through the main extract step (E) with doc_type "unga".
This file imports the old pv2 package and does not run in this repo as it stands.
"""
def unga_path(out_dir, slug):
    return os.path.join(out_dir, "unga", "%s_unga_statements.xlsx" % slug)


def statement_year(filename):
    """The year a transcript's filename names, or None where it names none or several."""
    years = re.findall(r"(20[0-4]\d)", os.path.basename(filename))
    return int(years[0]) if len(set(years)) == 1 else None


def run_stage8(client, unga_docs, out_dir, slug, force=False):
    """One call per General Debate statement: all 11 risks and all 15 HDI categories.

    A statement is 4 to 18 pages, so it is read whole rather than chunked: what an address was
    mainly about is only judgeable from the address. The documents arrive parsed by Document
    Intelligence like every plan and budget. Two refusals before anything is spent, each named:
    a document that parsed to nothing, and one whose text is not words (W139), which a model
    answers with an invented speech rather than an error.
    """
    from pv2 import doctype
    from pv2.parse import parse as P
    path = unga_path(out_dir, slug)
    if os.path.exists(path) and not force:
        _log(f"stage 8: reusing {os.path.relpath(path, out_dir)}")
        return [], []
    prompt = config.load_prompt("8")
    if UNGA_PLACEHOLDER not in prompt:
        raise ValueError("prompt 8 has lost its statement placeholder")
    ready, errors = [], []
    for d in unga_docs:
        fname = os.path.basename(d.path)
        text = mark_pages(d.markdown or "")
        score, n, judged = P.legibility(text)
        if not d.paragraphs:
            why = "parsed to zero paragraphs"
        elif judged and score < P.MIN_LEGIBLE:
            why = "text is not words: %d tokens at %.3f legibility (W139)" % (n, score)
        else:
            why = None
        if why:
            _log(f"  stage 8: REFUSED {fname}: {why}")
            errors.append(("refused", "%s: %s" % (fname, why)))
            continue
        ready.append((d, fname, clean_markdown(text)))
    _log(f"stage 8: {len(ready)} statement(s), {len(errors)} refused")
    if not ready:
        return [], errors

    results, call_errors = client.map(
        "8", ready, lambda item: prompt.replace(UNGA_PLACEHOLDER, item[2]),
        label="statement", expect="object")
    errors += [(ready[i][1], e) for i, e in call_errors]
    statements, risks, hdi = [], [], []
    for (d, fname, _text), res in zip(ready, results):
        if not isinstance(res, dict):
            continue
        header, r_rows, h_rows = schemas.validate_stage8(res, ctx=fname)
        key = {"doc_name": d.name, "statement_year": statement_year(fname)}
        risks += [dict(key, **r) for r in r_rows]
        hdi += [dict(key, **h) for h in h_rows]
        statements.append(dict(
            key, file=fname, pages=d.page_count,
            parser="document_intelligence",
            language=doctype.language_of(fname),
            risks_engaged=sum(1 for r in r_rows if r["direction"] != "absent"),
            hdi_advanced=sum(1 for h in h_rows if h["present"]), **header))
    if getattr(client, "dry_run", False):
        return statements, errors
    os.makedirs(os.path.dirname(path), exist_ok=True)
    writer.write_sheets(path, {"statements": (statements, UNGA_STATEMENT_COLUMNS),
                               "risks": (risks, UNGA_RISK_COLUMNS),
                               "hdi": (hdi, UNGA_HDI_COLUMNS)})
    _log(f"stage 8 -> {os.path.relpath(path, out_dir)} ({len(statements)} statements, "
         f"{len(risks)} risk rows, {len(hdi)} hdi rows)")
    return statements, errors
