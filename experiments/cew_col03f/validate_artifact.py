from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_SOURCE_SHA = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_SOURCE_VERSION = "CEW-N12-SRC-TAV05S-V2143DBCF"
EXPECTED_OCCURRENCE_IDS = tuple(f"COL-OCC-{index:04d}" for index in range(1, 23))
EXPECTED_ORDER = (
    "COL-OCC-0001",
    "COL-OCC-0015",
    *(oid for oid in EXPECTED_OCCURRENCE_IDS if oid not in {"COL-OCC-0001", "COL-OCC-0015"}),
)
ALLOWED_STATES = {
    "CORROBORATED_EXISTING_LABEL_CANDIDATE",
    "NEW_MULTI_CONFIG_LABEL_CANDIDATE",
    "SINGLE_CONFIG_DIRECT_OBSERVATION",
    "AMBIGUOUS_DIRECT_LABELS",
    "NO_DIRECT_LABEL_OBSERVED",
    "CONTRADICTS_EXISTING_DOCUMENTARY_CANDIDATE",
}
CANDIDATE_STATES = {
    "CORROBORATED_EXISTING_LABEL_CANDIDATE",
    "NEW_MULTI_CONFIG_LABEL_CANDIDATE",
}
AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "vertical_chain_assignment_authorized",
    "structural_identity_authorized",
    "canonical_node_assignment_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"COL03F_SEMANTIC_JSON_MISSING:{path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"COL03F_SEMANTIC_JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source_ref(ref: Any) -> None:
    if not isinstance(ref, dict):
        raise ValueError("COL03F_SEMANTIC_SOURCE_REF_INVALID")
    if ref.get("source_version_id") != EXPECTED_SOURCE_VERSION:
        raise ValueError("COL03F_SEMANTIC_SOURCE_VERSION_DRIFT")
    if ref.get("source_sha256") != EXPECTED_SOURCE_SHA:
        raise ValueError("COL03F_SEMANTIC_SOURCE_DIGEST_DRIFT")
    if not ref.get("page_id") or not ref.get("page_transform_id"):
        raise ValueError("COL03F_SEMANTIC_SOURCE_REF_INVALID")
    raster_sha = str(ref.get("raster_sha256") or "")
    if len(raster_sha) != 64:
        raise ValueError("COL03F_SEMANTIC_RASTER_DIGEST_INVALID")
    if int(ref.get("raster_width_px") or 0) <= 0 or int(ref.get("raster_height_px") or 0) <= 0:
        raise ValueError("COL03F_SEMANTIC_RASTER_DIMENSIONS_INVALID")


def _validate_review_file(root: Path, relative_path: Any, expected_sha: Any) -> None:
    path_text = str(relative_path or "")
    digest = str(expected_sha or "")
    if not path_text.startswith("review/") or len(digest) != 64:
        raise ValueError("COL03F_SEMANTIC_REVIEW_PROVENANCE_INVALID")
    path = root / path_text
    if not path.is_file():
        raise ValueError("COL03F_SEMANTIC_REVIEW_FILE_MISSING")
    if _sha256(path) != digest:
        raise ValueError("COL03F_SEMANTIC_REVIEW_HASH_DRIFT")


def _validate_crop_manifest(root: Path, manifest: Any) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("COL03F_SEMANTIC_CROP_MANIFEST_INVALID")
    for region in ("FOOTPRINT", "LOCAL", "CONTEXT"):
        item = manifest.get(region)
        bounds = item.get("bounds_px") if isinstance(item, dict) else None
        if not isinstance(bounds, list) or len(bounds) != 4:
            raise ValueError("COL03F_SEMANTIC_CROP_BOUNDS_INVALID")
        if any(not isinstance(value, int) for value in bounds):
            raise ValueError("COL03F_SEMANTIC_CROP_BOUNDS_INVALID")
        left, top, right, bottom = bounds
        if left < 0 or top < 0 or right <= left or bottom <= top:
            raise ValueError("COL03F_SEMANTIC_CROP_BOUNDS_INVALID")
    _validate_review_file(root, manifest.get("source_only_path"), manifest.get("source_only_sha256"))
    _validate_review_file(root, manifest.get("target_overlay_path"), manifest.get("target_overlay_sha256"))


def _candidate_values_valid(values: Any) -> bool:
    if not isinstance(values, list):
        return False
    return all(str(value).isdigit() and 1 <= int(str(value)) <= 999 for value in values)


def validate_col03f_artifact(root: Path) -> dict[str, Any]:
    root = Path(root)
    ledger = _load_json(root / "primary-bridge-evidence-ledger.json")
    queue = _load_json(root / "primary-bridge-inspection-queue.json")
    closure = _load_json(root / "primary-bridge-closure.json")

    for payload in (ledger, queue, closure):
        if payload.get("occurrence_count") != 22:
            raise ValueError("COL03F_SEMANTIC_OCCURRENCE_COUNT_DRIFT")

    order = ledger.get("inspection_order")
    if order != list(EXPECTED_ORDER):
        raise ValueError("COL03F_SEMANTIC_INSPECTION_ORDER_DRIFT")
    if queue.get("inspection_order") != order:
        raise ValueError("COL03F_SEMANTIC_QUEUE_ORDER_DRIFT")
    if queue.get("priority_occurrence_ids") != ["COL-OCC-0001", "COL-OCC-0015"]:
        raise ValueError("COL03F_SEMANTIC_PRIORITY_DRIFT")

    _validate_source_ref(ledger.get("source_ref"))
    rows = ledger.get("occurrences")
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError("COL03F_SEMANTIC_OCCURRENCE_COUNT_DRIFT")
    rows_by_id: dict[str, dict[str, Any]] = {}
    for expected_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError("COL03F_SEMANTIC_OCCURRENCE_ROW_INVALID")
        occurrence_id = str(row.get("occurrence_id") or "")
        if occurrence_id in rows_by_id:
            raise ValueError("COL03F_SEMANTIC_OCCURRENCE_SET_DRIFT")
        rows_by_id[occurrence_id] = row
        if row.get("queue_index") != expected_index or occurrence_id != order[expected_index - 1]:
            raise ValueError("COL03F_SEMANTIC_QUEUE_INDEX_DRIFT")
        _validate_source_ref(row.get("source_ref"))
        if row.get("source_ref") != ledger.get("source_ref"):
            raise ValueError("COL03F_SEMANTIC_SOURCE_REF_DRIFT")
        state = row.get("acquisition_state")
        if state not in ALLOWED_STATES:
            raise ValueError("COL03F_SEMANTIC_STATE_INVALID")
        candidate_values = row.get("candidate_values")
        if not _candidate_values_valid(candidate_values):
            raise ValueError("COL03F_SEMANTIC_CANDIDATE_VALUE_INVALID")
        if state in CANDIDATE_STATES:
            if len(candidate_values) != 1:
                raise ValueError("COL03F_SEMANTIC_CANDIDATE_STATE_DRIFT")
        elif candidate_values:
            raise ValueError("COL03F_SEMANTIC_CANDIDATE_STATE_DRIFT")
        if row.get("identity_promoted") is not False:
            raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")
        if row.get("historical_identity_positive_evidence_used") is not False:
            raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")
        if any(row.get(key) is not False for key in AUTHORITY_KEYS):
            raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")
        _validate_crop_manifest(root, row.get("crop_manifest"))

    if set(rows_by_id) != set(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03F_SEMANTIC_OCCURRENCE_SET_DRIFT")

    candidate_ids = [row["occurrence_id"] for row in rows if row.get("acquisition_state") in CANDIDATE_STATES]
    if ledger.get("candidate_occurrence_ids") != candidate_ids:
        raise ValueError("COL03F_SEMANTIC_CANDIDATE_SET_DRIFT")
    if ledger.get("identity_promotion_authorized") is not False:
        raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")

    entries = queue.get("entries")
    if not isinstance(entries, list) or len(entries) != 22:
        raise ValueError("COL03F_SEMANTIC_QUEUE_ENTRY_DRIFT")
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or entry.get("queue_index") != index or entry.get("occurrence_id") != order[index - 1]:
            raise ValueError("COL03F_SEMANTIC_QUEUE_ENTRY_DRIFT")
        if entry.get("identity_promoted") is not False:
            raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")
        row_manifest = rows_by_id[entry["occurrence_id"]]["crop_manifest"]
        for key in ("source_only_path", "source_only_sha256", "target_overlay_path", "target_overlay_sha256"):
            if entry.get(key) != row_manifest.get(key):
                raise ValueError("COL03F_SEMANTIC_QUEUE_REVIEW_DRIFT")
    if queue.get("all_authority_closed") is not True or queue.get("any_identity_resolved") is not False:
        raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")

    atlas_path = queue.get("atlas_path")
    atlas_sha = queue.get("atlas_sha256")
    _validate_review_file(root, atlas_path, atlas_sha)
    if closure.get("atlas_path") != atlas_path or closure.get("atlas_sha256") != atlas_sha:
        raise ValueError("COL03F_SEMANTIC_ATLAS_DRIFT")

    actual_counts = dict(sorted(Counter(str(row["acquisition_state"]) for row in rows).items()))
    if closure.get("state_counts") != actual_counts or sum(actual_counts.values()) != 22:
        raise ValueError("COL03F_SEMANTIC_STATE_COUNT_DRIFT")
    if closure.get("candidate_occurrence_ids") != candidate_ids:
        raise ValueError("COL03F_SEMANTIC_CANDIDATE_SET_DRIFT")
    unresolved_ids = [row["occurrence_id"] for row in rows if row.get("acquisition_state") not in CANDIDATE_STATES]
    if closure.get("unresolved_occurrence_ids") != unresolved_ids:
        raise ValueError("COL03F_SEMANTIC_UNRESOLVED_SET_DRIFT")

    probes = closure.get("candidate_probe_results")
    if not isinstance(probes, dict) or set(probes) != {"COL-OCC-0001", "COL-OCC-0015"}:
        raise ValueError("COL03F_SEMANTIC_PROBE_SET_DRIFT")
    for occurrence_id in ("COL-OCC-0001", "COL-OCC-0015"):
        probe = probes[occurrence_id]
        row = rows_by_id[occurrence_id]
        if not isinstance(probe, dict):
            raise ValueError("COL03F_SEMANTIC_PROBE_DRIFT")
        for key in ("acquisition_state", "candidate_values", "direct_observed_values", "documentary_candidate_values"):
            if probe.get(key) != row.get(key):
                raise ValueError("COL03F_SEMANTIC_PROBE_DRIFT")

    if closure.get("primary_source_replayable") is not True:
        raise ValueError("COL03F_SEMANTIC_REPLAYABILITY_DRIFT")
    if closure.get("historical_identity_positive_evidence_used") is not False:
        raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")
    if closure.get("any_identity_resolved") is not False or closure.get("all_authority_closed") is not True:
        raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")
    if closure.get("identity_promotion_authorized") is not False:
        raise ValueError("COL03F_SEMANTIC_AUTHORITY_DRIFT")

    expected_next = (
        "HUMAN_ADJUDICATE_PRIMARY_LABEL_BRIDGE_CANDIDATES"
        if candidate_ids
        else "ACQUIRE_EXTERNAL_OR_MANUAL_PRIMARY_IDENTITY_EVIDENCE"
    )
    if closure.get("next_required_action") != expected_next:
        raise ValueError("COL03F_SEMANTIC_NEXT_ACTION_DRIFT")

    return {
        "occurrence_count": 22,
        "candidate_count": len(candidate_ids),
        "candidate_occurrence_ids": candidate_ids,
        "state_counts": actual_counts,
        "all_authority_closed": True,
        "any_identity_resolved": False,
        "next_required_action": expected_next,
        "atlas_sha256": atlas_sha,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the governed COL-03F artifact surface")
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    result = validate_col03f_artifact(args.root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
