"""Scale: converting every amount into the unit the country declares.

A budget file states its own unit and a country config declares one. Where they differ,
stamping the declared unit on the row without converting rebases the year: Fiji held FY2017
at 4,356,831 thousand and FY2016 at 3,410 million, each right in its own unit, both labelled
"FJD thousand", a millionfold apart once added together.

`crore` and `lakh` are here because India declares "INR crore" and the old table held four
English words only, so India was never converted and never checked.
"""
SCALE_OF = {"thousand": 1e3, "lakh": 1e5, "million": 1e6, "crore": 1e7,
            "billion": 1e9, "trillion": 1e12}

# The closed vocabulary prompts 5 and 5c answer with, per row, and the only values the
# scale_word column may hold. It lives here, beside the multipliers, because a list of words
# in one file and their values in another is one list that can disagree with itself; the
# schema contract and the stage validator both import it.
#
# "unit" is not in SCALE_OF and is handled by name: a book printing whole currency states no
# scale word at all, and putting "unit" in the table above would make scale_word() match the
# substring in any label containing it. It is also the answer a label could never carry,
# which is half of why the column exists.
SCALE_WORDS = ("unit",) + tuple(sorted(SCALE_OF, key=SCALE_OF.get))


def scale_word(unit):
    """(word, value) for the scale a unit string names, longest word first, or (None, None)."""
    low = str(unit or "").lower()
    for w in sorted(SCALE_OF, key=len, reverse=True):
        if w in low:
            return w, SCALE_OF[w]
    return None, None


def scale_of_row(row, source_key="currency_unit_source"):
    """(word, value) for the scale one row is held in, from the row's own answer or its label.

    The column wins where it has a value: it is the model answering "what scale is this
    figure printed at", against a label that is a string copied off a page header and that
    named no scale at all on 8,024 of 15,964 rows. Every held workbook has no such column, so
    the label stays the fallback rather than becoming an error.
    """
    w = str(row.get("scale_word") or "").strip().lower()
    if w == "unit":
        return "unit", 1.0
    if w in SCALE_OF:
        return w, SCALE_OF[w]
    return scale_word(row.get(source_key) or row.get("currency_unit"))


def normalise(rows, declared, amount_key="amount", source_key="currency_unit_source"):
    """Convert each row into the declared unit. Returns what was converted, for the record.

    A declared unit naming no scale converts nothing: there is nothing to convert TO, and the
    file's own label cannot then be trusted. The Maldives declares "MVR" while five of its
    files label themselves "MVR million" and hold absolute rufiyaa; converting on that label
    turned 20.4bn into 2.04e16. Those countries are reported, not silently rescaled.
    """
    dw, dv = scale_word(declared)
    if not dw:
        return []
    changed = {}
    for r in rows:
        sw, sv = scale_of_row(r, source_key)
        if not sw or sw == dw:
            continue
        factor = sv / dv
        if r.get(amount_key) is not None:
            r[amount_key] = r[amount_key] * factor
        key = (r.get("fiscal_year"), sw, factor)
        changed[key] = changed.get(key, 0) + 1
    return [{"fiscal_year": y, "from_unit": w, "factor": f, "rows": n}
            for (y, w, f), n in sorted(changed.items())]
