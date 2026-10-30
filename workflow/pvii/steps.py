"""The four prompt steps, each run on ONE plan: C context, E extract, F fold, M map.

Every row a step writes carries the plan's columns (plan_id, period, doc_type), so the country
and global tables are these files stacked and nothing has to be joined back later.
"""
import collections
import hashlib
import json
import os
import re

from pvii import config, io, quotes, vocab
from pvii.parse import clean_markdown, markdown_page_chunks

SEP = "\n\n" + "=" * 70 + "\n"
CONTEXT_PART_TOKENS = 90000
FOLD_SHARD_MAX = 60
MAP_BATCH = 25
KEEP_STATEMENTS = ("commitment", "ongoing")
STATEMENT_TYPES = ("commitment", "ongoing", "completed", "background")
RISK_FRAMINGS = ("threat", "vulnerability", "constraint", "opportunity_with_risk")
MIN_EVIDENCE_CHARS = 8        # PV2 quote_found: a shorter "quote" is not evidence
# Step E's strategy-level fields, from PV2 prompts 3 and 4. The RHDR category is not among them:
# it is the tree's subpillar, set by step M.
CLASS_COLUMNS = ["risk_evidence", "stated_urgency", "sdg_targets",
                 "sdg_primary_dimension", "response_orientation", "response_evidence", "sector",
                 "sector_canonical", "institutional_lead", "implementation_status",
                 "has_timeline", "has_quantified_target", "has_monitoring", "legal_or_plan_basis"]

RISK_COLUMNS = ["risk_id", "plan_id", "country", "slug", "doc_type", "edition", "plan_title",
                "period_start", "period_end", "published", "ref", "page", "heading", "section_type", "risk",
                "other_risk", "framing", "quote", "quote_en", "quote_check"]
ROW_COLUMNS = ["row_id", "plan_id", "country", "slug", "doc_type", "edition", "plan_title",
               "period_start", "period_end", "published", "ref", "page", "heading", "section_type",
               "statement_type", "name", "objective", "target_group", "instrument", "pillar",
               "related_risks", "target_year", "target_year_quote", "horizon", "place",
               "quantified_targets", "named_agencies", "quote", "quote_en", "quote_check"
               ] + CLASS_COLUMNS
STRATEGY_COLUMNS = ["strategy_id", "plan_id", "country", "slug", "doc_type", "edition",
                    "plan_title", "period_start", "period_end", "published", "name", "objective",
                    "target_group", "instrument", "pillar", "statement_type", "related_risks",
                    "target_year", "horizon", "place", "n_mentions", "members", "refs", "quote",
                    "quote_en", "quote_check", "quantified_targets", "named_agencies"
                    ] + CLASS_COLUMNS + [
                    # step M
                    "tree_version", "relation", "objective_id", "tree_objective",
                    "new_objective", "node_id", "level", "depth_basis", "depth_words",
                    "group_id", "group", "family_id", "family", "mechanism_id", "mechanism",
                    "pathway_id", "pathway", "subpillar", "pillar_rhdr", "target_id", "target_label", "instrument_id",
                    "instrument_label", "proposal", "confidence", "map_note"]
PROPOSAL_COLUMNS = ["plan_id", "strategy_id", "name", "objective", "relation", "new_objective",
                    "node_id", "proposal", "quote_en", "quote"]


def _log(msg):
    print(msg, flush=True)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _str(v):
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def _list(v):
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return [_str(x) for x in v if _str(x)]
    return [_str(v)]


def _year(v):
    try:
        y = int(str(v).strip()[:4])
    except (TypeError, ValueError):
        return None
    return y if 1950 <= y <= 2100 else None


def horizon(target_year, plan):
    """plan where the stated year falls inside the period, long where after it, "" with none."""
    if target_year is None or plan.end is None:
        return ""
    if target_year > int(plan.end):
        return "long"
    if plan.start is not None and target_year < int(plan.start):
        return "before"
    return "plan"


