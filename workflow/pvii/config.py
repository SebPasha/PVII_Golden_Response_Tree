"""Paths, credentials, model routing, prices, caps and temperatures.

Lifted from PV2 workflow/pv2/extract/config.py, cut down to the four steps this workflow runs.
Credentials live in workflow/.env (gitignored), or in the environment. Nothing here prints a key.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))              # workflow/pvii
WORKFLOW = os.path.dirname(HERE)                               # workflow/
ROOT = os.path.dirname(WORKFLOW)                               # the repo
PROMPTS_DIR = os.path.join(WORKFLOW, "prompts")
CONFIGS_DIR = os.environ.get("PVII_CONFIGS") or os.path.join(WORKFLOW, "configs")
TREE_DIR = os.environ.get("PVII_TREE") or os.path.join(ROOT, "tree", "v1")
TREE_INPUTS = os.path.join(ROOT, "tree", "inputs")
# Outputs: data/plans/<plan_id>/, data/country/<slug>/, data/global/. Gitignored.
DATA_DIR = os.environ.get("PVII_DATA") or os.path.join(ROOT, "data")


def _load_dotenv():
    path = os.path.join(WORKFLOW, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


def _env(name, default=None, required=False):
    """The environment value, treating blank as absent so the default applies."""
    v = os.environ.get(name)
    if v is None or not str(v).strip():
        v = default
    if required and not v:
        sys.exit(f"ERROR: {name} is not set. Copy workflow/.env.example to workflow/.env.")
    return v


# The source library (the 3.3GB of plans git does not carry). A config names each document as
# data/sources/<slug>/..., the layout PV2 uses, so pointing this at PV2/data reuses that library
# and its parse cache as they are.
SOURCES_ROOT = _env("PVII_SOURCES_ROOT", os.path.join(ROOT, "data"))
# The parse and response cache, this workflow's own.
CACHE_DIR = _env("PVII_CACHE_DIR", os.path.join(DATA_DIR, "cache"))
RECORD_DIR = _env("PVII_RECORD_DIR", "")
# A second parse cache, read and never written: PV2/data/cache on the machine that holds it.
# Every Document Intelligence parse PV2 paid for is reused, keyed on the file's own hash.
PARSE_CACHE_FALLBACK = _env("PVII_PARSE_CACHE_FALLBACK", "")


def resolve(p):
    """A document path from a config made absolute. data/... resolves under SOURCES_ROOT."""
    if not p:
        return None
    if os.path.isabs(p):
        return p
    parts = os.path.normpath(p).split(os.sep)
    if parts[0] == "data":
        return os.path.join(SOURCES_ROOT, *parts[1:])
    return os.path.normpath(os.path.join(ROOT, p))


def openai_config(required=True):
    return {"base_url": _env("OPENAI_BASE_URL", required=required),
            "api_key": _env("AZURE_API_KEY", required=required)}


def docint_config(required=True):
    return {"endpoint": _env("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", required=required),
            "key": _env("AZURE_DOCUMENT_INTELLIGENCE_KEY", required=required)}


# Small model for per-chunk work, large model where the judgement spans the document or the tree.
MODEL_SMALL = _env("OPENAI_MODEL", "gpt-5.4-mini")
MODEL_LARGE = _env("OPENAI_MODEL_ALL_AT_ONCE", "gpt-5.4")
STAGE_MODELS = {"C": MODEL_LARGE, "C_reduce": MODEL_LARGE, "E": MODEL_SMALL,
                "F": MODEL_LARGE, "M": MODEL_LARGE}

# Output budget per step; a response cut off at the cap is retried larger, up to the ceiling.
STAGE_MAX_TOKENS = {"C": 8000, "C_reduce": 8000, "E": 16000, "F": 16000, "M": 16000}
MAX_OUTPUT_CEILING = 64000

# USD per 1M tokens; affects estimates and the spend cap only.
PRICES = {MODEL_SMALL: (float(_env("PRICE_GPT_5_4_MINI_IN", "0.25")),
                        float(_env("PRICE_GPT_5_4_MINI_OUT", "2.00"))),
          MODEL_LARGE: (float(_env("PRICE_GPT_5_4_IN", "1.25")),
                        float(_env("PRICE_GPT_5_4_OUT", "10.00")))}


def price_for(model):
    return PRICES.get(model, PRICES[MODEL_LARGE])     # unknown: price it like the dear one


# Caps for one invocation. Breaching either aborts the run rather than trimming it.
MAX_COST_USD = float(_env("PVII_MAX_COST_USD", "25.0"))
MAX_CALLS = int(_env("PVII_MAX_CALLS", "50000"))
CONCURRENCY = int(_env("PVII_CONCURRENCY", "0"))
STAGE_CONCURRENCY = {"E": 16, "C": 2, "C_reduce": 1, "F": 4, "M": 4}


def concurrency_for(stage):
    return CONCURRENCY or STAGE_CONCURRENCY.get(str(stage), 4)


STAGE_TIME_BUDGET_S = int(_env("PVII_STAGE_TIME_BUDGET", "300"))
FAILURE_RATE_ABORT = 0.20        # a step whose calls fail at this rate has a broken prompt


def failure_rate_abort_for(stage):
    return FAILURE_RATE_ABORT


MAX_RETRIES = 4
# PVII_OFFLINE=1: every call must come from the cache; a miss raises instead of spending.
OFFLINE = str(_env("PVII_OFFLINE", "")).strip().lower() in ("1", "true", "yes")

# Extraction runs at 0, judgement at 0.2. Temperature is part of the cache key.
STAGE_TEMPERATURES = {"C": 0.0, "C_reduce": 0.0, "E": 0.0, "F": 0.2, "M": 0.2}
TEMPERATURE = 0.0


def temperature_for(stage):
    return STAGE_TEMPERATURES.get(str(stage), TEMPERATURE)


# The eleven PV II risks. Fixed English values, used by E and checked in Python.
RISKS = ["Climate Change", "Pandemics", "Biodiversity Loss",
         "Environmental Degradation and Pollution", "Resource and Energy Pressures",
         "Shifts in Globalisation", "Technological Change", "Demographic Shifts",
         "Democratic Backsliding", "Growing Populism", "Increased Polarisation"]

PROMPT_FILES = {"C": "C_context.txt", "C_reduce": "C_context_reduce.txt",
                "E": "E_extract.txt", "F": "F_fold.txt", "M": "M_map.txt"}


def load_prompt(stage):
    with open(os.path.join(PROMPTS_DIR, PROMPT_FILES[stage]), encoding="utf-8") as f:
        return f.read()
