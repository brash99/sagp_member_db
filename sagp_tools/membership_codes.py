"""Interpret SAGP historical membership-code values.

These codes come from the original regional/contact files.  They are messy
historical data, but they now carry enough meaning to set an initial membership
status automatically.
"""

from __future__ import annotations

import re
from typing import Iterable

CURRENT_MEMBER_MIN_CODE = 25
EXECUTIVE_DONOR_CODE = 40

_CODE_RE = re.compile(r"^\s*(\d{1,2})(?:\s*[Hh])?\s*$")


def normalize_membership_code(value: object) -> str:
    """Return the canonical historical SAGP code.

    Rules from SAGP legacy notes:
    - a trailing H after a two-digit code means "Hard Copy" and is ignored;
    - single-digit numbers are understood as having a leading zero.

    Examples:
        "40H" -> "40"
        "1"   -> "01"
        "7"   -> "07"
        "25"  -> "25"
    """
    text = str(value or "").strip()
    if not text:
        return ""

    match = _CODE_RE.match(text)
    if not match:
        return text

    return f"{int(match.group(1)):02d}"


def code_to_year(code: object) -> int | None:
    """Map a normalized code to a year when it represents dues year data."""
    normalized = normalize_membership_code(code)
    if not normalized or not normalized.isdigit():
        return None

    value = int(normalized)
    if value in {1, EXECUTIVE_DONOR_CODE}:
        return None

    # Legacy note: single digit numbers are interpreted as 200X, and two digit
    # numbers as 20XX.
    return 2000 + value


def interpret_membership_codes(codes: Iterable[object]) -> tuple[str, int | None]:
    """Return (membership_status, last_paid_year) from code history.

    Priority order:
    1. Code 40/40H -> Executive and Donors.
    2. Codes CURRENT_MEMBER_MIN_CODE through EXECUTIVE_DONOR_CODE - 1 -> Current Member.
    3. Code 01 only/primarily -> Unknown A.
    4. Other interpretable year codes -> Past Member.
    5. No code -> Unknown B.
    """
    normalized_codes = [normalize_membership_code(code) for code in codes]
    normalized_codes = [code for code in normalized_codes if code]

    if not normalized_codes:
        return "Unknown B", None

    code_ints = []
    for code in normalized_codes:
        if code.isdigit():
            code_ints.append(int(code))

    if EXECUTIVE_DONOR_CODE in code_ints:
        return "Executive and Donors", None

    years = [year for year in (code_to_year(code) for code in normalized_codes) if year is not None]
    last_paid_year = max(years) if years else None

    if any(CURRENT_MEMBER_MIN_CODE <= code < EXECUTIVE_DONOR_CODE for code in code_ints):
        return "Current Member", last_paid_year

    non_one_codes = [code for code in code_ints if code != 1]
    if not non_one_codes:
        return "Unknown A", None

    if years:
        return "Past Member", last_paid_year

    return "Unknown B", None
