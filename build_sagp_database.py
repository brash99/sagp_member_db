#!/usr/bin/env python3
from pathlib import Path
from sagp_tools.importer import import_raw
from sagp_tools.normalize import normalize_all
from sagp_tools.filtering import filter_contacts_scope
from sagp_tools.deduplicate import build_master
from sagp_tools.reports import source_summary, code_summary, data_quality_text
from sagp_tools.io import write_csv
from sagp_tools.excel_export import write_workbook

RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")

NORMALIZED_FIELDS = [
    "RawRecordID", "SourceFile", "SourceRow", "SourceRegion",
    "OriginalFirstName", "OriginalMiddleName", "OriginalLastName",
    "FirstName", "MiddleName", "LastName", "Suffix", "DisplayName",
    "OriginalMembershipCode", "Institution", "Title", "PrimaryEmail", "Phone",
    "Address", "City", "StateProvince", "PostalCode", "Country", "Notes",
    "NameKey", "EmailKey", "InstitutionKey", "InclusionBasis", "NeedsReview"
]
MASTER_FIELDS = ["PersonID"] + NORMALIZED_FIELDS + [
    "SourceCount", "UniqueSourceCount", "RecordConfidence", "ReviewStatus",
    "MergedRecordCount", "MergeConfidence", "MergeReason",
    "AppearsIn", "CodeHistory", "InclusionBasisHistory",
]
PUBLIC_MASTER_FIELDS = [
    "PersonID", "DisplayName", "FirstName", "MiddleName", "LastName", "Suffix",
    "Institution", "Title", "PrimaryEmail", "Phone",
    "City", "StateProvince", "PostalCode", "Country",
    "OriginalMembershipCode", "CodeHistory", "AppearsIn",
]

REVIEW_FIELDS = ["ReviewGroup", "SuggestedReason", "SuggestedConfidence", "CurrentPersonID"] + NORMALIZED_FIELDS
MERGE_FIELDS = ["PersonID", "RawRecordID", "Reason", "Confidence", "SourceFile", "SourceRow"]
EXCLUDED_CONTACT_FIELDS = ["RawRecordID", "SourceFile", "SourceRow", "DisplayName", "PrimaryEmail", "Institution", "ExclusionReason"]


def has_member_identity(row):
    return any(
        str(row.get(field, "")).strip()
        for field in ("FirstName", "LastName", "OriginalMembershipCode")
    )


def drop_blank_member_identity_rows(raw_rows, normalized_rows):
    kept_raw = []
    kept_normalized = []
    skipped = []

    for raw, norm in zip(raw_rows, normalized_rows):
        if has_member_identity(norm):
            kept_raw.append(raw)
            kept_normalized.append(norm)
        else:
            skipped.append(norm)

    return kept_raw, kept_normalized, skipped


def main():
    raw_rows_all, raw_fields = import_raw(RAW_DIR)
    normalized_all = normalize_all(raw_rows_all)
    raw_rows, normalized, excluded_contacts = filter_contacts_scope(raw_rows_all, normalized_all)
    raw_rows, normalized, skipped_blank_members = drop_blank_member_identity_rows(
        raw_rows, normalized
    )
    master, duplicate_review, merge_log = build_master(normalized)
    OUTPUT_DIR.mkdir(exist_ok=True)

    write_csv(OUTPUT_DIR / "raw_normalized.csv", normalized, NORMALIZED_FIELDS)
    write_csv(OUTPUT_DIR / "master_persons.csv", master, MASTER_FIELDS)
    write_csv(OUTPUT_DIR / "duplicate_review.csv", duplicate_review, REVIEW_FIELDS)
    write_csv(OUTPUT_DIR / "merge_log.csv", merge_log, MERGE_FIELDS)
    write_csv(OUTPUT_DIR / "excluded_contacts.csv", excluded_contacts, EXCLUDED_CONTACT_FIELDS)
    source_rows = source_summary(raw_rows, normalized)
    code_rows = code_summary(normalized)
    report_text = data_quality_text(raw_rows, normalized, master, duplicate_review, excluded_contacts)

    write_csv(OUTPUT_DIR / "source_summary.csv", source_rows, ["SourceFile", "SourceRegion", "ImportedRows"])
    write_csv(OUTPUT_DIR / "code_summary.csv", code_rows, ["OriginalMembershipCode", "RowCount"])
    (OUTPUT_DIR / "DataQualityReport.txt").write_text(report_text, encoding="utf-8")

    workbook_path = write_workbook(
        OUTPUT_DIR / "SAGP_Reconciliation.xlsx",
        master_rows=master,
        public_master_rows=master,
        normalized_rows=normalized,
        duplicate_review_rows=duplicate_review,
        merge_log_rows=merge_log,
        source_summary_rows=source_rows,
        code_summary_rows=code_rows,
        report_text=report_text,
        master_fields=MASTER_FIELDS,
        public_master_fields=PUBLIC_MASTER_FIELDS,
        normalized_fields=NORMALIZED_FIELDS,
        review_fields=REVIEW_FIELDS,
        merge_fields=MERGE_FIELDS,
        excluded_contact_rows=excluded_contacts,
        excluded_contact_fields=EXCLUDED_CONTACT_FIELDS,
    )

    print(f"Imported {len(raw_rows_all)} raw rows before contacts.csv SAGP-scope filter")
    print(f"Kept {len(raw_rows)} SAGP-scope rows")
    print(f"Excluded {len(excluded_contacts)} contacts.csv rows outside SAGP scope")
    print(
        f"Skipped {len(skipped_blank_members)} rows with no first name, "
        f"last name, or membership code"
    )
    print(f"Created {len(master)} master person rows")
    print(f"Flagged {len(duplicate_review)} rows for duplicate review")
    print(f"Wrote outputs to {OUTPUT_DIR}")
    print(f"Wrote workbook to {workbook_path}")


if __name__ == "__main__":
    main()
