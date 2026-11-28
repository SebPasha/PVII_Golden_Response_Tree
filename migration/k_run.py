"""Step K: write each country's key messages from its plan's chains (gpt-5.4, one call a plan).

    cd migration
    python3 k_run.py ../data/migration_out key_messages/out [--plan-dir <workflow plan folder> ...]
                     [--compare <plan_id> <plan_id>] [--only brazil,thailand] [--dry-run] [--max-cost 20]

For every country on the page it takes the latest national plan (else the latest vision), builds the
chains with key_messages.py (no model calls), and asks for four to six key messages, each one chain:
risks and advantages -> mechanism (lever) -> objective (Growth, Wellbeing, Governance) -> instrument ->
target group, plus the comparative advantages and megatrend opportunities the strategies show. A
--plan-dir (a workflow run, data/plans/<plan_id>/) is used in place of the page's edition with the same
plan_id, or added beside it; its context.json gives the advantages step C read from the document.
--compare writes one comparison of two plans of the same country. Answers are cached like the mapping's.
Writes <out>/<plan_id>.json per plan, <out>/compare_<a>_vs_<b>.json, and <out>/key_messages.json (all).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "workflow"))
import key_messages as km  # noqa: E402
from pvii import config, llm, steps  # noqa: E402

MAX_FAMILIES, MAX_STRATEGIES = 16, 8

PROMPT = """Role

Development economist writing the key messages of one country's national development plan for a regional
human development report (RHDR).

Input

The plan's strategies, grouped by mechanism family on a policy tree. Each family carries its RHDR objective
(Growth, Wellbeing or Governance), the levers (literature-backed mechanisms) its strategies sit on, the
megatrend risks they respond to, their instruments, the groups they target, their weight in the plan
(mentions) and the national budget placed on the family where there is one (billions of the national
currency, by year). Then how the plan covers the eleven megatrends, and, where there is one, what the plan document
itself says about the country's strengths and opportunities.

Task

1. comparative_advantages: up to six things the country is good at or endowed with that the plan builds on
   (natural resources, location, energy, industries, institutions, people, platforms). Name only what the
   strategies or the document show; give the strategy names or the document quote as evidence.
2. opportunities: for each megatrend the plan treats as a chance as well as a threat, one line on the
   opportunity, with the strategies that pursue it. Leave out megatrends the plan only defends against.
3. messages: four to six key messages that together cover most of the plan's weight. Each is one chain:
   - title: three to six words;
   - objective: Growth, Wellbeing or Governance;
   - sentence: one sentence of the form "Facing <risks or domestic pressures>, and building on <advantage>,
     <country> works through <mechanism> to <objective>, using <instruments> for <groups>." Keep it under 55
     words. Drop the advantage clause where none applies;
   - risks: the megatrends it answers (names from the eleven), or [] when it answers domestic pressures;
   - pressures: the domestic, non-macroeconomic pressures in plain words, where the plan names them;
   - advantage: the comparative advantage it builds on, or "";
   - families: the family ids it joins (from the input only); levers: the lever ids (from the input only);
   - instruments: the main instruments in plain words, with their class in brackets where given;
   - targets: the groups of people it is for;
   - gap: one sentence on what is missing, where something is: a megatrend named but not answered, only
     Information instruments where the problem needs money or rules, a priority with little or no budget,
     no group named. "" when nothing stands out.
4. summary: two sentences on what the plan as a whole bets on.

Use only the input. Do not invent numbers. Write in plain English. Say RHDR, never HDI.

Output

A valid JSON object only, no markdown and no commentary:

{"comparative_advantages": [{"advantage": "", "evidence": [""]}],
 "opportunities": [{"megatrend": "", "opportunity": "", "evidence": [""]}],
 "messages": [{"title": "", "objective": "", "sentence": "", "risks": [], "pressures": "", "advantage": "",
               "families": [], "levers": [], "instruments": [], "targets": [], "gap": ""}],
 "summary": ""}
"""

COMPARE = """Role

Development economist comparing two national development plans of the same country, made by different
governments, for a regional human development report (RHDR).

Input

For each plan: its period, its key messages (each a chain from risks through a mechanism to an objective,
instrument and target group), its weight by RHDR objective, and its mechanism families with their weight.

