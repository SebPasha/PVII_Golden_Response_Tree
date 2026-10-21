"""The quote check, lifted from PV2 validate/truth.py and validate/evidence.py.

WHAT THIS ASSERTS
    Verbatim survives curly quotes, kerning spaces and Thai tone marks; a lightly edited quote
    is `edited`; an English rendering of a Thai paragraph is `translated`, not `not found`; an
    invention is `not found`.

WHAT IT IS BLIND TO
    Whether a translation is faithful. No string check can say.
"""
import pytest

from pvii import quotes as Q

PARA = ("The Government will establish a national health insurance fund covering all informal "
        "workers by 2027, financed through a payroll levy.")


@pytest.mark.unit
def test_verbatim_and_its_tiers():
    assert Q.check("establish a national health insurance fund", PARA) == Q.VERBATIM
    assert Q.check("establish a “national” health insurance fund", PARA) == Q.VERBATIM
    assert Q.check("estab lish a national health insur ance fund", PARA) == Q.VERBATIM


@pytest.mark.unit
def test_thai_marks_are_folded():
    para = "รัฐบาลจะพัฒนาระบบประกันสุขภาพถ้วนหน้า"
    assert Q.check("พัฒนาระบบประกันสุขภาพ", para) == Q.VERBATIM
    # the same quote retyped without its tone marks is still the same passage
    assert Q.check("พฒนาระบบประกนสขภาพ", para) in (Q.VERBATIM, Q.EDITED)


@pytest.mark.unit
def test_translation_is_named_not_called_invention():
    para = "รัฐบาลจะพัฒนาระบบประกันสุขภาพถ้วนหน้าให้ครอบคลุมแรงงานนอกระบบ"
    assert Q.check("The government will develop universal health insurance for the "
                   "informal workers", para) == Q.TRANSLATED


@pytest.mark.unit
def test_edited_and_not_found():
    assert Q.check("The Government will establish a national health insurance fund covering "
                   "every informal worker by 2027", PARA) == Q.EDITED
    assert Q.check("A new seaport will be built in the south", PARA) == Q.NOT_FOUND
    assert Q.check("", PARA) == ""
