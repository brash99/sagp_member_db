from pathlib import Path
from .config import REGION_FROM_FILE
from .io import read_csv


def infer_region(filename):
    if filename in REGION_FROM_FILE:
        return REGION_FROM_FILE[filename]
    stem = Path(filename).stem
    if stem.startswith("SAGP "):
        return stem.replace("SAGP ", "")
    return stem


def import_raw(raw_dir):
    raw_dir = Path(raw_dir)
    rows = []
    all_fields = []
    seen_fields = set()
    for path in sorted(raw_dir.glob("*.csv")):
        file_rows, fields = read_csv(path)
        for field in fields:
            if field not in seen_fields:
                seen_fields.add(field)
                all_fields.append(field)
        for i, row in enumerate(file_rows, start=2):
            r = dict(row)
            r["SourceFile"] = path.name
            r["SourceRow"] = i
            r["SourceRegion"] = infer_region(path.name)
            rows.append(r)
    return rows, ["SourceFile", "SourceRow", "SourceRegion"] + all_fields