# ================================================================ C: the context file
def context(client, plan, doc, out_dir, force=False):
    """The plan's context file, read once over the whole document. Never overwritten.

    Lifted from PV2 stage 4a's rule: a file that exists is not re-extracted, because the person
    reviewing it may have corrected it, and spending to overwrite a correction with a fresh
    guess is worse than keeping it. `force` is the way to ask again. Unlike 4a, which read only
    the first 90,000 tokens of every plan a country holds pooled together, this reads every part
    of one document and merges the parts.
    """
    path = os.path.join(out_dir, "context.json")
    if os.path.exists(path) and not force:
        _log("C: using existing %s (edit it by hand; --force-context asks again)" % path)
        return io.read_json(path)
    raw = doc.markdown or "\n\n".join(p["content"] for p in doc.paragraphs)
    pieces = [clean_markdown(p) for p in markdown_page_chunks(raw, max_tokens=CONTEXT_PART_TOKENS)]
    pieces = [p for p in pieces if p.strip()] or [clean_markdown(raw)]
    head = ("DOCUMENT: %s\nCOUNTRY: %s\nPERIOD IN THE REGISTER: %s-%s\nTYPE: %s"
            % (plan.title, plan.country, plan.start, plan.end, plan.doc_type))
    prompt = config.load_prompt("C")
    _log("C: %d part(s) of up to %d tokens" % (len(pieces), CONTEXT_PART_TOKENS))

    def build(i):
        return "%s%s%s\nPART %d OF %d%s%s\n" % (prompt, SEP, head, i + 1, len(pieces), SEP, pieces[i])

    parts, errors = client.map("C", list(range(len(pieces))), build, label="part", expect="object")
    if getattr(client, "dry_run", False):
        if len(pieces) > 1:
            client.call("C_reduce", "%s%s%s%s%s" % (config.load_prompt("C_reduce"), SEP, head, SEP,
                                                     "x" * 20000), expect="object")
        return {}
    parts = [p for p in parts if isinstance(p, dict)]
    if not parts:
        raise RuntimeError("C: no part of %s returned a context (%s)" % (plan.plan_id, errors[:1]))
    if len(parts) == 1:
        ctx = parts[0]
    else:
        ctx = client.call("C_reduce", "%s%s%s%sPARTS\n%s\n" % (
            config.load_prompt("C_reduce"), SEP, head, SEP,
            json.dumps(parts, ensure_ascii=False)), expect="object") or {}
    ctx = _clean_context(ctx, plan, clean_markdown(raw))
    io.write_json(path, ctx)
    with open(os.path.join(out_dir, "context.md"), "w", encoding="utf-8") as f:
        f.write(context_markdown(ctx, plan))
    return ctx


def _clean_context(ctx, plan, document_text):
    """Shape the context, check its quotes against the document, and compare its period."""
    out = {"plan_id": plan.plan_id, "title": plan.title,
           "publication": _publication(ctx.get("publication")),
           "period": ctx.get("period") or {}, "period_note": _str(ctx.get("period_note")),
           "structure": [s for s in ctx.get("structure") or [] if isinstance(s, dict)],
           "headline_targets": [t for t in ctx.get("headline_targets") or [] if isinstance(t, dict)],
           "risk_framing": ctx.get("risk_framing") or {},
           "vocabulary": [v for v in ctx.get("vocabulary") or [] if isinstance(v, dict)]}
    st, en = _year((out["period"] or {}).get("start")), _year((out["period"] or {}).get("end"))
    if (st, en) != (plan.start, plan.end) and (st or en):
        out["period_note"] = (out["period_note"] + " " if out["period_note"] else "") + (
            "The document reads %s-%s; the register says %s-%s." % (st, en, plan.start, plan.end))
    checks = {}
    for q in ([out["publication"]["quote"], (out["period"] or {}).get("quote")]
              + [s.get("parent_quote") for s in out["structure"]]
              + [t.get("quote") for t in out["headline_targets"]]
              + list((out["risk_framing"] or {}).get("quotes") or [])):
        if _str(q):
            v = quotes.check(q, document_text)
            checks[v] = checks.get(v, 0) + 1
    out["quote_checks"] = checks
    # A link between levels with no quoted sentence is the model grouping by subject, which
    # 4a learned to discard: it puts a structure in front of a reader the government never wrote.
    for s in out["structure"]:
        if s.get("parent") and not _str(s.get("parent_quote")):
            s["parent"] = ""
    return out


