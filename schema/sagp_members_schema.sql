PRAGMA foreign_keys = ON;
CREATE TABLE members (

    person_id TEXT PRIMARY KEY,

    display_name TEXT NOT NULL,

    title TEXT,

    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    suffix TEXT,

    institution TEXT,

    primary_email TEXT,
    secondary_email TEXT,

    phone TEXT,

    address1 TEXT,
    address2 TEXT,

    city TEXT,
    state_province TEXT,
    postal_code TEXT,
    country TEXT,

    region TEXT,

    membership_status TEXT,

    original_membership_code TEXT,

    member_since TEXT,

    last_paid_year INTEGER,

    active INTEGER NOT NULL DEFAULT 1,

    notes TEXT,

    created_at TEXT NOT NULL,

    updated_at TEXT NOT NULL

);

CREATE TABLE IF NOT EXISTS source_appearances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    source_file TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES members(person_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS membership_code_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    code TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES members(person_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imported_at TEXT NOT NULL,
    input_workbook TEXT NOT NULL,
    input_sheet TEXT NOT NULL,
    workbook_format_version TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    member_count INTEGER NOT NULL,
    skipped_blank_rows INTEGER NOT NULL,
    warnings TEXT
);

CREATE TABLE IF NOT EXISTS schema_info (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_members_name ON members(last_name, first_name, display_name);
CREATE INDEX IF NOT EXISTS idx_members_email ON members(primary_email);
CREATE INDEX IF NOT EXISTS idx_members_institution ON members(institution);
CREATE INDEX IF NOT EXISTS idx_source_appearances_person ON source_appearances(person_id);
CREATE INDEX IF NOT EXISTS idx_code_history_person ON membership_code_history(person_id);
