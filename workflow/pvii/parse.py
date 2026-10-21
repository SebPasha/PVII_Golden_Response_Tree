"""Documents to paragraphs and markdown: Document Intelligence, the PDF text layer, or docx.

One parse per document, cached by content hash. Paragraphs feed the per-chunk stages and
carry the Ref "<Doc> · p.<N> · §<M>"; the markdown keeps tables intact for stage 5.
"""
import hashlib
import json
import os
import re

from pvii import config

SKIP_ROLES = {"pageHeader", "pageFooter", "pageNumber"}
HEADING_ROLES = {"title", "sectionHeading"}       # carried on the rows beneath as `section`
MIN_CHARS = 25                                     # shorter fragments are page furniture
_PAGE_BREAK = re.compile(r"<!--\s*PageBreak\s*-->", re.IGNORECASE)
_PAGE_COMMENT = re.compile(r"<!--\s*Page(?:Number|Header|Footer|Break)[^>]*-->", re.IGNORECASE)
TEXT_LAYER_MIN_CHARS_PER_PAGE = 100
TEXT_LAYER_MIN_PAGE_FRACTION = 0.80
PAGE_RATE_USD = float(os.environ.get("PVII_DOCINT_PAGE_RATE", "0.01"))
# Pages parsed this process, for the cost record; a cached parse is free.
PAGES_PARSED = {"parsed": 0, "cached": 0, "documents": []}
# Set for --dry-run: an uncached PDF is read from its text layer rather than billed.
DRY_RUN = False
SCRIPT_RANGES = {"thaana": (0x0780, 0x07BF), "arabic": (0x0600, 0x06FF),
                 "latin": (0x0041, 0x024F), "cyrillic": (0x0400, 0x04FF),
                 "devanagari": (0x0900, 0x097F), "thai": (0x0E00, 0x0E7F)}


