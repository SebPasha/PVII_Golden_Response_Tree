"""Step 0: the register. One config per country, one entry per document, each with its period.

The unit of work is a single plan edition. PV2 listed every plan a country has in one `ndp`
list and read them as one corpus, which is why time never held: strategies were merged across
editions and joined to budget years their plan never covered. Here a document carries its own
type, period and language, and its plan_id carries the period into every row it produces.

    plan_id = <slug>_<doc_type>_<start>-<end>        e.g. thailand_ndp_2023-2027

A document runs only when it has both years and no `skip`. One that lacks a year says so in
`needs`, and is listed by `--list` rather than guessed.
"""
import json
import os
import re

from pvii import config

RUNNABLE = ("ndp", "vision", "sector")     # budget and unga are the parked lanes


class Plan:
    def __init__(self, slug, country, entry):
        self.slug, self.country, self.entry = slug, country, entry
        # A plan published as several files (Brazil's PPA annexes) lists them under `files`;
        # they are read as one document, in the order given.
        self.files = list(entry.get("files") or ([entry["file"]] if entry.get("file") else []))
        self.file = " + ".join(self.files)
        self.doc_type = entry.get("doc_type") or ""
        self.start, self.end = entry.get("start"), entry.get("end")
        self.language = entry.get("language") or ""
        self.title = entry.get("title") or os.path.basename(self.file)
        self.edition = entry.get("edition") or ""
        self.published = ""   # set from the context file (step C)

    @property
    def plan_id(self):
        if self.start is None or self.end is None:
            return ""
        tag = ""
        if self.doc_type == "sector":
            # Two sector plans can share a country and a period; the title tells them apart.
            tag = "_" + re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")[:40]
        return "%s_%s_%d-%d%s" % (self.slug, self.doc_type, int(self.start), int(self.end), tag)

    @property
    def paths(self):
        return [config.resolve(f) for f in self.files]

    def why_not_runnable(self):
        if self.entry.get("skip"):
            return "skip: " + self.entry["skip"]
        if self.doc_type not in RUNNABLE:
            return "doc_type %r is not run by this workflow" % self.doc_type
        if self.start is None or self.end is None:
            return "needs " + (self.entry.get("needs") or "a start and end year")
        if int(self.start) > int(self.end):
            return "start %s is after end %s" % (self.start, self.end)
        return ""

    def row(self):
        """The columns every output row of this plan carries."""
        return {"plan_id": self.plan_id, "country": self.country, "slug": self.slug,
                "doc_type": self.doc_type, "edition": self.edition, "plan_title": self.title,
                "period_start": self.start, "period_end": self.end, "published": self.published,
                "language": self.language}

    def __repr__(self):
        return "<Plan %s>" % (self.plan_id or self.file)


def load_country(slug, configs_dir=None):
    path = os.path.join(configs_dir or config.CONFIGS_DIR, "%s.json" % slug)
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    return [Plan(cfg["slug"], cfg["country"], e) for e in cfg.get("documents") or []]


def countries(configs_dir=None):
    d = configs_dir or config.CONFIGS_DIR
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def find(plan_id, configs_dir=None):
    """The Plan for a plan_id, from the config of the country it names."""
    slug = plan_id.split("_", 1)[0]
    # A skipped duplicate (China's Chinese originals) shares its English edition's plan_id;
    # the runnable one is the one meant.
    hits = [p for p in load_country(slug, configs_dir) if p.plan_id == plan_id]
    for p in sorted(hits, key=lambda p: bool(p.why_not_runnable())):
        return p
    raise KeyError("no document in configs/%s.json has plan_id %s" % (slug, plan_id))


def runnable(slug, doc_types=None, configs_dir=None):
    out = []
    for p in load_country(slug, configs_dir):
        if p.why_not_runnable():
            continue
        if doc_types and p.doc_type not in doc_types:
            continue
        out.append(p)
    return out


def plan_dir(plan_id):
    return os.path.join(config.DATA_DIR, "plans", plan_id)
