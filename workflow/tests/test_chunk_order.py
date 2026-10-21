"""Lifted from PV2 tests/unit/test_chunk_order.py; step C chunks the same way 4a did.

Chunk the raw markdown, then clean each piece. Never the other way round.

`markdown_page_chunks` splits on the `<!-- PageBreak -->` comments the parser leaves, and
`clean_markdown` strips exactly those comments. Cleaning first therefore leaves one chunk
holding everything, the token budget goes silently unapplied, and the stage sends the whole
corpus to the model.

Stage 5 got this right and named the trap in a comment at its own call. Stage 4a was written
later and fell into it anyway: it sent 380,000 tokens for Thailand, and Bangladesh was
projected at 3.85 million tokens and $14.44 for a single call, which stopped ten countries at
their spend cap before anyone noticed (W114). A comment did not prevent the second occurrence,
so the rule is asserted here, both as behaviour and at every call site.
"""
import os
import re

import pytest

from pvii.parse import clean_markdown, mark_pages, markdown_page_chunks

STAGES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "pvii", "steps.py")


def _pages(n, words=400):
    """A document of `n` pages, each carrying the page marker the parser writes."""
    page = " ".join("word%d" % i for i in range(words))
    return "\n\n<!-- PageBreak -->\n\n".join(page for _ in range(n))


@pytest.mark.unit
def test_cleaning_first_destroys_the_split():
    """The defect itself, so the test fails if the trap ever stops being a trap."""
    raw = _pages(40)
    assert len(markdown_page_chunks(raw, max_tokens=500)) > 1, "the raw text must split"
    assert len(markdown_page_chunks(clean_markdown(raw), max_tokens=500)) == 1, (
        "cleaning removed the page markers, so the chunker found nothing to split on and "
        "returned the whole document as one piece")


@pytest.mark.unit
def test_chunking_first_keeps_the_budget():
    """Pages are grouped up to the budget. A page is never split, so a chunk can exceed the
    budget by at most one page, which is the contract the callers rely on."""
    from pvii.llm import count_tokens
    raw = _pages(40)
    page = count_tokens(_pages(1))
    budget = page * 4
    pieces = [clean_markdown(p) for p in markdown_page_chunks(raw, max_tokens=budget)]
    assert len(pieces) > 1
    assert all(count_tokens(p) <= budget + page for p in pieces), (
        "a piece is more than one page past the budget it was chunked to")
    assert "PageBreak" not in "".join(pieces), "the pieces still carry the marker comments"


@pytest.mark.unit
def test_no_stage_chunks_text_it_has_already_cleaned():
    """The rule at every call site, not only the two that exist today."""
    src = open(STAGES, encoding="utf-8").read()
    bad = [m.group(0) for m in
           re.finditer(r"markdown_page_chunks\(\s*clean_markdown\([^)]*\)", src)]
    assert not bad, ("a stage cleans before it chunks, which silently drops its token "
                     "budget: %s" % bad)
    # The variable form: chunking a name that was assigned from clean_markdown.
    cleaned = set(re.findall(r"^\s*(\w+)\s*=\s*[^\n]*clean_markdown\(", src, re.M))
    chunked = set(re.findall(r"markdown_page_chunks\(\s*(\w+)", src))
    assert not (cleaned & chunked), (
        "these are cleaned and then chunked, so their budget does not apply: %s"
        % sorted(cleaned & chunked))


@pytest.mark.unit
def test_marked_chunks_carry_the_documents_own_page_numbers():
    """A chunk from the middle of a book must not restart its page numbering at 1.

    `source_page` is only worth asking for if the number the model reads is the number the
    page has in the document. Numbering per chunk would look right inside every chunk and be
    wrong in all but the first.
    """
    from pvii.llm import count_tokens
    raw = _pages(40)
    pieces = markdown_page_chunks(raw, max_tokens=count_tokens(_pages(1)) * 4, with_pages=True)
    assert len(pieces) > 1
    seen = [int(n) for p in pieces for n in re.findall(r"\[page (\d+)\]", p)]
    assert seen == list(range(1, 41))


@pytest.mark.unit
def test_page_markers_survive_cleaning_and_the_comments_do_not():
    """Cleaning is what used to remove every trace of the page, so it is what must not."""
    cleaned = clean_markdown(mark_pages(_pages(3)))
    assert cleaned.count("[page 1]") == 1 and "[page 3]" in cleaned
    assert "PageBreak" not in cleaned


@pytest.mark.unit
def test_the_quote_check_text_is_marker_free():
    """Stage 4a builds its haystack with `clean_markdown` and its pieces with the default
    chunker. A marker in a piece and not in the haystack breaks the quote gate, so the
    default has to stay unmarked."""
    raw = _pages(4)
    pieces = [clean_markdown(p) for p in markdown_page_chunks(raw, max_tokens=500)]
    assert "[page" not in "".join(pieces) and "[page" not in clean_markdown(raw)