def doc_name(path):
    """'Thailand 13th Plan 2023-27 THAI.pdf' -> 'Thailand 13th Plan 2023 27 THAI'."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", stem, flags=re.UNICODE)).strip()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class ParsedDoc:
    def __init__(self, path, name, paragraphs, markdown, page_count):
        self.path, self.name = path, name
        self.paragraphs, self.markdown, self.page_count = paragraphs, markdown, page_count

    def __repr__(self):
        return f"<ParsedDoc {self.name!r} pages={self.page_count} paragraphs={len(self.paragraphs)}>"


def _page_count(path):
    try:
        import logging
        from pypdf import PdfReader
        logging.getLogger("pypdf").setLevel(logging.CRITICAL)
        return len(PdfReader(path).pages)
    except Exception:                               # unreadable: analyse whole
        return 0


def _split_pdf(data, pages_per_slice):
    import io
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(io.BytesIO(data))
    out = []
    for start in range(0, len(reader.pages), pages_per_slice):
        writer = PdfWriter()
        for page in reader.pages[start:start + pages_per_slice]:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        out.append(buf.getvalue())
    return out


def _stitch(results):
    """Sliced analyses back into one, page numbers absolute, page-break markers kept."""
    paragraphs, parts, pages, offset = [], [], [], 0
    for r in results:
        for p in (r.paragraphs or []):
            page = p.bounding_regions[0].page_number if p.bounding_regions else 1
            paragraphs.append({"content": p.content or "", "role": p.role, "page": page + offset})
        parts.append(r.content or "")
        pages.extend(r.pages or [])
        offset += len(r.pages or [])
    return {"paragraphs": paragraphs, "markdown": "\n\n<!-- PageBreak -->\n\n".join(parts),
            "page_count": len(pages)}


def _analyze(path, endpoint, key):
    """One prebuilt-layout call per slice of at most 150 pages / 10 MB; the service times out on more."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentContentFormat
    from azure.core.credentials import AzureKeyCredential

    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    with open(path, "rb") as f:
        data = f.read()
    pages_per_slice = int(os.environ.get("PVII_DOCINT_PAGES_PER_SLICE", "150"))
    slice_bytes = int(os.environ.get("PVII_DOCINT_SLICE_BYTES", str(10 * 1024 * 1024)))
    total = _page_count(path)
    if total:
        pages_per_slice = max(1, min(pages_per_slice, slice_bytes // max(1, len(data) // total)))

    def analyse(payload):
        return client.begin_analyze_document(
            "prebuilt-layout", AnalyzeDocumentRequest(bytes_source=payload),
            output_content_format=DocumentContentFormat.MARKDOWN).result()

    def sliced(n):
        return _stitch([analyse(chunk) for chunk in _split_pdf(data, n)])

    if total and total > pages_per_slice:
        try:
            return sliced(pages_per_slice)
        except Exception as e:                      # one retry at half size on a timeout
            if "timeout" not in str(e).lower() or pages_per_slice <= 1:
                raise
            print("  %s: Document Intelligence timed out at %d pages per slice, retrying at %d"
                  % (os.path.basename(path), pages_per_slice, pages_per_slice // 2))
            return sliced(max(1, pages_per_slice // 2))
    return _stitch([analyse(data)])


def _count_pages(raw):
    n = raw.get("pages")
    if isinstance(n, int):
        return n
    md = raw.get("markdown") or ""
    return md.count("<!-- PageBreak -->") + 1 if md else 0


def script_counts(text):
    out = dict.fromkeys(SCRIPT_RANGES, 0)
    for ch in text:
        o = ord(ch)
        for name, (lo, hi) in SCRIPT_RANGES.items():
            if lo <= o <= hi:
                out[name] += 1
                break
    return out


# A page of glyph codes is a page of characters. A PDF whose font encoding does not resolve
# yields thousands of them, and every volume test passes it: India's 2025 General Debate
# statement read as "! " # $ %" over six pages and was answered with an invented speech (W139).
# Legibility is the share of word-like tokens that are common function words. English, French
# and Spanish are carried because statements are delivered in all three, and Malay and
# Indonesian because five Malaysian and Indonesian sector strategies read 0.000 to 0.019
# without them while being perfectly good text. A text written mostly outside the Latin script
# is not judged here, since these words cannot occur in it.
FUNCTION_WORDS = frozenset("""the of and to in a is that for on as with by at from it this be are
was were an or not have has had will would can could should may we our us they their he she his
her its world international national development countries country people government united
nations peace security climate change global economic social human rights year years must all
more other than which who what when where how also been being into over under between
le la les des une un et de du au aux dans pour sur par avec est sont nous notre que qui ne pas
plus comme tout cette ce son ses leur nos monde pays nations unies developpement el los las y en
por con para es son este esta como mas todo nuestro nuestra se su sus paises mundo desarrollo
naciones unidas yang dan di untuk dengan dalam ini itu ke dari pada oleh serta bagi akan adalah
kepada telah tidak atau juga secara sebagai kerajaan pemerintah negara pembangunan""".split())
MIN_LEGIBLE = 0.05          # a real statement scores 0.15 to 0.60; glyph codes score 0.000


def legibility(text):
    """(score, tokens, judged). judged is False where the text is mostly not Latin script."""
    letters = [c for c in text if c.isalpha()]
    latin = sum(1 for c in letters if c.isascii() or 0x00C0 <= ord(c) <= 0x024F)
    if letters and latin / len(letters) < 0.5:
        return None, len(letters), False
    toks = [t.lower() for t in re.findall(r"[^\W\d_]{2,}", text, re.UNICODE)]
    if len(toks) < 50:
        return 0.0, len(toks), True
    return sum(1 for t in toks if t in FUNCTION_WORDS) / len(toks), len(toks), True


def read_docx(path):
    """A .docx as paragraphs (page 1, page_count 0), or None if it is not one."""
    if not path.lower().endswith(".docx"):
        return None
    try:
        import zipfile
        with zipfile.ZipFile(path) as z:
            if "word/document.xml" not in z.namelist():
                return None
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
    except (zipfile.BadZipFile, OSError, KeyError):
        return None
    paras = []
    for block in re.split(r"</w:p>", xml):
        text = re.sub(r"<[^>]+>", "", re.sub(r"<w:(?:tab|br)[^>]*/>", " ", block))
        text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&quot;", '"').replace("&apos;", "'"))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paras.append({"content": text, "page": 1})
    if not paras:
        return None
    return {"paragraphs": paras, "markdown": "\n\n".join(p["content"] for p in paras),
            "page_count": 0}


def read_text_layer(path, min_chars=200):
    """The PDF's own embedded text in Document Intelligence's shape, or None for a scan."""
    if not path.lower().endswith(".pdf"):
        return None
    try:
        import fitz                                 # PyMuPDF
    except ImportError:
        return None
    try:
        fitz.TOOLS.mupdf_display_errors(False)
    except AttributeError:
        pass
    try:
        doc = fitz.open(path)
    except Exception:
        return None
    paragraphs, total = [], 0
    try:
        n_pages = doc.page_count
        for pno in range(n_pages):
            for block in doc[pno].get_text("blocks"):
                text = (block[4] or "").strip()
                if text:
                    total += len(text)
                    paragraphs.append({"content": text, "page": pno + 1, "role": None})
    finally:
        doc.close()
    if total < min_chars:
        return None
    # One break per PAGE, not one per transition, and the leading gap too. A blank or
    # image-only page yields no paragraph, and writing a single break across it made the
    # markdown's page ordinals a count of the pages that had text: mark_pages numbers by
    # break, so maldives budget_2013 started on physical page 5 and was marked [page 1], and
    # budget_2007 was out by 39. Document Intelligence has always emitted one per page.
    md, last = [], 1
    for p in paragraphs:
        md += ["<!-- PageBreak -->"] * max(0, p["page"] - last)
        md.append(p["content"])
        last = p["page"]
    # The document's own page count, not the number of pages that yielded text: the first is
    # what a page number is counted against, the second is what the coverage figure measures.
    return {"paragraphs": paragraphs, "markdown": "\n\n".join(md), "pages": n_pages,
            "page_count": n_pages, "_source": "text_layer"}


def text_layer_coverage(path):
    """(pages with real text, total pages), or (0, 0) when unreadable."""
    raw, total = read_text_layer(path), _page_count(path)
    if not raw or not total:
        return 0, total
    per_page = {}
    for p in raw["paragraphs"]:
        per_page[p["page"]] = per_page.get(p["page"], 0) + len(p["content"])
    return sum(1 for n in per_page.values() if n >= TEXT_LAYER_MIN_CHARS_PER_PAGE), total


def text_layer_is_usable(path, min_fraction=TEXT_LAYER_MIN_PAGE_FRACTION):
    """(usable, reason): can this PDF be read for free without losing pages?"""
    good, total = text_layer_coverage(path)
    if not total:
        return False, "page count unavailable"
    frac = good / float(total)
    why = "text layer reaches %d of %d pages (%.0f%%)" % (good, total, frac * 100)
    return frac >= min_fraction, why


def _warn_if_script_mismatch(path, raw):
    """The OCR read a Thaana budget as Arabic once; the file's own text layer shows it."""
    tl = read_text_layer(path)
    if not tl:
        return

    def top(counts):
        counts = {k: v for k, v in counts.items() if v}
        return max(counts, key=counts.get) if counts else None

    ocr = top(script_counts(" ".join(p.get("content") or "" for p in raw.get("paragraphs", []))))
    emb = top(script_counts(" ".join(p["content"] for p in tl["paragraphs"])))
    if ocr and emb and ocr != emb:
        print("  WARNING: %s: the OCR came back mostly %s but the file's own text layer is "
              "mostly %s. Set \"parser\": \"text_layer\" for this country."
              % (os.path.basename(path), ocr, emb))


def parse_document(path, cache_dir=None, use_cache=True, offline_ok=False,
                   prefer_text_layer=False):
    """One document -> ParsedDoc. Cached by content hash; the text layer needs no network."""
    cache_dir = cache_dir or config.CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)
    cname = f"{'tl' if prefer_text_layer else 'di'}_{file_hash(path)}.json"
    cpath = os.path.join(cache_dir, cname)
    # A parse PV2 already paid for is read from its cache, never written into it.
    if use_cache and not os.path.exists(cpath) and config.PARSE_CACHE_FALLBACK:
        held = os.path.join(config.PARSE_CACHE_FALLBACK, cname)
        if os.path.exists(held):
            import shutil
            shutil.copy2(held, cpath)
    name = doc_name(path)

    docx = read_docx(path)
    if docx is not None:
        return ParsedDoc(path, name, _paragraphs(docx, name), docx["markdown"], 0)

    if DRY_RUN and not (use_cache and os.path.exists(cpath)):
        would = _page_count(path)
        raw = read_text_layer(path) or {"paragraphs": [], "markdown": "", "page_count": would}
        PAGES_PARSED["parsed"] += would
        PAGES_PARSED["documents"].append({"file": os.path.basename(path), "pages": would,
                                          "cached": False, "estimated": True})
        return ParsedDoc(path, name, _paragraphs(raw, name), raw["markdown"], would)

    from_cache = use_cache and os.path.exists(cpath)
    if from_cache:
        with open(cpath, encoding="utf-8") as f:
            raw = json.load(f)
    elif prefer_text_layer:
        raw = read_text_layer(path)
        if raw is None:
            raise ValueError("%s has no usable text layer; leave it to Document Intelligence"
                             % os.path.basename(path))
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False)
    else:
        if offline_ok or config.OFFLINE:
            raise FileNotFoundError(f"no cached parse for {os.path.basename(path)} (offline)")
        cfg = config.docint_config()
        raw = _analyze_with_retry(path, cfg["endpoint"], cfg["key"])
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False)
        _warn_if_script_mismatch(path, raw)

    from pvii.llm import record
    record(cpath)
    pages = _count_pages(raw)
    PAGES_PARSED["cached" if from_cache else "parsed"] += pages
    PAGES_PARSED["documents"].append({"file": os.path.basename(path), "pages": pages,
                                      "cached": bool(from_cache)})
    return ParsedDoc(path, name, _paragraphs(raw, name), raw["markdown"], raw.get("page_count", 0))


def _analyze_with_retry(path, endpoint, key, attempts=5, sleep=None):
    """Document Intelligence, retried on a dropped connection with backoff.

    Three runs on 31 August each died on the first connection error after their parses
    were already paid for (W98): a resolver hiccup or a write timeout is not a verdict on
    the document. Transport errors and 429/5xx responses retry with 2, 4, 8, 16 seconds
    between attempts; a 4xx that is not a rate limit is the document's problem and raises
    at once.
    """
    import time as _time
    sleep = _time.sleep if sleep is None else sleep
    last = None
    for i in range(attempts):
        try:
            return _analyze(path, endpoint, key)
        except Exception as e:                  # noqa: BLE001 - classified below
            name = type(e).__name__
            status = getattr(e, "status_code", None)
            transient = (name in ("ServiceRequestError", "ServiceResponseError",
                                  "ConnectionError", "TimeoutError")
                         or (status is not None and (status == 429 or status >= 500)))
            if not transient or i == attempts - 1:
                raise
            last = e
            wait = 2 ** (i + 1)
            print("    note: Document Intelligence %s on %s, retrying in %ds (%d of %d)"
                  % (name, os.path.basename(path), wait, i + 1, attempts - 1))
            sleep(wait)
    raise last


def _paragraphs(raw, name):
    """Reader output -> the chunk list every stage iterates, each with its Ref."""
    paragraphs, per_page, section = [], {}, ""
    for p in raw["paragraphs"]:
        role, text = p.get("role"), (p.get("content") or "").strip()
        if role in SKIP_ROLES or not text:
            continue
        if role in HEADING_ROLES:
            section = text
            continue
        if len(text) < MIN_CHARS:
            continue
        page = p.get("page", 1)
        per_page[page] = per_page.get(page, 0) + 1
        paragraphs.append({"ref": f"{name} · p.{page} · §{per_page[page]}", "page": page,
                           "index": len(paragraphs) + 1, "role": role, "section": section,
                           "content": text})
    return paragraphs


PAGE_MARK = "[page %d]"


def _marked_pages(markdown):
    """The document's pages, in order, each headed by the marker naming its number.

    The ordinal counts the page breaks the parser wrote, so it is the page's position in the
    parse. Both parsers now write one break per page of the document, including the pages that
    yielded no text, so the ordinal is the physical page: `read_text_layer` used to write a
    break only where a page had text, which put Maldives budget_2007 out by 39 pages.

    A page with no text is dropped rather than sent as a bare marker, and numbering counts it
    all the same. Emptiness is judged on the page with the parser's own comments stripped: a
    Document Intelligence page carrying nothing but `<!-- PageNumber="ii" -->` is text to
    `strip()` and nothing at all to the model, and it reached the model as a marker standing
    over an empty page, which prompt 5 tells the model cannot happen.
    """
    return ["%s\n\n%s" % (PAGE_MARK % n, page.strip())
            for n, page in enumerate(_PAGE_BREAK.split(markdown), 1)
            if _PAGE_COMMENT.sub("", page).strip()]


def mark_pages(markdown):
    """Page numbers in a line the model can read, for a whole document sent in one call.

    `clean_markdown` strips the parser's page comments, so nothing the model saw said which
    page a figure was on and `source_page` could not be asked for. Numbering happens against
    the whole document, before any chunking, so a chunk from the middle of a book carries the
    document's own ordinals instead of restarting at 1.
    """
    return "\n\n".join(_marked_pages(markdown))


def markdown_page_chunks(markdown, max_tokens=60000, with_pages=False):
    """Page-aligned chunks under a token budget, for the whole-document stages.

    `with_pages` heads each page with its `[page N]` marker; without it a chunk is the bytes
    it always was. Off by default because a stage that only quotes the text (4a) checks its
    quotes against the marker-free document, and a marker landing inside a quoted sentence
    would fail that check.
    """
    from pvii.llm import count_tokens
    chunks, current, current_tokens = [], [], 0
    for page in (_marked_pages(markdown) if with_pages else _PAGE_BREAK.split(markdown)):
        t = count_tokens(page)
        if current and current_tokens + t > max_tokens:
            chunks.append("\n\n".join(current))
            current, current_tokens = [], 0
        current.append(page)
        current_tokens += t
    if current:
        chunks.append("\n\n".join(current))
    return [c for c in chunks if c.strip()]


def clean_markdown(markdown):
    """Strip the page-marker comments the model does not need.

    The `[page N]` markers `mark_pages` writes are text, not comments, and survive this on
    purpose: they are the only thing telling the model what to put in `source_page`.
    """
    return re.sub(r"\n{3,}", "\n\n", _PAGE_COMMENT.sub("", markdown)).strip()
