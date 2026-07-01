import re
from .membership_codes import normalize_membership_code

CODE_RE = re.compile(r"^\s*([0-9]{1,2}[A-Za-z]?)\s*$")
TRAILING_CODE_RE = re.compile(r"^(.*?)\s+([0-9]{1,2}[A-Za-z]?)\s*$")
PREFIXES = {"dr", "prof", "prof.", "mr", "mrs", "ms"}
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}
CONTACTS_FILENAME = "contacts.csv"


def clean(value):
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def is_code(value):
    return bool(CODE_RE.match(clean(value)))


def strip_trailing_code(value):
    """Return (text_without_code, code) for values like 'Ruben 1'."""
    v = clean(value)
    if not v:
        return "", ""
    if is_code(v):
        return "", normalize_membership_code(v)
    match = TRAILING_CODE_RE.match(v)
    if match:
        text, code = clean(match.group(1)), clean(match.group(2))
        if text:
            return text, normalize_membership_code(code)
    return v, ""


def split_leading_suffix(value):
    """Handle values such as 'III Thomas' -> ('Thomas', 'III')."""
    parts = clean(value).split()
    if len(parts) >= 2 and parts[0].lower() in SUFFIXES:
        return " ".join(parts[1:]), parts[0]
    return clean(value), ""


def split_trailing_suffix(value):
    """Handle values such as 'Byrne III' -> ('Byrne', 'III')."""
    parts = clean(value).split()
    if len(parts) >= 2 and parts[-1].lower() in SUFFIXES:
        return " ".join(parts[:-1]), parts[-1]
    return clean(value), ""


def extract_code(first, middle, last, notes=""):
    """Preserve the magic SAGP code without interpreting it."""
    for value in (last, middle, first):
        text, code = strip_trailing_code(value)
        if code:
            return code
    # Very conservative: do not mine notes yet.
    return ""


def _source_is_contacts(source_file):
    return clean(source_file) == CONTACTS_FILENAME


def _parse_single_column_name(name, *, source_file="", code=""):
    """Parse names stored entirely in the first name column.

    For contacts.csv, the Google export usually means First Last.  For SAGP
    regional files with a code in the third column, the dominant legacy pattern
    is Last First Code, so parse two-token values as Last First and flag them
    for review because this is still heuristic.
    """
    parts = clean(name).split()
    if len(parts) < 2:
        return {"FirstName": clean(name), "MiddleName": "", "LastName": "", "Suffix": "", "OriginalMembershipCode": code}

    suffix = ""
    # Pattern: Last Suffix First, e.g. Byrne III Thomas.
    if len(parts) >= 3 and parts[1].lower() in SUFFIXES:
        return {
            "FirstName": " ".join(parts[2:]),
            "MiddleName": "",
            "LastName": parts[0],
            "Suffix": parts[1],
            "OriginalMembershipCode": code,
            "NeedsReview": "single-column last-first heuristic",
        }

    if parts[-1].lower() in SUFFIXES:
        suffix = parts.pop()

    if code and not _source_is_contacts(source_file):
        return {
            "FirstName": " ".join(parts[1:]),
            "MiddleName": "",
            "LastName": parts[0],
            "Suffix": suffix,
            "OriginalMembershipCode": code,
            "NeedsReview": "single-column last-first heuristic",
        }

    return {
        "FirstName": parts[0],
        "MiddleName": " ".join(parts[1:-1]),
        "LastName": parts[-1],
        "Suffix": suffix,
        "OriginalMembershipCode": code,
    }


def parse_name(first, middle, last, source_file=""):
    """Handle the main observed malformed-name patterns.

    The common SAGP regional-file pattern is Last | First | Code. Other rows
    may be First Last | | Code, Last First | | Code, First | | Last, or Google
    Contacts-style First | Middle | Last.
    """
    f_raw, m_raw, l_raw = clean(first), clean(middle), clean(last)

    # Pull codes out of either a pure code cell or a trailing code accidentally
    # appended to a name cell, e.g. 'Ruben 1'.
    f, f_code = strip_trailing_code(f_raw)
    m, m_code = strip_trailing_code(m_raw)
    l, l_code = strip_trailing_code(l_raw)
    code = l_code or m_code or f_code

    f_is_code, m_is_code, l_is_code = is_code(f_raw), is_code(m_raw), is_code(l_raw)

    # Pattern: Last | First | code, or Last | First | blank.
    if f and m and (l_is_code or not l_raw):
        last_name, suffix_from_last = split_trailing_suffix(f)
        first_name, suffix_from_first = split_leading_suffix(m)
        suffix = suffix_from_last or suffix_from_first
        return {
            "FirstName": first_name,
            "MiddleName": "",
            "LastName": last_name,
            "Suffix": suffix,
            "OriginalMembershipCode": code,
        }

    # Pattern: First | blank | Last.
    if f and not m and l and not l_code:
        return {"FirstName": f, "MiddleName": "", "LastName": l, "Suffix": "", "OriginalMembershipCode": code}

    # Pattern: full name in first column only, often with code in third column.
    if f and not m and (not l or l_is_code):
        return _parse_single_column_name(f, source_file=source_file, code=code)

    # Fallback: assume Google semantics.
    return {
        "FirstName": f if not f_is_code else "",
        "MiddleName": m if not m_is_code else "",
        "LastName": l if not l_is_code else "",
        "Suffix": "",
        "OriginalMembershipCode": code,
    }


def display_name(first, middle, last, suffix=""):
    return clean(" ".join(x for x in [first, middle, last, suffix] if clean(x)))


def name_key(first, last):
    return re.sub(r"[^a-z0-9]", "", f"{clean(last).lower()}|{clean(first).lower()}")
