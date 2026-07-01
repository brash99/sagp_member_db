# SAGP App 2: Database Builder

App 2 converts the frozen `Master` sheet from the reconciliation workbook into a canonical SQLite database for long-term membership management.

## Workflow

```text
App 1: raw CSV files -> SAGP_Reconciliation.xlsx
App 2: Master sheet -> sagp_members.db
App 3: GUI membership manager -> edits sagp_members.db
```

The key design principle is that the generated workbook is a migration artifact.  Once App 2 has built `sagp_members.db`, the SQLite database becomes the source of truth for the GUI app.

## Install

```bash
pip install -r requirements-app2.txt
```

## Build the database

From the repository root:

```bash
python build_database_from_master.py \
  --input output/SAGP_Reconciliation.xlsx \
  --output output/sagp_members.db \
  --overwrite
```

This reads the `Master` sheet and creates these tables:

- `members`
- `source_appearances`
- `membership_code_history`
- `schema_info`
- `import_log`

## Inspect the database

```bash
python inspect_database.py output/sagp_members.db
```

Search for a member:

```bash
python inspect_database.py output/sagp_members.db --search "Eric Silverman"
```

Export the canonical member table back to CSV:

```bash
python inspect_database.py output/sagp_members.db --export-members output/members_export.csv
```

## Frozen workbook contract

App 2 currently expects the `Master` sheet to contain these columns:

```text
PersonID
DisplayName
FirstName
MiddleName
LastName
Suffix
Institution
Title
PrimaryEmail
Phone
City
StateProvince
PostalCode
Country
OriginalMembershipCode
CodeHistory
AppearsIn
```

If App 1 changes the `Master` sheet format later, update `REQUIRED_COLUMNS` and `COLUMN_TO_DB` in `sagp_db_tools/build_database_from_master.py`.

## Notes for App 3

The GUI should edit the SQLite database, not the generated workbook.  The first App 3 screen can be built almost entirely from the `members` table, while the provenance/history panels can use `source_appearances` and `membership_code_history`.


## Contract freeze

See `docs/SAGP_CONTRACTS.md` for the frozen App 1 -> App 2 workbook contract and App 2 -> App 3 SQLite contract.
