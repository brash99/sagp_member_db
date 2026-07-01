from collections import defaultdict
from .names import clean
from .config import (
    AUTO_MERGE_POSSIBLE_DUPLICATES,
    AUTO_MERGE_POSSIBLE_DUPLICATES_MIN_CONFIDENCE,
)


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def choose_canonical(records):
    """Choose the best source row to represent the current person fields.

    This does not discard the other records; their provenance is aggregated
    into AppearsIn, CodeHistory, InclusionBasisHistory, SourceCount, etc.
    """
    def score(r):
        return (
            10 if clean(r.get("PrimaryEmail")) else 0,
            5 if clean(r.get("Institution")) else 0,
            3 if r.get("SourceFile") != "contacts.csv" else 0,
            2 if clean(r.get("DisplayName")) else 0,
            -int(str(r.get("SourceRow") or 999999)),
        )
    return max(records, key=score)


def _add_group_links(rows, key_field_names, reason, confidence, links, candidate_groups=None):
    """Find groups sharing a key and append merge/review links.

    key_field_names may be a single field or a tuple/list of fields. Empty key
    components suppress grouping. The returned links are intentionally group-
    level; transitive clustering later prevents split master identities.
    """
    if isinstance(key_field_names, str):
        key_field_names = (key_field_names,)

    by_key = defaultdict(list)
    for i, r in enumerate(rows):
        key = tuple(r.get(field) for field in key_field_names)
        if all(key):
            by_key[key].append(i)

    for key, idxs in by_key.items():
        idxs = sorted(set(idxs))
        if len(idxs) > 1:
            group = {"reason": reason, "confidence": confidence, "idxs": idxs, "key": key}
            if candidate_groups is not None:
                candidate_groups.append(group)
            else:
                links.append(group)


def build_identity_links(rows):
    """Return automatic links and possible duplicate links.

    Automatic links are safe enough to merge without human input. Possible links
    are normally sent to DuplicateReview, unless the config flag enables an
    aggressive one-command merge pass.
    """
    auto_links = []
    possible_links = []

    # Strong automatic evidence.
    _add_group_links(rows, "EmailKey", "exact_email", 100, auto_links)
    _add_group_links(rows, ("NameKey", "InstitutionKey"), "exact_name_institution", 96, auto_links)

    # Weaker evidence: same normalized name, possibly different institutions or emails.
    _add_group_links(rows, "NameKey", "exact_name_only", 82, auto_links, candidate_groups=possible_links)

    return auto_links, possible_links


def _unique_join(records, field):
    return "; ".join(sorted({clean(r.get(field, "")) for r in records if clean(r.get(field, ""))}))


def _record_confidence(records, merge_reason=None, merge_confidence=None):
    """Estimate confidence that a master row belongs in the SAGP database.

    This is intentionally separate from merge confidence.  A singleton from a
    SAGP source file can be high-confidence even though no merge occurred.
    """
    source_files = {clean(r.get("SourceFile")) for r in records if clean(r.get("SourceFile"))}
    bases = " ".join(clean(r.get("InclusionBasis")) for r in records).lower()
    has_non_contacts = any(src and src != "contacts.csv" for src in source_files)
    has_contacts = "contacts.csv" in source_files

    if len(records) > 1:
        if merge_reason == "exact_email":
            return 100
        if merge_reason == "exact_name_institution":
            return 97 if len(source_files) > 1 else 96
        if merge_reason == "exact_name_only_auto":
            return max(88, int(merge_confidence or 82))
        if "multiple_reasons" in str(merge_reason):
            return max(90, int(merge_confidence or 90))
        return max(90, int(merge_confidence or 90))

    if has_non_contacts:
        return 95
    if "mentions sagp" in bases:
        return 85
    if "matches sagp source" in bases:
        return 90
    if has_contacts:
        return 75
    return 70


def _review_status(source_count, merge_reason, record_confidence):
    if source_count == 1:
        return "AUTO_SINGLE"
    if merge_reason in {"exact_email", "exact_name_institution"}:
        return "AUTO_MERGED"
    if merge_reason == "exact_name_only_auto":
        return "AUTO_MERGED_POSSIBLE_DUPLICATE"
    if "multiple_reasons" in str(merge_reason):
        return "AUTO_MERGED"
    if record_confidence < 85:
        return "REVIEW_LOW_CONFIDENCE"
    return "AUTO"


