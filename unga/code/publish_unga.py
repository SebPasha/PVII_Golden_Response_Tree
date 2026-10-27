#!/usr/bin/env python3
"""Publish a country's UNGA statement layer to Supabase: its own tables, its own run.

    python -m pv2.publish.unga --country india --dry-run   # the payload, sent nowhere
    python -m pv2.publish.unga --country india
    python -m pv2.publish.unga --all                        # every country holding stage 8 outputs

WHAT THIS LAYER IS
Stage 8 reads each General Debate statement whole and records, for all 11 risks and all 15
HDI categories, what the government told the Assembly, with a quoted passage and its page.
This loads that into the 0018 tables under a run keyed by a hash of the workbook, so the same
outputs replace the same run and a bad run is deleted by its own id.

It is the sector publisher's shape (publish/sector.py) and for the same reasons: a separate
cadence from the panel, a separate run, and a join back that lives in views.

NO AMOUNTS. Nothing here writes money, and 0018's tables have no column that could hold it.

EXIT CODE
    0  published, or the dry run written
    1  nothing to publish for this country
    2  could not reach Supabase, or 0018 is not applied
"""
import argparse
import datetime
import json
import os
import sys

from pv2 import country
from pv2.extract import config, stages, writer
from pv2.publish import artifacts, db

TABLES = ("unga_statements", "unga_risk_grid", "unga_hdi")


class PublishError(Exception):
    """Reported and exited on; nothing is half-written."""


def _text(v):
    s = "" if v is None else str(v).strip()
    return s.replace("\x00", "") or None


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _bool(v):
    """writer.py stores a boolean as Y or N; anything else true-looking is accepted too."""
    return str(v).strip().lower() in ("y", "yes", "true", "1")


def outputs(slug):
    cfg = country.load(slug)
    return stages.unga_path(cfg.out("stages") if cfg else config.resolve("data/llm/%s" % slug),
                            slug)


def sources(slug):
    """{file name: (storage_path, sha256)} from the fetch manifest, else hashed from disk."""
    dest = config.resolve("data/sources/%s" % slug)
    out = {}
    manifest = os.path.join(dest, "manifest.json")
    if os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as f:
            for e in json.load(f).get("files", []):
                if isinstance(e, dict) and str(e.get("path", "")).startswith("unga/"):
                    out[e["name"]] = (e.get("bucket_key"), e.get("sha256"))
    folder = os.path.join(dest, "unga")
    for name in (os.listdir(folder) if os.path.isdir(folder) else []):
        if name not in out and name.lower().endswith(".pdf"):
            out[name] = (None, artifacts.sha256(os.path.join(folder, name)))
    return out


def build(slug):
    """Everything to write for one country's UNGA layer, read from disk. No network."""
    cfg = country.load(slug)
    if not cfg:
        raise PublishError("no country config for %s" % slug)
    path = outputs(slug)
    if not os.path.exists(path):
        raise PublishError("no stage 8 outputs for %s. Run:\n"
                           "  python3 runbook/07_unga.py --country %s --extract" % (slug, slug))
    statements = writer.read_rows(path, "statements")
    risks = writer.read_rows(path, "risks")
    hdi = writer.read_rows(path, "hdi")
    if not statements or len(risks) != 11 * len(statements) or len(hdi) != 15 * len(statements):
        raise PublishError(
            "%s: the workbook is not a whole grid (%d statements, %d risk rows, %d hdi rows); "
            "stage 8 writes 11 and 15 per statement, so this is a damaged or partial file"
            % (slug, len(statements), len(risks), len(hdi)))
    src = sources(slug)
    prompt = os.path.join(config.PROMPTS_DIR, config.PROMPT_FILES["8"])
    run = {"country_slug": slug, "run_key": artifacts.sha256(path),
           "started_at": datetime.datetime.fromtimestamp(
               os.path.getmtime(path), datetime.timezone.utc).isoformat(),
           "statements": len(statements),
           "refused": max(0, len(cfg.unga) - len(statements)),
           "prompt_sha": artifacts.sha256(prompt),
           "model": config.STAGE_MODELS.get("8")}
    rows_s = []
    for s in statements:
        storage, sha = src.get(_text(s.get("file")) or "", (None, None))
        rows_s.append({"doc_name": _text(s.get("doc_name")), "file": _text(s.get("file")),
                       "statement_year": _int(s.get("statement_year")),
                       "storage_path": storage, "sha256": sha,
                       "pages": _int(s.get("pages")), "parser": _text(s.get("parser")),
                       "language": _text(s.get("language")),
                       "speaker_name": _text(s.get("speaker_name")),
                       "speaker_role": _text(s.get("speaker_role")),
                       "statement_summary": _text(s.get("statement_summary")),
                       "risks_engaged": _int(s.get("risks_engaged")),
                       "hdi_advanced": _int(s.get("hdi_advanced"))})
    rows_r = [{"doc_name": _text(r.get("doc_name")),
               "statement_year": _int(r.get("statement_year")),
               "risk": _text(r.get("category")), "salience": _text(r.get("salience")),
               "direction": _text(r.get("direction")), "evidence": _text(r.get("evidence")),
               "evidence_page": _int(r.get("evidence_page")),
               "evidence_translated": _bool(r.get("evidence_translated")),
               "rationale": _text(r.get("rationale"))} for r in risks]
    rows_h = [{"doc_name": _text(h.get("doc_name")),
               "statement_year": _int(h.get("statement_year")),
               "category": _text(h.get("category")), "present": _bool(h.get("present")),
               "salience": _text(h.get("salience")), "evidence": _text(h.get("evidence")),
               "evidence_page": _int(h.get("evidence_page")),
               "evidence_translated": _bool(h.get("evidence_translated")),
               "rationale": _text(h.get("rationale"))} for h in hdi]
    return {"slug": slug, "country": cfg.name, "run": run, "unga_statements": rows_s,
            "unga_risk_grid": rows_r, "unga_hdi": rows_h,
            "_out_dir": os.path.dirname(path)}