def _publication(p):
    """{date, event, quote}: the date as stated (YYYY, YYYY-MM or YYYY-MM-DD), "" when not."""
    p = p if isinstance(p, dict) else {}
    date = _str(p.get("date"))
    if not re.fullmatch(r"(19|20)\d\d(-[01]\d(-[0-3]\d)?)?", date):
        date = ""
    return {"date": date, "event": _str(p.get("event")) if date else "",
            "quote": _str(p.get("quote")) if date else ""}


def published(ctx):
    """The plan's publication date from its context, for the `published` column."""
    return ((ctx or {}).get("publication") or {}).get("date", "")


def context_markdown(ctx, plan):
    lines = ["# Context: %s" % plan.title, "",
             "plan_id `%s`, %s, %s to %s. This file is read by the extract and map steps; "
             "edit it freely, a re-run never overwrites it." % (plan.plan_id, plan.country,
                                                                 plan.start, plan.end), ""]
    pub = ctx.get("publication") or {}
    lines += ["**Published:** %s" % ("%s (%s)" % (pub["date"], pub.get("event") or "date")
                                     if pub.get("date") else "not stated"), ""]
    if ctx.get("period_note"):
        lines += ["**Period note:** " + ctx["period_note"], ""]
    lines += ["## Structure", ""]
    for s in ctx.get("structure") or []:
        lines.append("- %s %s %s%s" % (s.get("level", ""), s.get("number", ""), s.get("name", ""),
                                       (" (under %s)" % s["parent"]) if s.get("parent") else ""))
    lines += ["", "## Headline targets", ""]
    for t in ctx.get("headline_targets") or []:
        lines.append("- %s (%s)" % (t.get("target", ""), t.get("year") or "no year"))
    rf = ctx.get("risk_framing") or {}
    lines += ["", "## Risk framing", "", _str(rf.get("summary")), "",
              "Risks named: " + (", ".join(rf.get("risks_named") or []) or "none"), ""]
    lines += ["## Vocabulary", ""]
    for v in ctx.get("vocabulary") or []:
        lines.append("- **%s**: %s" % (v.get("term", ""), v.get("gloss", "")))
    lines += ["", "Quote checks against the document: %s" % json.dumps(ctx.get("quote_checks") or {})]
    return "\n".join(lines) + "\n"


def context_text(ctx, plan, max_chars=9000):
    """The compact context E and M carry with every call."""
    lines = ["Document: %s (%s), %s, period %s-%s" % (plan.title, plan.doc_type, plan.country,
                                                     plan.start, plan.end)]
    if ctx.get("structure"):
        lines.append("Structure:")
        for s in ctx["structure"]:
            lines.append("  %s %s %s%s" % (s.get("level", ""), s.get("number", ""), s.get("name", ""),
                                           (" [under %s]" % s["parent"]) if s.get("parent") else ""))
    rf = ctx.get("risk_framing") or {}
    if rf.get("summary"):
        lines.append("Risk framing: " + _str(rf["summary"]))
    if ctx.get("vocabulary"):
        lines.append("Terms: " + "; ".join("%s = %s" % (v.get("term", ""), v.get("gloss", ""))
                                           for v in ctx["vocabulary"]))
    text = "\n".join(lines)
    return text if len(text) <= max_chars else text[:max_chars] + "\n[context truncated]"