Task

Compare the two plans on the chain, not on rhetoric:
- continuity: up to four mechanisms both plans rely on, with how their weight or instruments changed;
- added: up to four mechanisms or target groups only the later plan has;
- dropped: up to four only the earlier plan has;
- instruments: one or two sentences on how the mix of Money, Authority, Information and Organisation moved;
- risks: one or two sentences on which megatrends each plan answers;
- headline: two sentences a reader can take away.
Use only the input, plain English, no numbers that are not in it. Say RHDR, never HDI.

Output

A valid JSON object only:

{"headline": "", "continuity": [{"mechanism": "", "change": ""}], "added": [{"item": "", "note": ""}],
 "dropped": [{"item": "", "note": ""}], "instruments": "", "risks": ""}
"""


def latest_plans(out_dir):
    plans = {}
    excluded = json.load(open(os.path.join(HERE, "excluded_plans.json"), encoding="utf-8"))
    for r in km.load(os.path.join(out_dir, "plans.csv"),
                     lambda r: r["doc_type"] in ("ndp", "vision") and r["plan_id"] not in excluded):
        # The latest national plan with enough strategies to say something (else the latest vision).
        key = (r["doc_type"] == "ndp", int(r["n_strategies"] or 0) >= 30, int(r["period_end"] or 0),
               int(r["period_start"] or 0))
        if r["slug"] not in plans or key > plans[r["slug"]][0]:
            plans[r["slug"]] = (key, r["plan_id"])
    return {s: p for s, (_, p) in plans.items()}


def chain_text(res, ctx):
    lines = ["Country: %s" % res["country"], "Plan: %s (%s), %s" % (res["title"], res["doc_type"], res["period"]),
             "Strategies: %d, mentions: %d, weight by objective (strategies): %s" % (
                 res["strategies"], res["mentions"], json.dumps(res["objectives"])), "", "FAMILIES"]
    for c in res["chains"][:MAX_FAMILIES]:
        lines.append("- %s | %s | group %s | objective %s | share %.1f%% | mentions %d" % (
            c["family_id"], c["family"], c["group"] or "-", c["objective"], 100 * c["share"], c["mentions"]))
        if c["levers"]:
            lines.append("  levers: " + "; ".join("%s (%d)" % (k, n) for k, n in c["levers"][:6]))
        if c["risks"]:
            lines.append("  risks: " + "; ".join("%s (%d)" % (k, n) for k, n in c["risks"]))
        if c["instruments"]:
            lines.append("  instruments: " + "; ".join(k for k, _ in c["instruments"]))
        if c["targets"]:
            lines.append("  targets: " + "; ".join(k for k, _ in c["targets"]))
        if c["budget_bn"]:
            lines.append("  budget (bn, by year): " + json.dumps(c["budget_bn"]))
        for s in c["strategies"][:MAX_STRATEGIES]:
            lines.append("    * %s (%d)%s" % (s["name"], s["mentions"], (" [%s]" % ", ".join(s["risks"])) if s["risks"] else ""))
    lines += ["", "MEGATRENDS (strategies, mentions)"]
    for m, v in res["risk_coverage"].items():
        lines.append("- %s: %d, %d" % (m, v["strategies"], v["mentions"]))
    if ctx:
        lines += ["", "WHAT THE DOCUMENT SAYS"]
        for a in ctx.get("comparative_advantages") or []:
            lines.append("- advantage: %s | %s" % (a.get("advantage", ""), a.get("quote", "")))
        for o in ctx.get("opportunities") or []:
            lines.append("- opportunity (%s): %s | %s" % (o.get("risk", ""), o.get("opportunity", ""), o.get("quote", "")))
        rf = ctx.get("risk_framing") or {}
        if rf.get("summary"):
            lines.append("- risk framing: " + rf["summary"])
    return "\n".join(lines)


def clean(ans, res):
    fams = {c["family_id"] for c in res["chains"]}
    levs = {k.split(" ")[0] for c in res["chains"] for k, _ in c["levers"]}
    weight = {c["family_id"]: c["mentions"] for c in res["chains"]}
    ans = ans if isinstance(ans, dict) else {}
    for m in ans.get("messages") or []:
        m["families"] = [f for f in m.get("families") or [] if f in fams]
        m["levers"] = [x for x in m.get("levers") or [] if x in levs]
        m["risks"] = [x for x in m.get("risks") or [] if x in km.MEGATRENDS]
        m["mentions"] = sum(weight[f] for f in m["families"])
        m["share"] = round(m["mentions"] / (res["mentions"] or 1), 3)
        if m.get("objective") not in ("Growth", "Wellbeing", "Governance"):
            m["objective"] = ""
    return ans


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir")
    ap.add_argument("dest")
    ap.add_argument("--plan-dir", action="append", default=[])
    ap.add_argument("--compare", nargs=2, action="append", default=[])
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-cost", type=float, default=20.0)
    ap.add_argument("--concurrency", type=int, default=6)
    a = ap.parse_args()
    os.makedirs(a.dest, exist_ok=True)
    todo = {}                                         # plan_id -> (source, context)
    for slug, pid in latest_plans(a.out_dir).items():
        todo[pid] = (pid, None)
    for d in a.plan_dir:
        res = km.build(a.out_dir, d)
        ctx_path = os.path.join(d, "context.json")
        todo[res["plan"]] = (d, json.load(open(ctx_path, encoding="utf-8")) if os.path.exists(ctx_path) else None)
    if a.only:
        keep = {s.strip() for s in a.only.split(",")}
        todo = {p: v for p, v in todo.items() if p.split("_")[0] in keep or any(p.startswith(k + "_") for k in keep)}
    built = {pid: (km.build(a.out_dir, src), ctx) for pid, (src, ctx) in sorted(todo.items())}
    items = sorted(built)
    print("%d plans, %d calls" % (len(items), len(items) + len(a.compare)), flush=True)

    ledger = llm.Ledger(a.max_cost, config.MAX_CALLS, dry_run=a.dry_run)
    client = llm.LLMClient(ledger, dry_run=a.dry_run)
    try:
        results, errors = client.map("K", items, lambda pid: PROMPT + steps.SEP + chain_text(*built[pid]),
                                     model=config.MODEL_LARGE, label="plan", expect="object",
                                     concurrency=a.concurrency, max_tokens=8000)
    except (llm.BudgetExceeded, llm.StageAborted) as e:
        print(ledger.report())
        print("STOPPED: %s (answers so far are cached; run again to finish)" % e)
        return 1
    allout = {}
    if not a.dry_run:
        for pid, ans in zip(items, results):
            res, ctx = built[pid]
            out = {**res, "context": {k: (ctx or {}).get(k) for k in ("comparative_advantages", "opportunities", "risk_framing")}
                   if ctx else None, "k": clean(ans, res)}
            out["chains"] = [{**c, "strategies": c["strategies"][:15]} for c in out["chains"]]
            json.dump(out, open(os.path.join(a.dest, pid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            allout[pid] = out
    for p1, p2 in a.compare:
        def side(pid):
            o = allout.get(pid) or {}
            return {"plan": pid, "period": o.get("period"), "objectives": o.get("objectives"),
                    "messages": (o.get("k") or {}).get("messages"),
                    "families": [{"family": c["family"], "objective": c["objective"], "share": c["share"],
                                  "instrument_classes": c["instrument_classes"]} for c in o.get("chains", [])[:20]]}
        prompt = COMPARE + steps.SEP + json.dumps({"earlier": side(p1), "later": side(p2)}, ensure_ascii=False)
        try:
            ans = client.call("K", prompt, model=config.MODEL_LARGE, max_tokens=6000, expect="object")
        except Exception as e:                       # noqa: BLE001
            print("compare %s vs %s failed: %s" % (p1, p2, e))
            continue
        if not a.dry_run:
            json.dump({"earlier": p1, "later": p2, **(ans or {})},
                      open(os.path.join(a.dest, "compare_%s_vs_%s.json" % (p1, p2)), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
    print(ledger.report(), flush=True)
    if not a.dry_run:
        json.dump(allout, open(os.path.join(a.dest, "key_messages.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("wrote %d plans to %s (%d errors)" % (len(allout), a.dest, len(errors)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
