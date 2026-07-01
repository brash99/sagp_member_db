from .names import clean, parse_name, display_name, name_key
from .membership_codes import interpret_membership_codes


def first_nonblank(row, *fields):
    for field in fields:
        v = clean(row.get(field, ""))
        if v:
            return v
    return ""


def normalize_row(row, raw_index):
    parsed = parse_name(
        row.get("First Name"),
        row.get("Middle Name"),
        row.get("Last Name"),
        source_file=row.get("SourceFile", ""),
    )
    suffix = clean(parsed.get("Suffix") or row.get("Name Suffix"))
    first = clean(parsed.get("FirstName"))
    middle = clean(parsed.get("MiddleName"))
    last = clean(parsed.get("LastName"))
    email = first_nonblank(row, "E-mail 1 - Value", "E-mail 2 - Value", "E-mail 3 - Value")
    institution = first_nonblank(row, "Organization Name")
    phone = first_nonblank(row, "Phone 1 - Value", "Phone 2 - Value")
    membership_status, last_paid_year = interpret_membership_codes([parsed.get("OriginalMembershipCode", "")])

    return {
        "RawRecordID": f"RAW{raw_index:06d}",
        "SourceFile": row.get("SourceFile", ""),
        "SourceRow": row.get("SourceRow", ""),
        "SourceRegion": row.get("SourceRegion", ""),
        "OriginalFirstName": clean(row.get("First Name")),
        "OriginalMiddleName": clean(row.get("Middle Name")),
        "OriginalLastName": clean(row.get("Last Name")),
        "FirstName": first,
        "MiddleName": middle,
        "LastName": last,
        "Suffix": suffix,
        "DisplayName": display_name(first, middle, last, suffix),
        "OriginalMembershipCode": parsed.get("OriginalMembershipCode", ""),
        "MembershipStatus": membership_status,
        "LastPaidYear": last_paid_year or "",
        "Institution": institution,
        "Title": first_nonblank(row, "Organization Title"),
        "PrimaryEmail": email,
        "Phone": phone,
        "Address": first_nonblank(row, "Address 1 - Formatted"),
        "City": first_nonblank(row, "Address 1 - City"),
        "StateProvince": first_nonblank(row, "Address 1 - Region"),
        "PostalCode": first_nonblank(row, "Address 1 - Postal Code"),
        "Country": first_nonblank(row, "Address 1 - Country"),
        "Notes": clean(row.get("Notes")),
        "NameKey": name_key(first, last),
        "EmailKey": clean(email).lower(),
        "InstitutionKey": clean(institution).lower(),
        "NeedsReview": clean(parsed.get("NeedsReview")),
    }


def normalize_all(raw_rows):
    return [normalize_row(row, i) for i, row in enumerate(raw_rows, start=1)]