# ================================================================ E: extract
def extract(client, plan, doc, ctx, out_dir):
    """One call per paragraph: risks and strategies, quoted and checked against the paragraph."""
    prompt = e_prompt()
    ctx_block = context_text(ctx, plan)
    chunks = list(doc.paragraphs)
    _log("E: %d chunks" % len(chunks))

    def build(p):
        return "%s%sCONTEXT\n%s%sCHUNK\nRef: %s\nHeading: %s\n\n%s\n" % (
            prompt, SEP, ctx_block, SEP, p["ref"], p.get("section", ""), p["content"])

    results, errors = client.map("E", chunks, build, label="chunk", expect="object")
    risks, rows, dropped, invalid = [], [], [], []
    guards = collections.Counter()
    base = plan.row()
    for p, res in zip(chunks, results):
        if res is None:
            continue
        if not isinstance(res, dict):
            invalid.append((p["ref"], "not an object"))
            continue
        loc = {"ref": p["ref"], "page": p.get("page"), "heading": p.get("section", ""),
               "section_type": _str(res.get("section_type"))}
        for k, r in enumerate(res.get("risks") or []):
            if not isinstance(r, dict):
                continue
            risk = _str(r.get("risk"))
            if risk not in config.RISKS and risk != "other":
                invalid.append((p["ref"], "risk %r is not one of the eleven" % risk))
                continue
            framing = _str(r.get("framing"))
            row = dict(base, **loc)
            row.update(risk_id="%s#k%d.%d" % (plan.plan_id, p["index"], k + 1), risk=risk,
                       other_risk=_str(r.get("other_risk")) if risk == "other" else "",
                       framing=framing if framing in RISK_FRAMINGS else "",
                       quote=_str(r.get("quote")), quote_en=_str(r.get("quote_en")),
                       quote_check=quotes.check(r.get("quote"), p["content"]))
            risks.append(row)
        for k, s in enumerate(res.get("strategies") or []):
            if not isinstance(s, dict) or not _str(s.get("name")):
                continue
            ty = _year(s.get("target_year"))
            row = dict(base, **loc, **classify(s, p["content"], guards))
            row.update(row_id="%s#r%d.%d" % (plan.plan_id, p["index"], k + 1),
                       statement_type=_str(s.get("statement_type")).lower(),
                       name=_str(s.get("name")), objective=_str(s.get("objective")),
                       target_group=_str(s.get("target_group")),
                       instrument=_str(s.get("instrument")), pillar=_str(s.get("pillar")),
                       target_year=ty,
                       target_year_quote=_str(s.get("target_year_quote")) if ty else "",
                       horizon=horizon(ty, plan), place=_str(s.get("place")),
                       quantified_targets=_list(s.get("quantified_targets")),
                       named_agencies=_list(s.get("named_agencies")),
                       quote=_str(s.get("quote")), quote_en=_str(s.get("quote_en")),
                       quote_check=quotes.check(s.get("quote"), p["content"]))
            # An unknown or missing statement_type is kept and blanked, as in PV2: only a clear
            # completed or background label drops a row.
            if row["statement_type"] not in STATEMENT_TYPES:
                row["statement_type"] = ""
            (rows if row["statement_type"] in KEEP_STATEMENTS + ("",) else dropped).append(row)
    if getattr(client, "dry_run", False):
        # A dry run's answers are all None; files of empty tables would read as a plan that
        # was run and found nothing.
        return {"risks": [], "rows": [], "dropped": [], "errors": [], "invalid": [], "guards": {}}
    io.write_csv(os.path.join(out_dir, "risks.csv"), risks, RISK_COLUMNS)
    io.write_csv(os.path.join(out_dir, "strategy_rows.csv"), rows, ROW_COLUMNS)
    io.write_csv(os.path.join(out_dir, "strategy_rows_dropped.csv"), dropped, ROW_COLUMNS)
    _log("E -> %d risk records, %d strategy rows kept, %d dropped by the commitment test, "
         "%d call errors, %d invalid items; guards %s" % (
             len(risks), len(rows), len(dropped), len(errors), len(invalid),
             json.dumps(dict(guards))))
    return {"risks": risks, "rows": rows, "dropped": dropped,
            "errors": [(chunks[i]["ref"], e) for i, e in errors], "invalid": invalid,
            "guards": dict(guards)}


def e_prompt():
    return config.load_prompt("E")


def _found(quote, text):
    """Is an evidence phrase in the text the model was shown? PV2's quote_found, through this
    repo's quote matcher so Thai marks and pypdf spacing do not refuse a faithful phrase."""
    q = _str(quote)
    return len(quotes.normalise(q)) >= MIN_EVIDENCE_CHARS and \
        quotes.check(q, text) in (quotes.VERBATIM, quotes.EDITED)


