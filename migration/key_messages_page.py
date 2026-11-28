"""Build the key messages page from step K's answers. No model calls.

    cd migration && python3 key_messages_page.py key_messages/out key_messages/page.html

Inlines <out>/key_messages.json (trimmed) and every <out>/compare_*.json into key_messages_template.html.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reshape_common import REGION  # noqa: E402


def region(slug, given):
    if given:
        return given
    if slug in REGION:
        return REGION[slug]
    p = os.path.join(HERE, "added", slug, "region.txt")
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else "Other"


def trim(o):
    keep = ("family_id", "family", "group", "objective", "mentions", "share", "levers", "risks", "instruments",
            "instrument_classes", "targets", "budget_bn")
    chains = [{**{k: c[k] for k in keep}, "strategies": [s["name"] for s in c["strategies"][:5]]}
              for c in o["chains"][:18]]
    return {"plan": o["plan"], "country": o["country"], "slug": o["slug"], "region": region(o["slug"], o.get("region")),
            "title": o.get("title", ""), "period": o.get("period", ""), "doc_type": o.get("doc_type", ""),
            "strategies": o["strategies"], "mentions": o["mentions"], "on_a_lever": o["on_a_lever"],
            "objectives": o["objectives"], "budget_years": o.get("budget_years", []),
            "risk_coverage": {m: [v["strategies"], v["mentions"]] for m, v in o["risk_coverage"].items()},
            "context": o.get("context"), "k": o.get("k") or {}, "chains": chains}


def main():
    src, dest = sys.argv[1], sys.argv[2]
    data = json.load(open(os.path.join(src, "key_messages.json"), encoding="utf-8"))
    plans = {pid: trim(o) for pid, o in data.items()}
    comps = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(src, "compare_*.json")))]
    html = open(os.path.join(HERE, "key_messages_template.html"), encoding="utf-8").read()
    blob = json.dumps({"plans": plans, "compare": comps}, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*DATA*/null", blob)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote %s: %d plans, %d comparisons, %.0f KB" % (dest, len(plans), len(comps), len(html) / 1024))


if __name__ == "__main__":
    main()
