#!/usr/bin/env python3
"""Small inspection utility for the SAGP SQLite database."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def print_summary(conn: sqlite3.Connection) -> None:
    print("SAGP database summary")
    for table in ["members", "source_appearances", "membership_code_history", "import_log"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count}")
    print("\nTop source files:")
    for row in conn.execute(
        """
        SELECT source_file, COUNT(*) AS n
        FROM source_appearances
        GROUP BY source_file
        ORDER BY n DESC, source_file
        LIMIT 15
        """
    ):
        print(f"  {row['source_file']}: {row['n']}")
    print("\nSample members:")
    for row in conn.execute(
        """
        SELECT person_id, display_name, institution, primary_email
        FROM members
        ORDER BY last_name, first_name, display_name
        LIMIT 10
        """
    ):
        print(f"  {row['person_id']}: {row['display_name']} | {row['institution'] or ''} | {row['primary_email'] or ''}")


def search(conn: sqlite3.Connection, term: str) -> None:
    like = f"%{term}%"
    rows = conn.execute(
        """
        SELECT person_id, display_name, institution, primary_email, city, state_province, country
        FROM members
        WHERE display_name LIKE ?
           OR first_name LIKE ?
           OR last_name LIKE ?
           OR institution LIKE ?
           OR primary_email LIKE ?
        ORDER BY last_name, first_name, display_name
        LIMIT 50
        """,
        (like, like, like, like, like),
    ).fetchall()
    if not rows:
        print(f"No matches for {term!r}")
        return
    for row in rows:
        print(f"{row['person_id']}: {row['display_name']}")
        print(f"  Institution: {row['institution'] or ''}")
        print(f"  Email:       {row['primary_email'] or ''}")
        print(f"  Location:    {row['city'] or ''} {row['state_province'] or ''} {row['country'] or ''}".strip())


def export_members(conn: sqlite3.Connection, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        """
        SELECT person_id, display_name, first_name, middle_name, last_name, suffix,
               institution, title, primary_email, phone, city, state_province,
               postal_code, country, original_membership_code, active, notes,
               created_at, updated_at
        FROM members
        ORDER BY last_name, first_name, display_name
        """
    ).fetchall()
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(rows[0].keys() if rows else [
            "person_id", "display_name", "first_name", "middle_name", "last_name", "suffix",
            "institution", "title", "primary_email", "phone", "city", "state_province",
            "postal_code", "country", "original_membership_code", "active", "notes",
            "created_at", "updated_at",
        ])
        for row in rows:
            writer.writerow([row[k] for k in row.keys()])
    print(f"Exported {len(rows)} members to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the SAGP SQLite database.")
    parser.add_argument("database", type=Path)
    parser.add_argument("--search", help="Search members by name, email, or institution")
    parser.add_argument("--export-members", type=Path, help="Export members table to CSV")
    args = parser.parse_args()

    with connect(args.database) as conn:
        if args.search:
            search(conn, args.search)
        elif args.export_members:
            export_members(conn, args.export_members)
        else:
            print_summary(conn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