def classify(s, paragraph, guards):
    """Step 4's fields for one strategy record, clamped as PV2's validate_stage4 clamps them.

    The guards, each counted: a risk with
    no phrase found in the paragraph is dropped (no quote, no risk); a proactive or
    transformative score with no phrase found falls to BAU; a target code that is not one of
    the 169 official targets is dropped.
    """
    risks, ev, lost = vocab.pair_risks(_list_positional(s.get("related_risks")),
                                       _list_positional(s.get("risk_evidence")),
                                       lambda q: _found(q, paragraph))
    guards["risk dropped: no quote found"] += len(lost)
    ori = vocab.ORIENTATIONS.get(_str(s.get("response_orientation")).lower(), "BAU")
    rev = _str(s.get("response_evidence"))
    if ori != "BAU" and not _found(rev, paragraph):
        guards["response set to BAU: no quote found"] += 1
        ori = "BAU"
    if ori == "BAU":
        rev = ""
    targets = []
    for t in _list(s.get("sdg_targets")):
        if t not in vocab.SDG_TARGET_DIMENSIONS:
            guards["SDG target not official"] += 1
        elif t not in targets:
            targets.append(t)
    st, lb, ur = (_str(s.get(k)).lower() for k in
                  ("implementation_status", "legal_or_plan_basis", "stated_urgency"))
    sector = _str(s.get("sector"))
    return dict(
        related_risks=risks, risk_evidence=ev,
        stated_urgency=ur if ur in vocab.URGENCIES else "medium",
        sdg_targets=targets, sdg_primary_dimension=vocab.primary_dimension(targets),
        response_orientation=ori, response_evidence=rev,
        sector=sector, sector_canonical=vocab.sector_canonical(sector),
        institutional_lead=_str(s.get("institutional_lead")),
        implementation_status=st if st in vocab.STATUSES else "aspiration",
        legal_or_plan_basis=lb if lb in vocab.BASES else "none",
        **{yn: "Y" if _str(s.get(yn)).upper().startswith("Y") else "N"
           for yn in ("has_timeline", "has_quantified_target", "has_monitoring")})


def _list_positional(v):
    """_list, but blanks keep their place so evidence[i] still pairs with risks[i] (PV2)."""
    if v is None or v == "":
        return []
    return [_str(x) for x in v] if isinstance(v, list) else [_str(v)]


# ================================================================ F: fold
_STOP = frozenset("and of the to for in on a an with by develop strengthen promote improve "
                  "enhance support expand increase build national programme program".split())


def _tokens(s):
    return {t for t in re.findall(r"[a-z]{3,}", str(s).lower()) if t not in _STOP}


def shards(rows, shard_max=FOLD_SHARD_MAX):
    """Rows grouped by pillar, each group split so no call sees more than shard_max rows.

    Rows with no pillar are grouped by the first content word of their objective, which keeps
    rows on one subject together without a model call. A duplicate that falls across two shards
    is missed; leaving two rows apart is the cheap error, as in PV2's 4b.
    """
    groups = {}
    for r in rows:
        key = r.get("pillar") or ""
        if not key:
            toks = sorted(_tokens(r.get("objective") or r.get("name")))
            key = "~" + (toks[0] if toks else "")
        groups.setdefault(key, []).append(r)
    out = []
    for key in sorted(groups):
        g = sorted(groups[key], key=lambda r: (r.get("objective") or "", r.get("name") or ""))
        for i in range(0, len(g), shard_max):
            out.append(g[i:i + shard_max])
    return out


def fold(client, plan, rows, out_dir):
    """Same strategy stated twice in one document becomes one strategy. Never across documents."""
    prompt = config.load_prompt("F")
    todo = [s for s in shards(rows) if len(s) > 1]
    _log("F: %d rows in %d shard(s) to read" % (len(rows), len(todo)))

    def build(shard):
        lines = ["%d | %s | %s | %s | %s | %s | %s" % (
            i + 1, r["name"], r["objective"], r["target_group"] or "-", r["instrument"] or "-",
            r["pillar"] or "-", r["ref"]) for i, r in enumerate(shard)]
        return "%s%sSTRATEGY ROWS FROM %s\n%s\n" % (prompt, SEP, plan.title, "\n".join(lines))

    results, errors = client.map("F", todo, build, label="shard", expect="array")
    group_of = {}      # row_id -> group dict
    for shard, res in zip(todo, results):
        if not isinstance(res, list):
            continue
        used = set()
        for g in res:
            if not isinstance(g, dict):
                continue
            ids = []
            for x in g.get("merge_ids") or []:
                try:
                    i = int(x)
                except (TypeError, ValueError):
                    continue
                if 1 <= i <= len(shard) and i not in used and i not in ids:
                    ids.append(i)
            if len(ids) < 2:
                continue
            used.update(ids)
            grp = {"name": _str(g.get("name")), "objective": _str(g.get("objective")),
                   "target_group": _str(g.get("target_group")),
                   "instrument": _str(g.get("instrument")),
                   "members": [shard[i - 1]["row_id"] for i in ids]}
            for i in ids:
                group_of[shard[i - 1]["row_id"]] = grp
    strategies, seen = [], set()
    by_id = {r["row_id"]: r for r in rows}
    for r in rows:
        if r["row_id"] in seen:
            continue
        grp = group_of.get(r["row_id"])
        members = [by_id[m] for m in grp["members"]] if grp else [r]
        seen.update(m["row_id"] for m in members)
        strategies.append(_merge(plan, members, grp, len(strategies) + 1))
    _log("F -> %d strategies from %d rows (%d shard errors)" % (len(strategies), len(rows), len(errors)))
    return strategies, [(e[1]) for e in errors]


