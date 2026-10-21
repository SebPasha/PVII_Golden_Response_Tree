"""Is a quote really in the paragraph it cites?

Lifted from PV2: normalise, despace and overlap from validate/evidence.py, and fold, trigrams,
english_share, match_quote and classify from validate/truth.py, with their reasons. Nothing
else from those modules is needed here: the paragraph a quote cites is the chunk the model was
given, so ground truth is always in hand.

Four tiers, each a weaker claim than the last: verbatim after unicode and punctuation
normalisation; verbatim with all whitespace removed (pypdf splits words at kerning
boundaries); verbatim with marks and punctuation folded away (Thai tone marks, Arabic harakat,
CJK punctuation); otherwise a character-trigram overlap, `edited` above NEAR and `not found`
below. A `not found` English quote against a non-English source is `translated`: it may be
faithful, and no string check can say.
"""
import re
import unicodedata

VERBATIM, EDITED, TRANSLATED, NOT_FOUND = "verbatim", "edited", "translated", "not found"
NEAR = 0.80
MIN_QUOTE_CHARS = 12          # below this a "quote" is a label, not a passage

_PUNCT = dict.fromkeys(map(ord, "‘’“”\"'`´–,−‐-"), None)
_LETTERFORMS = {0x06CC: "ي", 0x0649: "ي", 0x06A9: "ك", 0x06AA: "ك"}
_TATWEEL = "ـ"
TRIGRAM = 3
FUNCTION_WORDS = frozenset("the of and to in a for is on that with as by are be this it "
                           "from at an".split())
ENGLISH_QUOTE = 0.15          # above this, the quote is English prose
ENGLISH_SOURCE = 0.05         # below this, the paragraph it cites is not


def normalise(s):
    """Comparable text: unicode-normalised, punctuation-insensitive, whitespace-collapsed."""
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = s.translate(_PUNCT)
    return re.sub(r"\s+", " ", s).strip().casefold()


def despace(s):
    return re.sub(r"\s+", "", s)


def overlap(quote_tokens, source_tokens_set):
    if not quote_tokens:
        return 0.0
    return sum(1 for t in quote_tokens if t in source_tokens_set) / len(quote_tokens)


def fold(s):
    """Marks, punctuation, separators and control characters dropped, then casefolded."""
    s = unicodedata.normalize("NFKC", str(s or "")).replace(_TATWEEL, "")
    s = s.translate(_LETTERFORMS)
    kept = [c for c in s if unicodedata.category(c)[0] not in ("M", "P", "Z", "C")]
    return "".join(kept).casefold()


def trigrams(s):
    return [s[i:i + TRIGRAM] for i in range(len(s) - TRIGRAM + 1)]


def english_share(text):
    toks = re.findall(r"[a-z]+", str(text or "").lower())
    return sum(1 for t in toks if t in FUNCTION_WORDS) / len(toks) if toks else 0.0


def match_quote(quote, paragraph):
    """(verdict, tier, overlap) for one quote against one paragraph."""
    nq, npar = normalise(quote), normalise(paragraph)
    if nq and nq in npar:
        return VERBATIM, 1, 1.0
    if nq and despace(nq) in despace(npar):
        return VERBATIM, 2, 1.0
    fq, fpar = fold(quote), fold(paragraph)
    if fq and fq in fpar:
        return VERBATIM, 3, 1.0
    score = overlap(trigrams(fq), set(trigrams(fpar)))
    return (EDITED if score >= NEAR else NOT_FOUND), 4, round(score, 3)


def classify(quote, paragraph, verdict):
    if verdict != NOT_FOUND:
        return verdict
    if english_share(quote) > ENGLISH_QUOTE and english_share(paragraph) < ENGLISH_SOURCE:
        return TRANSLATED
    return verdict


def check(quote, paragraph):
    """The verdict for a quote against the chunk it came from, or "" for no quote."""
    if not str(quote or "").strip():
        return ""
    verdict, _tier, _score = match_quote(quote, paragraph)
    return classify(quote, paragraph, verdict)
