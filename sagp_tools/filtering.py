"""Filtering rules for deciding which raw contacts belong in SAGP scope.

The original ``contacts.csv`` appears to be the outgoing officer's full Google
Contacts export, not a SAGP-specific export.  Most SAGP-relevant rows in that
file include the string "SAGP" somewhere in the contact record.  This module
keeps all explicitly SAGP source files, then applies a conservative gate to
``contacts.csv``.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

Row = Mapping[str, object]

CONTACTS_FILENAME = "contacts.csv"
SAGP_TOKEN = "sagp"


def _text(value: object) -> str:
    return "" if value is None else str(value)


def raw_row_mentions_sagp(raw_row: Row) -> bool:
    """Return True if any raw field contains the token SAGP."""
    return SAGP_TOKEN in " ".join(_text(v).lower() for v in raw_row.values())


def make_sagp_reference_keys(normalized_rows: Sequence[Row]) -> tuple[set[str], set[str]]:
    """Build email and name keys from non-contacts SAGP-specific source rows."""
    email_keys: set[str] = set()
    name_keys: set[str] = set()
    for row in normalized_rows:
        if row.get("SourceFile") == CONTACTS_FILENAME:
            continue
        email = _text(row.get("EmailKey")).strip().lower()
        name = _text(row.get("NameKey")).strip().lower()
        if email:
            email_keys.add(email)
        if name:
            name_keys.add(name)
    return email_keys, name_keys


def filter_contacts_scope(raw_rows: Sequence[Row], normalized_rows: Sequence[Row]) -> tuple[list[Row], list[Row], list[dict[str, object]]]:
    """Keep only SAGP-scope rows.

    Rules:
    - Always keep rows from SAGP-specific source files.
    - For ``contacts.csv``, keep the row if it contains "SAGP" anywhere.
    - Also keep a ``contacts.csv`` row if it matches a non-contacts SAGP row by
      exact normalized email or exact normalized name. This lets contacts.csv
      enrich known SAGP people even when the notes field does not explicitly
      contain SAGP.

    Returns ``(kept_raw_rows, kept_normalized_rows, excluded_rows)``.  The
    excluded rows are lightweight audit rows suitable for CSV/report output.
    """
    email_keys, name_keys = make_sagp_reference_keys(normalized_rows)
    kept_raw: list[Row] = []
    kept_norm: list[Row] = []
    excluded: list[dict[str, object]] = []

    for raw, norm in zip(raw_rows, normalized_rows):
        source = _text(norm.get("SourceFile") or raw.get("SourceFile"))
        if source != CONTACTS_FILENAME:
            kept_raw.append(raw)
            kept_norm.append(norm)
            continue

        mentions_sagp = raw_row_mentions_sagp(raw)
        email_match = _text(norm.get("EmailKey")).strip().lower() in email_keys if norm.get("EmailKey") else False
        name_match = _text(norm.get("NameKey")).strip().lower() in name_keys if norm.get("NameKey") else False

        if mentions_sagp or email_match or name_match:
            kept_raw.append(raw)
            kept_norm.append(norm)
        else:
            excluded.append({
                "RawRecordID": norm.get("RawRecordID", ""),
                "SourceFile": source,
                "SourceRow": norm.get("SourceRow", ""),
                "DisplayName": norm.get("DisplayName", ""),
                "PrimaryEmail": norm.get("PrimaryEmail", ""),
                "Institution": norm.get("Institution", ""),
                "ExclusionReason": "contacts.csv row did not mention SAGP and did not match a SAGP-source email/name",
            })

    return kept_raw, kept_norm, excluded