def _merge(plan, members, grp, n):
    first = members[0]
    years = [m["target_year"] for m in members if m.get("target_year")]
    ty = min(years) if years else None
    # Not a union: PV2 learned that a union gives one strategy ten risks. Keep the risks most
    # of the merged statements name, most often named first, at most three.
    counts = collections.Counter(x for m in members for x in (m.get("related_risks") or []))
    risks = [x for x, c in counts.most_common() if c * 2 >= len(members)]
    best = next((m for m in members if m.get("quote_check") == quotes.VERBATIM), first)
    s = dict(plan.row())
    s.update(strategy_id="%s#s%d" % (plan.plan_id, n),
             name=(grp or {}).get("name") or first["name"],
             objective=(grp or {}).get("objective") or first["objective"],
             target_group=(grp or {}).get("target_group") or first["target_group"],
             instrument=(grp or {}).get("instrument") or first["instrument"],
             pillar=first.get("pillar", ""),
             statement_type="commitment" if any(m["statement_type"] == "commitment" for m in members)
             else "ongoing" if any(m["statement_type"] == "ongoing" for m in members) else "",
             related_risks=risks[:3], target_year=ty, horizon=horizon(ty, plan),
             place="; ".join(sorted({m["place"] for m in members if m.get("place")})),
             n_mentions=len(members), members=[m["row_id"] for m in members],
             refs=[m["ref"] for m in members], quote=best["quote"], quote_en=best["quote_en"],
             quote_check=best["quote_check"],
             quantified_targets=_union(m.get("quantified_targets") for m in members),
             named_agencies=_union(m.get("named_agencies") for m in members))
    s.update(_merge_class(members, s["related_risks"]))
    return s


def _union(lists):
    out = []
    for xs in lists:
        for x in xs or []:
            if x not in out:
                out.append(x)
    return out


def _strongest(values, order):
    """The first of `order` that any member holds: highest urgency, strongest status, basis."""
    return next((o for o in order if o in values), order[-1])


def _common(values):
    """The most common non-blank value, ties to the one named first."""
    vals = [v for v in values if v]
    if not vals:
        return ""
    counts = collections.Counter(vals)
    return next(v for v in vals if counts[v] == max(counts.values()))


def _merge_class(members, risks):
    """Step 4's fields for a folded strategy, merged the PV2 way (4_strategy_clean rule 9):
    union of SDG targets; the highest urgency; the strongest status and basis; the most common
    category and sector; the response of a member whose quote was found. Each kept risk keeps
    the quote of the first member that evidenced it."""
    targets = _union(m.get("sdg_targets") for m in members)
    scored = [m for m in members if m.get("response_orientation") in ("proactive", "transformative")]
    ori = _common([m["response_orientation"] for m in scored]) if scored else "BAU"
    ev_of = {}
    for m in members:
        for r, q in zip(m.get("related_risks") or [], m.get("risk_evidence") or []):
            ev_of.setdefault(r, q)
    sector = _common([m.get("sector") for m in members])
    return dict(
        risk_evidence=[ev_of.get(r, "") for r in risks],
        stated_urgency=_strongest({m.get("stated_urgency") for m in members}, vocab.URGENCIES),
        sdg_targets=targets, sdg_primary_dimension=vocab.primary_dimension(targets),
        response_orientation=ori,
        response_evidence=next((m["response_evidence"] for m in scored
                                if m["response_orientation"] == ori), ""),
        sector=sector, sector_canonical=vocab.sector_canonical(sector),
        institutional_lead=next((m["institutional_lead"] for m in members
                                 if m.get("institutional_lead")), ""),
        implementation_status=_strongest({m.get("implementation_status") for m in members},
                                         vocab.STATUSES),
        legal_or_plan_basis=_strongest({m.get("legal_or_plan_basis") for m in members}, vocab.BASES),
        **{yn: "Y" if any(m.get(yn) == "Y" for m in members) else "N"
           for yn in ("has_timeline", "has_quantified_target", "has_monitoring")})


