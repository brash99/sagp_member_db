from collections import defaultdict
from .names import clean


def choose_canonical(records):
    # Prefer rows with email, institution, and non-master SAGP source over generic contacts export.
    def score(r):
        return (
            10 if clean(r.get("PrimaryEmail")) else 0,
            5 if clean(r.get("Institution")) else 0,
            3 if r.get("SourceFile") != "contacts.csv" else 0,
            -int(str(r.get("SourceRow") or 999999)),
        )
    return max(records, key=score)


def group_records(rows):
    groups = []
    used = set()

    # Exact email match is strongest.
    by_email = defaultdict(list)
    for i, r in enumerate(rows):
        if r.get("EmailKey"):
            by_email[r["EmailKey"]].append(i)
    for key, idxs in by_email.items():
        if len(idxs) > 1:
            group = sorted(set(idxs))
            groups.append(("exact_email", 100, group))
            used.update(group)

    # Exact normalized name + institution.
    by_name_inst = defaultdict(list)
    for i, r in enumerate(rows):
        key = (r.get("NameKey"), r.get("InstitutionKey"))
        if key[0] and key[1] and i not in used:
            by_name_inst[key].append(i)
    for key, idxs in by_name_inst.items():
        if len(idxs) > 1:
            group = sorted(set(idxs))
            groups.append(("exact_name_institution", 96, group))
            used.update(group)

    # Possible duplicates: exact normalized name only.
    possible = []
    by_name = defaultdict(list)
    for i, r in enumerate(rows):
        if r.get("NameKey"):
            by_name[r["NameKey"]].append(i)
    for key, idxs in by_name.items():
        if len(idxs) > 1:
            possible.append(("exact_name_only", 82, sorted(set(idxs))))

    return groups, possible


def build_master(rows):
    auto_groups, possible_groups = group_records(rows)
    assigned = {}
    master = []
    merge_log = []

    for group_num, (reason, confidence, idxs) in enumerate(auto_groups, start=1):
        pid = f"SAGP{len(master)+1:06d}"
        recs = [rows[i] for i in idxs]
        canonical = dict(choose_canonical(recs))
        canonical["PersonID"] = pid
        canonical["MergedRecordCount"] = len(recs)
        canonical["MergeConfidence"] = confidence
        canonical["MergeReason"] = reason
        canonical["AppearsIn"] = "; ".join(sorted({r.get("SourceFile", "") for r in recs}))
        canonical["CodeHistory"] = "; ".join(sorted({r.get("OriginalMembershipCode", "") for r in recs if r.get("OriginalMembershipCode")}))
        master.append(canonical)
        for r in recs:
            assigned[r["RawRecordID"]] = pid
            merge_log.append({"PersonID": pid, "RawRecordID": r["RawRecordID"], "Reason": reason, "Confidence": confidence, "SourceFile": r.get("SourceFile"), "SourceRow": r.get("SourceRow")})

    for r in rows:
        if r["RawRecordID"] not in assigned:
            pid = f"SAGP{len(master)+1:06d}"
            canonical = dict(r)
            canonical["PersonID"] = pid
            canonical["MergedRecordCount"] = 1
            canonical["MergeConfidence"] = 0
            canonical["MergeReason"] = "single_record"
            canonical["AppearsIn"] = r.get("SourceFile", "")
            canonical["CodeHistory"] = r.get("OriginalMembershipCode", "")
            master.append(canonical)
            assigned[r["RawRecordID"]] = pid

    duplicate_review = []
    seen = set()
    review_group = 1
    for reason, confidence, idxs in possible_groups:
        raw_ids = tuple(sorted(rows[i]["RawRecordID"] for i in idxs))
        if raw_ids in seen:
            continue
        seen.add(raw_ids)
        if len({assigned.get(rid) for rid in raw_ids}) == 1:
            continue
        for i in idxs:
            r = dict(rows[i])
            r["ReviewGroup"] = f"REVIEW{review_group:04d}"
            r["SuggestedReason"] = reason
            r["SuggestedConfidence"] = confidence
            r["CurrentPersonID"] = assigned.get(r["RawRecordID"], "")
            duplicate_review.append(r)
        review_group += 1

    return master, duplicate_review, merge_log
