from collections import Counter, defaultdict


def source_summary(raw_rows, normalized_rows):
    c = Counter(r.get("SourceFile", "") for r in raw_rows)
    regions = {}
    for r in raw_rows:
        regions[r.get("SourceFile", "")] = r.get("SourceRegion", "")
    return [{"SourceFile": f, "SourceRegion": regions.get(f, ""), "ImportedRows": n} for f, n in sorted(c.items())]


def code_summary(rows):
    c = Counter(r.get("OriginalMembershipCode", "") or "[blank]" for r in rows)
    return [{"OriginalMembershipCode": code, "RowCount": n} for code, n in sorted(c.items(), key=lambda x: (-x[1], x[0]))]


def data_quality_text(raw_rows, normalized_rows, master, dup_review):
    missing_email = sum(1 for r in master if not r.get("PrimaryEmail"))
    missing_inst = sum(1 for r in master if not r.get("Institution"))
    missing_name = sum(1 for r in master if not r.get("DisplayName"))
    return "\n".join([
        "SAGP Reconciliation v0.1 Data Quality Report",
        "============================================",
        f"Raw records imported: {len(raw_rows)}",
        f"Normalized raw records: {len(normalized_rows)}",
        f"Master person rows: {len(master)}",
        f"Possible duplicate review rows: {len(dup_review)}",
        "",
        f"Master rows missing primary email: {missing_email}",
        f"Master rows missing institution: {missing_inst}",
        f"Master rows missing display name: {missing_name}",
        "",
        "Notes:",
        "- Original name fields are preserved separately from interpreted fields.",
        "- Membership codes are preserved as OriginalMembershipCode and are not interpreted.",
        "- Exact email duplicates are merged automatically.",
        "- Exact normalized name + institution duplicates are merged automatically.",
        "- Exact-name-only matches across separate PersonIDs are exported for human review.",
    ])