# ================================================================ M: map onto the mother tree
def map_to_tree(client, plan, strategies, ctx, tree, out_dir):
    """Each strategy placed on the mother tree: same, differs or new, under the depth rule."""
    prompt = config.load_prompt("M")
    menu = tree.menu()
    doc_block = context_text(ctx, plan, max_chars=4000)
    batches = [strategies[i:i + MAP_BATCH] for i in range(0, len(strategies), MAP_BATCH)]
    _log("M: %d strategies in %d batch(es), tree %s" % (len(strategies), len(batches), tree.version))

    def build(batch):
        lines = ["%d | %s | %s | %s | %s | %s" % (
            i + 1, s["name"], s["objective"], s["target_group"] or "-", s["instrument"] or "-",
            s["quote_en"] or s["quote"]) for i, s in enumerate(batch)]
        # The tree comes first and is identical in every call, so the endpoint's prompt cache
        # serves it after the first batch.
        return "%s%sTHE TREE\n%s%sTHE DOCUMENT\n%s%sSTRATEGIES\n%s\n" % (
            prompt, SEP, menu, SEP, doc_block, SEP, "\n".join(lines))

    results, errors = client.map("M", batches, build, label="batch", expect="array")
    proposals = []
    for batch, res in zip(batches, results):
        answers = {}
        for a in res if isinstance(res, list) else []:
            if isinstance(a, dict):
                try:
                    answers[int(a.get("id"))] = a
                except (TypeError, ValueError):
                    continue
        for i, s in enumerate(batch):
            resolve(s, answers.get(i + 1), tree)
            if s["relation"] in ("differs", "new"):   # v1: no objective fits; v2: no node fits
                proposals.append({k: s.get(k, "") for k in PROPOSAL_COLUMNS})
    io.write_csv(os.path.join(out_dir, "strategies.csv"), strategies, STRATEGY_COLUMNS)
    io.write_csv(os.path.join(out_dir, "proposals.csv"), proposals, PROPOSAL_COLUMNS)
    counts = {}
    for s in strategies:
        counts[s["relation"]] = counts.get(s["relation"], 0) + 1
    _log("M -> %s; %d proposals for the tree" % (json.dumps(counts), len(proposals)))
    return strategies, proposals, [e[1] for e in errors]


def _resolve_v2(s, a, tree, node, text, notes):
    """Tree v2: no objectives to match, so the answer is a node and a proposed objective.

    The depth rule is tested here as the tree states it: a pathway needs its text cues in the
    strategy's wording, a mechanism its plan words; a claim without them steps up one level,
    and the reason is written on the row. A merged pathway becomes the sibling it merged into.
    """
    s["new_objective"] = _str(a.get("new_objective"))
    final = tree.canonical(node) if tree.level_of(node) else ""
    if node and not final:
        notes.append("node %s is not in the tree" % node)
    while final in tree.pathways or (final in tree.mid and tree.test_mid_cues):
        cue = tree.cue_matches(final, text)
        if cue:
            s["depth_basis"], s["depth_words"] = "strategy wording", cue
            break
        up = tree.parent_of(final)
        notes.append("held at %s: the wording carries none of %s's cues" % (up, final))
        final = up
    if final and not s["depth_basis"]:
        level = tree.level_of(final)
        s["depth_basis"] = (tree.level_names[1] if level == "L2" else
                            tree.level_names[0] if level == "L1" else "holding")
        if tree.required_level and level == "L1":
            # v3: a family is the required level; a group alone is a weak placement, counted.
            notes.append("%s only: a %s is required" % (tree.level_names[0], tree.level_names[1]))
    s["relation"] = "placed" if final else "new"
    if not final:
        s["proposal"] = _str(a.get("proposal")) or (
            "no node fits: %s" % (s["new_objective"] or s["objective"]))
    return final


