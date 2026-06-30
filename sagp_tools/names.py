import re

CODE_RE = re.compile(r"^\s*([0-9]{1,2}[A-Za-z]?)\s*$")
PREFIXES = {"dr", "prof", "prof.", "mr", "mrs", "ms"}
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}


def clean(value):
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def is_code(value):
    return bool(CODE_RE.match(clean(value)))


def extract_code(first, middle, last, notes=""):
    """Preserve the magic SAGP code without interpreting it."""
    for value in (last, middle, first):
        v = clean(value)
        if is_code(v):
            return v
    # Very conservative: do not mine notes yet.
    return ""


def parse_name(first, middle, last):
    """Handle the main observed malformed-name patterns.

    The most common SAGP pattern is Last | First | Code. Other rows may be
    First Last | |, or First | | Last.
    """
    f, m, l = clean(first), clean(middle), clean(last)
    code = extract_code(f, m, l)
    f_is_code, m_is_code, l_is_code = is_code(f), is_code(m), is_code(l)

    # Pattern: Last | First | code, or Last | First | blank
    if f and m and (l_is_code or not l):
        return {"FirstName": m, "MiddleName": "", "LastName": f, "OriginalMembershipCode": code}

    # Pattern: First | blank | Last
    if f and not m and l and not l_is_code:
        return {"FirstName": f, "MiddleName": "", "LastName": l, "OriginalMembershipCode": code}

    # Pattern: Full Name in first column only.
    if f and not m and (not l or l_is_code):
        parts = f.split()
        if len(parts) >= 2:
            suffix = ""
            if parts[-1].lower() in SUFFIXES:
                suffix = parts.pop()
            return {
                "FirstName": parts[0],
                "MiddleName": " ".join(parts[1:-1]),
                "LastName": parts[-1],
                "Suffix": suffix,
                "OriginalMembershipCode": code,
            }

    # Fallback: assume Google semantics.
    return {"FirstName": f if not f_is_code else "", "MiddleName": m if not m_is_code else "", "LastName": l if not l_is_code else "", "OriginalMembershipCode": code}


def display_name(first, middle, last, suffix=""):
    return clean(" ".join(x for x in [first, middle, last, suffix] if clean(x)))


def name_key(first, last):
    return re.sub(r"[^a-z0-9]", "", f"{clean(last).lower()}|{clean(first).lower()}")
