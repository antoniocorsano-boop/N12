from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any


EXPECTED_OCCURRENCE_IDS = tuple(f"COL-OCC-{index:04d}" for index in range(1, 23))
PRIORITY_OCCURRENCE_IDS = ("COL-OCC-0001", "COL-OCC-0015")
DIRECT_RELATIONS = {"INTERNAL", "INTERSECTING"}
FIXED_OCR_CONFIGURATIONS = {"PSM6", "PSM11"}
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

_DECIMAL_LABEL_RE = re.compile(r"^(?:[1-9][0-9]{0,2})$")


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_label(value: Any) -> str | None:
    text = str(value or "").strip()
    if not _DECIMAL_LABEL_RE.fullmatch(text):
        return None
    return str(int(text))


def inspection_priority(
    occurrence_ids: list[str],
    documentary_candidates: dict[str, list[str]],
) -> list[str]:
    """Return the deterministic COL-03F candidate-first review order."""

    ids = sorted(set(str(value) for value in occurrence_ids if str(value)))
    if ids != list(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03F_OCCURRENCE_SET_DRIFT")

    normalized_candidates: dict[str, list[str]] = {}
    for occurrence_id, values in documentary_candidates.items():
        candidates = sorted(
            {
                label
                for value in values
                if (label := _canonical_label(value)) is not None
            },
            key=lambda value: int(value),
        )
        if candidates:
            normalized_candidates[str(occurrence_id)] = candidates

    if normalized_candidates.get("COL-OCC-0001") != ["4"] or normalized_candidates.get("COL-OCC-0015") != ["30"]:
        raise ValueError("COL03F_DOCUMENTARY_CANDIDATE_PREDECESSOR_DRIFT")
    if set(normalized_candidates) != set(PRIORITY_OCCURRENCE_IDS):
        raise ValueError("COL03F_DOCUMENTARY_CANDIDATE_PREDECESSOR_DRIFT")

    remainder = [value for value in ids if value not in PRIORITY_OCCURRENCE_IDS]
    return [*PRIORITY_OCCURRENCE_IDS, *remainder]


def _eligible_direct_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        if str(observation.get("relation") or "") not in DIRECT_RELATIONS:
            continue
        label = _canonical_label(observation.get("normalized_text"))
        if label is None:
            continue
        if observation.get("exact_source_reconstructible") is not True:
            continue
        if not observation.get("provenance_ref"):
            continue
        normalized = deepcopy(observation)
        normalized["normalized_text"] = label
        eligible.append(normalized)
    return sorted(
        eligible,
        key=lambda item: (
            int(str(item["normalized_text"])),
            str(item.get("ocr_configuration") or ""),
            str(item.get("region_class") or ""),
            str(item.get("provenance_ref") or ""),
        ),
    )


def classify_acquisition_state(
    documentary_candidates: list[str],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify focused primary-source observations without promoting identity."""

    predecessor_values = sorted(
        {
            label
            for value in documentary_candidates
            if (label := _canonical_label(value)) is not None
        },
        key=lambda value: int(value),
    )
    if len(predecessor_values) > 1:
        raise ValueError("COL03F_DOCUMENTARY_PREDECESSOR_AMBIGUOUS")

    direct = _eligible_direct_observations(observations)
    values = sorted({str(item["normalized_text"]) for item in direct}, key=lambda value: int(value))
    configurations_by_value = {
        value: sorted(
            {
                str(item.get("ocr_configuration") or "")
                for item in direct
                if item["normalized_text"] == value and str(item.get("ocr_configuration") or "")
            }
        )
        for value in values
    }

    state: str
    candidate_values: list[str] = []

    if not values:
        state = "NO_DIRECT_LABEL_OBSERVED"
    elif len(values) > 1:
        state = "AMBIGUOUS_DIRECT_LABELS"
    elif predecessor_values:
        observed = values[0]
        predecessor = predecessor_values[0]
        if observed == predecessor:
            state = "CORROBORATED_EXISTING_LABEL_CANDIDATE"
            candidate_values = [observed]
        else:
            state = "CONTRADICTS_EXISTING_DOCUMENTARY_CANDIDATE"
    else:
        observed = values[0]
        configurations = set(configurations_by_value[observed])
        if FIXED_OCR_CONFIGURATIONS.issubset(configurations):
            state = "NEW_MULTI_CONFIG_LABEL_CANDIDATE"
            candidate_values = [observed]
        else:
            state = "SINGLE_CONFIG_DIRECT_OBSERVATION"

    supporting = [
        deepcopy(item)
        for item in direct
        if item["normalized_text"] in set(candidate_values)
    ]
    result = {
        "state": state,
        "candidate_values": candidate_values,
        "direct_observed_values": values,
        "documentary_candidate_values": predecessor_values,
        "ocr_configurations_by_value": configurations_by_value,
        "eligible_direct_observation_count": len(direct),
        "supporting_observations": supporting,
        "identity_promoted": False,
    }
    result["classification_digest"] = _canonical_digest(result)
    return result


def _rows_by_occurrence(ledger: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    rows = ledger.get(key)
    if not isinstance(rows, list):
        raise ValueError("COL03F_OCCURRENCE_SET_DRIFT")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("COL03F_OCCURRENCE_SET_DRIFT")
        occurrence_id = str(row.get("occurrence_id") or "")
        if not occurrence_id or occurrence_id in indexed:
            raise ValueError("COL03F_OCCURRENCE_SET_DRIFT")
        indexed[occurrence_id] = row
    if set(indexed) != set(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03F_OCCURRENCE_SET_DRIFT")
    return indexed


def _documentary_candidate_map(documentary_rows: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for occurrence_id, row in documentary_rows.items():
        hypotheses = row.get("hypotheses") or []
        if not isinstance(hypotheses, list):
            raise ValueError("COL03F_DOCUMENTARY_PREDECESSOR_DRIFT")
        values = sorted(
            {
                label
                for hypothesis in hypotheses
                if isinstance(hypothesis, dict)
                and (label := _canonical_label(hypothesis.get("candidate_value"))) is not None
            },
            key=lambda value: int(value),
        )
        if values:
            result[occurrence_id] = values
    return result


def _validate_source_ref(source_ref: dict[str, Any]) -> dict[str, Any]:
    required = (
        "source_version_id",
        "page_id",
        "page_transform_id",
        "source_sha256",
        "raster_sha256",
        "raster_width_px",
        "raster_height_px",
    )
    if any(not source_ref.get(key) for key in required):
        raise ValueError("COL03F_SOURCE_PROVENANCE_INCOMPLETE")
    if str(source_ref["source_version_id"]) != "CEW-N12-SRC-TAV05S-V2143DBCF":
        raise ValueError("COL03F_SOURCE_VERSION_DRIFT")
    if str(source_ref["source_sha256"]) != "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580":
        raise ValueError("COL03F_SOURCE_DIGEST_DRIFT")
    return deepcopy(source_ref)


def build_primary_bridge_ledger(
    *,
    occurrence_ledger: dict[str, Any],
    documentary_ledger: dict[str, Any],
    col03e_dossiers: dict[str, Any],
    focused_observations: dict[str, list[dict[str, Any]]],
    source_ref: dict[str, Any],
    crop_manifests: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build the authority-closed, candidate-first COL-03F evidence ledger."""

    occurrence_rows = _rows_by_occurrence(occurrence_ledger, "occurrences")
    documentary_rows = _rows_by_occurrence(documentary_ledger, "occurrences")
    dossier_rows = _rows_by_occurrence(col03e_dossiers, "dossiers")
    documentary_candidates = _documentary_candidate_map(documentary_rows)
    order = inspection_priority(list(occurrence_rows), documentary_candidates)
    validated_source_ref = _validate_source_ref(source_ref)

    if set(focused_observations) != set(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03F_FOCUSED_OBSERVATION_SET_DRIFT")
    if set(crop_manifests) != set(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03F_CROP_MANIFEST_SET_DRIFT")

    ledger_rows: list[dict[str, Any]] = []
    for queue_index, occurrence_id in enumerate(order, start=1):
        occurrence = occurrence_rows[occurrence_id]
        dossier = dossier_rows[occurrence_id]
        if dossier.get("identity_promoted") is not False:
            raise ValueError("COL03F_PREDECESSOR_IDENTITY_AUTHORITY_DRIFT")
        dossier_digest = str(dossier.get("dossier_digest") or "")
        if not dossier_digest:
            raise ValueError("COL03F_PREDECESSOR_DOSSIER_DIGEST_MISSING")

        crop_manifest = deepcopy(crop_manifests[occurrence_id])
        for region_class in ("FOOTPRINT", "LOCAL", "CONTEXT"):
            region = crop_manifest.get(region_class)
            if not isinstance(region, dict) or not region.get("bounds_px"):
                raise ValueError("COL03F_CROP_MANIFEST_INCOMPLETE")
        for path_key, digest_key in (
            ("source_only_path", "source_only_sha256"),
            ("target_overlay_path", "target_overlay_sha256"),
        ):
            if not crop_manifest.get(path_key) or len(str(crop_manifest.get(digest_key) or "")) != 64:
                raise ValueError("COL03F_REVIEW_IMAGE_PROVENANCE_INCOMPLETE")

        classification = classify_acquisition_state(
            documentary_candidates.get(occurrence_id, []),
            focused_observations[occurrence_id],
        )
        if classification["state"] not in ALLOWED_STATES:
            raise ValueError("COL03F_ACQUISITION_STATE_INVALID")

        occurrence_bbox = (
            occurrence.get("primary_graphical_representation", {}).get("bbox")
            if isinstance(occurrence.get("primary_graphical_representation"), dict)
            else None
        )
        if not isinstance(occurrence_bbox, dict):
            raise ValueError("COL03F_OCCURRENCE_BBOX_MISSING")

        row: dict[str, Any] = {
            "schema": "CEW_COL03F_PRIMARY_BRIDGE_OCCURRENCE_v1",
            "queue_index": queue_index,
            "occurrence_id": occurrence_id,
            "col03e_dossier_digest": dossier_digest,
            "occurrence_bbox": deepcopy(occurrence_bbox),
            "source_ref": deepcopy(validated_source_ref),
            "crop_manifest": crop_manifest,
            "focused_observations": sorted(
                (deepcopy(item) for item in focused_observations[occurrence_id] if isinstance(item, dict)),
                key=lambda item: (
                    str(item.get("region_class") or ""),
                    str(item.get("ocr_configuration") or ""),
                    str(item.get("normalized_text") or ""),
                    str(item.get("provenance_ref") or ""),
                ),
            ),
            "acquisition_state": classification["state"],
            "candidate_values": classification["candidate_values"],
            "direct_observed_values": classification["direct_observed_values"],
            "documentary_candidate_values": classification["documentary_candidate_values"],
            "classification_digest": classification["classification_digest"],
            "identity_promoted": False,
            "historical_identity_positive_evidence_used": False,
        }
        for key in AUTHORITY_KEYS:
            row[key] = False
        row["row_digest"] = _canonical_digest(row)
        ledger_rows.append(row)

    return {
        "schema": "CEW_COL03F_PRIMARY_BRIDGE_EVIDENCE_LEDGER_v1",
        "source_ref": validated_source_ref,
        "occurrence_count": len(ledger_rows),
        "inspection_order": order,
        "occurrences": ledger_rows,
        "candidate_occurrence_ids": [
            row["occurrence_id"] for row in ledger_rows if row["acquisition_state"] in CANDIDATE_STATES
        ],
        "identity_promotion_authorized": False,
    }