def dump(payload):
    where = os.path.join(payload["_out_dir"], "publish_payload")
    os.makedirs(where, exist_ok=True)
    for name in ("run",) + TABLES:
        with open(os.path.join(where, "%s.json" % name), "w", encoding="utf-8") as f:
            json.dump(payload[name], f, indent=1, default=str, ensure_ascii=False)
    return where


def push(payload, client):
    """Upsert the run, then replace its rows. Returns (unga_run_id, counts)."""
    client.insert("countries", [{"slug": payload["slug"], "country": payload["country"]}],
                  on_conflict="slug")
    got = client.insert("unga_runs", [payload["run"]], on_conflict="country_slug,run_key",
                        returning=True)
    if not got:
        raise PublishError("Supabase accepted the UNGA run but returned no row")
    run_id = got[0]["id"]
    for table in TABLES:            # replace, never append: the same outputs twice is one run
        client.delete(table, {"unga_run_id": "eq.%s" % run_id})
    counts = {}
    for table in TABLES:
        rows = [dict(r, unga_run_id=run_id) for r in payload[table]]
        if rows:
            client.insert(table, rows)
        counts[table] = len(rows)
    return run_id, counts


def publish_country(slug, dry_run=False):
    payload = build(slug)
    run = payload["run"]
    years = sorted(y for y in (s["statement_year"] for s in payload["unga_statements"]) if y)
    print("\n=== %s ===" % payload["country"])
    print("  statements  %d (%s), %d refused" % (run["statements"],
                                                ", ".join(map(str, years)) or "no years",
                                                run["refused"]))
    print("  risk grid   %d rows, %d engaged" % (
        len(payload["unga_risk_grid"]),
        sum(1 for r in payload["unga_risk_grid"] if r["direction"] != "absent")))
    print("  hdi         %d rows, %d present" % (
        len(payload["unga_hdi"]), sum(1 for h in payload["unga_hdi"] if h["present"])))
    if dry_run:
        where = dump(payload)
        print("  DRY RUN, nothing sent. Payload -> %s" % os.path.relpath(where, config.PV2_ROOT))
        return 0
    client = db.connect()
    try:
        run_id, counts = push(payload, client)
    except db.DBError as e:
        if "unga_" in str(e) or "does not exist" in str(e) or "schema cache" in str(e):
            print("\nFAILED: %s\n  -> apply workflow/supabase/migrations/0018_unga_layer.sql "
                  "in the SQL editor first." % e, file=sys.stderr)
            return 2
        raise
    print("  published   %s" % run_id)
    for table, n in sorted(counts.items()):
        print("    %-18s %d" % (table, n))
    return 0


def held_slugs():
    return [s for s in country.all_slugs() if os.path.exists(outputs(s))]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", action="append", default=[])
    ap.add_argument("--all", action="store_true", help="every country holding stage 8 outputs")
    ap.add_argument("--dry-run", action="store_true", help="write the payload, send nothing")
    a = ap.parse_args(argv)
    slugs = held_slugs() if a.all else a.country
    if not slugs:
        ap.error("name --country or pass --all")
    worst = 0
    for s in slugs:
        try:
            worst = max(worst, publish_country(s, dry_run=a.dry_run))
        except PublishError as e:
            print("%s: %s" % (s, e), file=sys.stderr)
            worst = max(worst, 1)
    return worst


if __name__ == "__main__":
    sys.exit(main())