def resolve(s, a, tree):
    """Apply one model answer to one strategy under the tree's own rules, in place."""
    s.update(tree_version=tree.version, relation="unmapped", objective_id="", tree_objective="",
             new_objective="", node_id="", level="", depth_basis="", depth_words="",
             group_id="", group="", family_id="", family="", mechanism_id="", mechanism="",
             pathway_id="", pathway="", subpillar="", pillar_rhdr="", target_id="", target_label="", instrument_id="",
             instrument_label="", proposal="", confidence="", map_note="")
    if not a:
        s["map_note"] = "no answer for this strategy"
        return s
    notes = []
    oid = _str(a.get("objective_id"))
    node = _str(a.get("node_id"))
    # The cue gate reads the strategy's own words only. The model's depth_words are not added:
    # a cue it could pass with its own wording is no gate.
    text = " ".join([s.get("name", ""), s.get("objective", ""), s.get("quote_en", ""), s.get("quote", "")])
    if not tree.objectives:
        final = _resolve_v2(s, a, tree, node, text, notes)
    elif oid and oid != "NEW" and oid in tree.objectives:
        base, level = tree.node_of_objective(oid)
        s.update(relation="same", objective_id=oid,
                 tree_objective=tree.objectives[oid]["objective"], depth_basis="inherited from objective")
        final = base
        if level == "L2" and node in tree.mechanisms and tree.family_of(node) == base:
            cue = tree.cue_matches(node, text)
            if cue:
                final, s["depth_basis"], s["depth_words"] = node, "deepened by strategy wording", cue
            else:
                notes.append("deepening to %s refused: its wording carries none of the "
                             "mechanism's cues" % node)
        elif node and node != base:
            notes.append("answer placed it at %s; kept at its objective's node" % node)
    else:
        if oid and oid != "NEW":
            notes.append("objective %s is not in the tree" % oid)
        s["new_objective"] = _str(a.get("new_objective"))
        final = node if tree.level_of(node) else ""
        if node and not final:
            notes.append("node %s is not in the tree" % node)
        if final in tree.mechanisms:
            cue = tree.cue_matches(final, text)
            if cue:
                s["depth_basis"], s["depth_words"] = "strategy wording", cue
            else:
                notes.append("held at the family: the wording carries none of %s's cues" % final)
                final = tree.family_of(final)
                s["depth_basis"] = "family (no cue for the mechanism)"
        elif final:
            s["depth_basis"] = "family" if tree.level_of(final) == "L2" else "holding"
        s["relation"] = "differs" if final else "new"
        s["proposal"] = _str(a.get("proposal")) or (
            "new objective under %s: %s" % (final, s["new_objective"]) if final else
            "no node fits: %s" % (s["new_objective"] or s["objective"]))
    s["node_id"], s["level"] = final, tree.level_of(final)
    d = tree.describe(final) if final else {}
    s.update(group_id=d.get("group_id", ""), group=d.get("group", ""),
             family_id=d.get("family_id", ""), family=d.get("family", ""),
             mechanism_id=d.get("mechanism_id", ""), mechanism=d.get("mechanism", ""),
             pathway_id=d.get("pathway_id", ""), pathway=d.get("pathway", ""),
             # The official RHDR category and pillar: the tree's own, never a separate guess.
             subpillar=d.get("subpillar", ""), pillar_rhdr=d.get("pillar", ""))
    tid, iid = _str(a.get("target_id")), _str(a.get("instrument_id"))
    if tid in tree.targets:
        s["target_id"], s["target_label"] = tid, tree.targets[tid]["label"]
    if iid in tree.instruments:
        s["instrument_id"], s["instrument_label"] = iid, tree.instruments[iid]["label"]
    conf = _str(a.get("confidence")).lower()
    s["confidence"] = conf if conf in ("high", "medium", "low") else ""
    s["map_note"] = "; ".join(notes)
    return s
