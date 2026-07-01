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


def data_quality_text(raw_rows, normalized_rows, master, dup_review, excluded_contacts=None):
    excluded_contacts = excluded_contacts or []
    missing_email = sum(1 for r in master if not r.get("PrimaryEmail"))
    missing_inst = sum(1 for r in master if not r.get("Institution"))
    missing_name = sum(1 for r in master if not r.get("DisplayName"))
    return "\n".join([
        "SAGP Reconciliation v0.5 Data Quality Report",
        "============================================",
        f"SAGP-scope raw records kept: {len(raw_rows)}",
        f"Normalized SAGP-scope records: {len(normalized_rows)}",
        f"contacts.csv rows excluded as non-SAGP: {len(excluded_contacts)}",
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
        "- contacts.csv is treated as a full personal Google Contacts export; rows are kept only if they mention SAGP or match a SAGP-source person by exact email/name.",
        "- Exact email duplicates are merged automatically.",
        "- Exact normalized name + institution duplicates are merged automatically.",
        "- Master is the user-facing SAGP list; MasterAudit contains provenance, confidence, and raw diagnostic fields.",
        "- RecordConfidence estimates whether the row belongs in the SAGP database.",
        "- MergeConfidence is blank for single-record people because no merge was attempted.",
        "- Exact-name-only matches across separate PersonIDs are exported for human review.",
    ])
