#!/usr/bin/env python3
from pathlib import Path
from sagp_tools.importer import import_raw
from sagp_tools.normalize import normalize_all
from sagp_tools.deduplicate import build_master
from sagp_tools.reports import source_summary, code_summary, data_quality_text
from sagp_tools.io import write_csv

RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")

NORMALIZED_FIELDS = [
    "RawRecordID", "SourceFile", "SourceRow", "SourceRegion",
    "OriginalFirstName", "OriginalMiddleName", "OriginalLastName",
    "FirstName", "MiddleName", "LastName", "Suffix", "DisplayName",
    "OriginalMembershipCode", "Institution", "Title", "PrimaryEmail", "Phone",
    "Address", "City", "StateProvince", "PostalCode", "Country", "Notes",
    "NameKey", "EmailKey", "InstitutionKey", "NeedsReview"
]
MASTER_FIELDS = ["PersonID"] + NORMALIZED_FIELDS + ["MergedRecordCount", "MergeConfidence", "MergeReason", "AppearsIn", "CodeHistory"]
REVIEW_FIELDS = ["ReviewGroup", "SuggestedReason", "SuggestedConfidence", "CurrentPersonID"] + NORMALIZED_FIELDS
MERGE_FIELDS = ["PersonID", "RawRecordID", "Reason", "Confidence", "SourceFile", "SourceRow"]


def main():
    raw_rows, raw_fields = import_raw(RAW_DIR)
    normalized = normalize_all(raw_rows)
    master, duplicate_review, merge_log = build_master(normalized)
    OUTPUT_DIR.mkdir(exist_ok=True)

    write_csv(OUTPUT_DIR / "raw_normalized.csv", normalized, NORMALIZED_FIELDS)
    write_csv(OUTPUT_DIR / "master_persons.csv", master, MASTER_FIELDS)
    write_csv(OUTPUT_DIR / "duplicate_review.csv", duplicate_review, REVIEW_FIELDS)
    write_csv(OUTPUT_DIR / "merge_log.csv", merge_log, MERGE_FIELDS)
    write_csv(OUTPUT_DIR / "source_summary.csv", source_summary(raw_rows, normalized), ["SourceFile", "SourceRegion", "ImportedRows"])
    write_csv(OUTPUT_DIR / "code_summary.csv", code_summary(normalized), ["OriginalMembershipCode", "RowCount"])
    (OUTPUT_DIR / "DataQualityReport.txt").write_text(data_quality_text(raw_rows, normalized, master, duplicate_review), encoding="utf-8")

    print(f"Imported {len(raw_rows)} raw rows")
    print(f"Created {len(master)} master person rows")
    print(f"Flagged {len(duplicate_review)} rows for duplicate review")
    print(f"Wrote outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