def _apply_master_metadata(canonical, records, *, merge_reason, merge_confidence):
    source_count = len(records)
    source_files = {clean(r.get("SourceFile")) for r in records if clean(r.get("SourceFile"))}
    canonical["SourceCount"] = source_count
    canonical["UniqueSourceCount"] = len(source_files)
    canonical["MergedRecordCount"] = source_count  # retained for backward compatibility
    canonical["MergeConfidence"] = "" if source_count == 1 else merge_confidence
    canonical["MergeReason"] = merge_reason if source_count > 1 else "single_record"
    canonical["AppearsIn"] = _unique_join(records, "SourceFile")
    canonical["CodeHistory"] = _unique_join(records, "OriginalMembershipCode")
    canonical["InclusionBasisHistory"] = _unique_join(records, "InclusionBasis")
    canonical["RecordConfidence"] = _record_confidence(records, merge_reason, merge_confidence)
    canonical["ReviewStatus"] = _review_status(source_count, merge_reason, canonical["RecordConfidence"])
    return canonical


def _cluster_reason_and_confidence(cluster_idxs, merge_links):
    reasons = []
    confidences = []
    cset = set(cluster_idxs)
    for link in merge_links:
        if len(cset.intersection(link["idxs"])) >= 2:
            reasons.append(link["reason"])
            confidences.append(link["confidence"])

    if not reasons:
        return "single_record", ""

    unique_reasons = sorted(set(reasons))
    confidence = max(confidences) if confidences else ""
    if len(unique_reasons) == 1:
        reason = unique_reasons[0]
        if reason == "exact_name_only":
            reason = "exact_name_only_auto"
        return reason, confidence
    return "multiple_reasons: " + "; ".join(unique_reasons), confidence


def _build_clusters(rows, merge_links):
    uf = UnionFind(len(rows))
    for link in merge_links:
        idxs = link["idxs"]
        first = idxs[0]
        for idx in idxs[1:]:
            uf.union(first, idx)

    clusters = defaultdict(list)
    for i in range(len(rows)):
        clusters[uf.find(i)].append(i)
    return list(clusters.values())


def build_master(rows):
    auto_links, possible_links = build_identity_links(rows)

    merge_links = list(auto_links)
    auto_merge_possible = bool(AUTO_MERGE_POSSIBLE_DUPLICATES)
    if auto_merge_possible:
        for link in possible_links:
            if int(link["confidence"]) >= int(AUTO_MERGE_POSSIBLE_DUPLICATES_MIN_CONFIDENCE):
                merge_links.append(link)

    clusters = _build_clusters(rows, merge_links)

    assigned = {}
    master = []
    merge_log = []

    # Stable ordering by the earliest source row represented in each cluster.
    clusters = sorted(clusters, key=lambda idxs: min(rows[i].get("RawRecordID", "") for i in idxs))

    for idxs in clusters:
        pid = f"SAGP{len(master)+1:06d}"
        recs = [rows[i] for i in idxs]
        reason, confidence = _cluster_reason_and_confidence(idxs, merge_links)
        canonical = dict(choose_canonical(recs))
        canonical["PersonID"] = pid
        _apply_master_metadata(canonical, recs, merge_reason=reason, merge_confidence=confidence)
        master.append(canonical)
        for r in recs:
            assigned[r["RawRecordID"]] = pid
            if len(recs) > 1:
                merge_log.append({
                    "PersonID": pid,
                    "RawRecordID": r["RawRecordID"],
                    "Reason": reason,
                    "Confidence": confidence,
                    "SourceFile": r.get("SourceFile"),
                    "SourceRow": r.get("SourceRow"),
                })

    # Map PersonID to master row so review status can be updated after possible
    # duplicate groups are generated.
    master_by_pid = {r["PersonID"]: r for r in master}

    duplicate_review = []
    seen = set()
    review_group = 1
    for link in possible_links:
        if auto_merge_possible and int(link["confidence"]) >= int(AUTO_MERGE_POSSIBLE_DUPLICATES_MIN_CONFIDENCE):
            continue

        pids = sorted({assigned.get(rows[i]["RawRecordID"]) for i in link["idxs"] if assigned.get(rows[i]["RawRecordID"])})
        if len(pids) <= 1:
            continue

        key = tuple(pids)
        if key in seen:
            continue
        seen.add(key)

        for pid in pids:
            if pid in master_by_pid and master_by_pid[pid].get("ReviewStatus") != "AUTO_MERGED":
                master_by_pid[pid]["ReviewStatus"] = "REVIEW_POSSIBLE_DUPLICATE"

        # Keep the existing row-wise sheet shape for compatibility, but it is
        # now generated from unresolved master clusters rather than pre-cluster
        # raw records. CurrentPersonID makes it clear which master rows are in play.
        for i in link["idxs"]:
            r = dict(rows[i])
            r["ReviewGroup"] = f"REVIEW{review_group:04d}"
            r["SuggestedReason"] = link["reason"]
            r["SuggestedConfidence"] = link["confidence"]
            r["CurrentPersonID"] = assigned.get(r["RawRecordID"], "")
            duplicate_review.append(r)
        review_group += 1

    return master, duplicate_review, merge_log
