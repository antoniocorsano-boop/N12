from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from experiments.cew_col03b.hypotheses import build_identity_hypothesis
from experiments.cew_col03b.local_evidence import (
    build_local_topology_signature,
    build_text_evidence,
    classify_text_relation,
    derive_local_region,
)
from experiments.cew_col03b.predecessor import (
    build_evidence_bundle_skeleton,
    validate_col03a_predecessor,
)


QUALIFIED_COL03A_SHA = "0d4a43cf02eadd2ab6f4b2641888395586c08a98"

CHANNEL_KEYS = (
    "internal_text_evidence",
    "intersecting_text_evidence",
    "nearby_text_evidence",
    "high_resolution_read_evidence",
    "callout_evidence",
    "local_topology_evidence",
    "cross_document_evidence",
)

CLOSED_AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _pretty_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _representation_bbox(occurrence: dict[str, Any]) -> dict[str, float]:
    representation = occurrence.get("primary_graphical_representation")
    if not isinstance(representation, dict) or not isinstance(representation.get("bbox"), dict):
        raise ValueError(f"occurrence lacks primary bbox: {occurrence.get('occurrence_id')}")
    box = representation["bbox"]
    return {
        "x": float(box["x"]),
        "y": float(box["y"]),
        "width": float(box["width"]),
        "height": float(box["height"]),
    }


def _center(box: dict[str, float]) -> tuple[float, float]:
    return box["x"] + box["width"] / 2.0, box["y"] + box["height"] / 2.0


def _nearest_directional_neighbors(
    occurrences: list[dict[str, Any]],
    target: dict[str, Any],
) -> dict[str, str | None]:
    target_id = str(target.get("occurrence_id") or "")
    target_center = _center(_representation_bbox(target))
    best: dict[str, tuple[float, str] | None] = {"left": None, "right": None, "up": None, "down": None}
    for other in occurrences:
        other_id = str(other.get("occurrence_id") or "")
        if not other_id or other_id == target_id:
            continue
        other_center = _center(_representation_bbox(other))
        dx = other_center[0] - target_center[0]
        dy = other_center[1] - target_center[1]
        distance = (dx * dx + dy * dy) ** 0.5
        candidates: list[str] = []
        if dx < 0:
            candidates.append("left")
        elif dx > 0:
            candidates.append("right")
        if dy < 0:
            candidates.append("up")
        elif dy > 0:
            candidates.append("down")
        for direction in candidates:
            current = best[direction]
            if current is None or (distance, other_id) < current:
                best[direction] = (distance, other_id)
    return {direction: value[1] if value is not None else None for direction, value in best.items()}


def _no_evidence_marker(*, occurrence_id: str, channel: str, reason: str) -> dict[str, Any]:
    return {
        "evidence_id": f"NONE-{occurrence_id}-{channel}",
        "occurrence_id": occurrence_id,
        "channel": channel,
        "evidence_class": "NO_EVIDENCE",
        "status": "NO_EVIDENCE",
        "reason": reason,
        "exact_source_reconstructible": True,
    }


def build_exact_source_bundles(
    *,
    ledger: dict[str, Any],
    text_observations: list[dict[str, Any]],
    raster_sha256: str,
    raster_width_px: int,
    raster_height_px: int,
) -> list[dict[str, Any]]:
    occurrences = ledger.get("occurrences") if isinstance(ledger, dict) else None
    if not isinstance(occurrences, list) or ledger.get("occurrence_count") != 22 or len(occurrences) != 22:
        raise ValueError("COL-03B exact-source builder requires exactly 22 COL-03A occurrences")
    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    ordered_occurrences = sorted((deepcopy(row) for row in occurrences), key=lambda row: str(row.get("occurrence_id") or ""))
    if [str(row.get("occurrence_id") or "") for row in ordered_occurrences] != expected_ids:
        raise ValueError("COL-03B exact-source occurrence ID drift")
    if len(str(raster_sha256)) != 64 or raster_width_px <= 0 or raster_height_px <= 0:
        raise ValueError("invalid exact-source raster provenance")

    ledger_digest = hashlib.sha256(_canonical_bytes(ledger)).hexdigest()
    sorted_text = sorted(
        (deepcopy(row) for row in text_observations if isinstance(row, dict)),
        key=lambda row: (str(row.get("token_id") or ""), str(row.get("raw_text") or "")),
    )
    bundles: list[dict[str, Any]] = []

    for occurrence in ordered_occurrences:
        occurrence_id = str(occurrence["occurrence_id"])
        occurrence_bbox = _representation_bbox(occurrence)
        local_region = derive_local_region(
            occurrence,
            margin_x=max(0.02, occurrence_bbox["width"] * 1.5),
            margin_y=max(0.02, occurrence_bbox["height"] * 1.5),
        )
        bundle = build_evidence_bundle_skeleton(occurrence, col03a_ledger_digest=ledger_digest)

        text_by_channel: dict[str, list[dict[str, Any]]] = {
            "internal_text_evidence": [],
            "intersecting_text_evidence": [],
            "nearby_text_evidence": [],
        }
        for observation in sorted_text:
            text_bbox = observation.get("bbox")
            if not isinstance(text_bbox, dict):
                continue
            relation = classify_text_relation(
                occurrence_bbox=occurrence_bbox,
                text_bbox=text_bbox,
                local_region=local_region,
            )
            if relation == "OUTSIDE":
                continue
            channel = {
                "INTERNAL": "internal_text_evidence",
                "INTERSECTING": "intersecting_text_evidence",
                "NEARBY": "nearby_text_evidence",
            }[relation]
            token_id = str(observation.get("token_id") or "")
            if not token_id:
                continue
            evidence = build_text_evidence(
                evidence_id=f"{occurrence_id}-{token_id}",
                occurrence_id=occurrence_id,
                occurrence_bbox=occurrence_bbox,
                text_bbox=text_bbox,
                local_region=local_region,
                raw_text=str(observation.get("raw_text") or ""),
                normalized_text=str(observation.get("normalized_text") or observation.get("raw_text") or ""),
                extraction_method="TESSERACT_PSM11_SUPPORT_LIKE_TOKEN",
                provenance_ref=f"{occurrence.get('page_transform_id')}:{token_id}",
            )
            evidence["channel"] = channel
            evidence["observation_root_id"] = token_id
            evidence["confidence"] = observation.get("confidence")
            text_by_channel[channel].append(evidence)

        internal = sorted(text_by_channel["internal_text_evidence"], key=lambda row: str(row["evidence_id"]))
        distinct_internal_values = sorted({str(row.get("normalized_text") or "") for row in internal if str(row.get("normalized_text") or "")})
        if len(distinct_internal_values) > 1:
            bundle["conflict_state"] = "AMBIGUOUS_TEXT_BINDING"
            for row in internal:
                row["ambiguous"] = True

        for channel in ("internal_text_evidence", "intersecting_text_evidence", "nearby_text_evidence"):
            values = sorted(text_by_channel[channel], key=lambda row: str(row["evidence_id"]))
            bundle[channel] = values or [
                _no_evidence_marker(
                    occurrence_id=occurrence_id,
                    channel=channel,
                    reason="NO_SUPPORT_LIKE_TEXT_IN_CHANNEL",
                )
            ]

        hypotheses: list[dict[str, Any]] = []
        for candidate_value in distinct_internal_values:
            supporting = [row for row in internal if str(row.get("normalized_text") or "") == candidate_value]
            hypotheses.append(
                build_identity_hypothesis(
                    occurrence_id=occurrence_id,
                    hypothesis_kind="DOCUMENTARY_LABEL_CANDIDATE",
                    candidate_value=candidate_value,
                    supporting=supporting,
                    contradicting=[],
                )
            )
        bundle["hypotheses"] = sorted(hypotheses, key=lambda row: str(row["hypothesis_id"]))
        if bundle["hypotheses"]:
            bundle["documentary_identity_resolution_state"] = (
                "MULTIPLE_CANDIDATES" if len(bundle["hypotheses"]) > 1 else "CANDIDATE_ONLY"
            )

        bundle["high_resolution_read_evidence"] = [
            {
                "evidence_id": f"HR-{occurrence_id}",
                "occurrence_id": occurrence_id,
                "channel": "high_resolution_read_evidence",
                "evidence_class": "HIGH_RESOLUTION_SOURCE_REGION",
                "status": "OBSERVED",
                "region_bbox": local_region,
                "raster_sha256": raster_sha256,
                "raster_width_px": raster_width_px,
                "raster_height_px": raster_height_px,
                "source_version_id": occurrence.get("source_version_id"),
                "page_id": occurrence.get("page_id"),
                "page_transform_id": occurrence.get("page_transform_id"),
                "exact_source_reconstructible": True,
            }
        ]
        bundle["callout_evidence"] = [
            _no_evidence_marker(
                occurrence_id=occurrence_id,
                channel="callout_evidence",
                reason="NO_DETERMINISTIC_CONNECTOR_BINDING_ESTABLISHED",
            )
        ]
        topology = build_local_topology_signature(
            occurrence_id=occurrence_id,
            neighbors=_nearest_directional_neighbors(ordered_occurrences, occurrence),
            contacts=[],
            bay_order=None,
            provenance_ref=f"{occurrence.get('page_transform_id')}:GOVERNED_OCCURRENCE_NEIGHBORHOOD",
        )
        topology["channel"] = "local_topology_evidence"
        topology["topology_scope"] = "DOCUMENTARY_OCCURRENCE_NEIGHBORHOOD_ONLY"
        bundle["local_topology_evidence"] = [topology]
        bundle["cross_document_evidence"] = [
            _no_evidence_marker(
                occurrence_id=occurrence_id,
                channel="cross_document_evidence",
                reason="NO_GOVERNED_HISTORICAL_COORDINATE_CORRESPONDENCE_ESTABLISHED",
            )
        ]
        bundles.append(finalize_evidence_bundle(bundle))

    return bundles


def finalize_evidence_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(bundle)
    missing: list[str] = []
    for channel in CHANNEL_KEYS:
        values = result.get(channel)
        if not isinstance(values, list) or not values:
            missing.append(channel)
    result["missing_channels"] = missing
    result["documentary_evidence_state"] = "COMPLETE" if not missing else "PARTIAL"
    if not result.get("documentary_identity_resolution_state"):
        result["documentary_identity_resolution_state"] = "UNRESOLVED"
    return result


def build_documentary_reconciliation(
    bundles: list[dict[str, Any]],
    *,
    historical_manifest: dict[str, Any],
) -> dict[str, Any]:
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    counts = {channel: 0 for channel in CHANNEL_KEYS}
    no_evidence_counts = {channel: 0 for channel in CHANNEL_KEYS}
    hypothesis_states: dict[str, int] = {}
    ambiguous_occurrences: list[str] = []
    contradictory_occurrences: list[str] = []
    uses_historical = False

    for bundle in ordered:
        for channel in CHANNEL_KEYS:
            values = bundle.get(channel)
            if not isinstance(values, list):
                continue
            counts[channel] += len(values)
            no_evidence_counts[channel] += sum(
                1 for item in values if isinstance(item, dict) and item.get("evidence_class") in {"NO_EVIDENCE", "NOT_APPLICABLE"}
            )
            if channel == "cross_document_evidence":
                uses_historical = uses_historical or any(
                    isinstance(item, dict) and item.get("evidence_class") != "NO_EVIDENCE" for item in values
                )
        for hypothesis in bundle.get("hypotheses", []):
            if isinstance(hypothesis, dict):
                state = str(hypothesis.get("state") or "UNSPECIFIED")
                hypothesis_states[state] = hypothesis_states.get(state, 0) + 1
                if state == "AMBIGUOUS":
                    ambiguous_occurrences.append(str(bundle.get("occurrence_id")))
                if state == "CONTRADICTED":
                    contradictory_occurrences.append(str(bundle.get("occurrence_id")))
        if bundle.get("conflict_state") in {"AMBIGUOUS_TEXT_BINDING", "AMBIGUOUS_CROSS_DOCUMENT_MATCH"}:
            ambiguous_occurrences.append(str(bundle.get("occurrence_id")))
        if bundle.get("conflict_state") == "CONTRADICTORY_DOCUMENTARY_EVIDENCE":
            contradictory_occurrences.append(str(bundle.get("occurrence_id")))

    artifacts = historical_manifest.get("artifacts", []) if isinstance(historical_manifest, dict) else []
    historical_provenance_complete = True
    if uses_historical:
        if not isinstance(artifacts, list) or not artifacts:
            historical_provenance_complete = False
        else:
            for artifact in artifacts:
                if not isinstance(artifact, dict) or any(not artifact.get(key) for key in ("artifact_id", "path", "version", "sha256")):
                    historical_provenance_complete = False
                    break

    ambiguous_occurrences = sorted(set(ambiguous_occurrences))
    contradictory_occurrences = sorted(set(contradictory_occurrences))
    return {
        "occurrence_count": len(ordered),
        "occurrence_ids": [str(row.get("occurrence_id") or "") for row in ordered],
        "evidence_counts_by_channel": counts,
        "explicit_no_evidence_counts_by_channel": no_evidence_counts,
        "hypothesis_states": dict(sorted(hypothesis_states.items())),
        "ambiguous_occurrence_ids": ambiguous_occurrences,
        "contradictory_occurrence_ids": contradictory_occurrences,
        "historical_artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
        "historical_provenance_complete": historical_provenance_complete,
        "human_review_required": bool(ambiguous_occurrences or contradictory_occurrences),
        "bundle_digest": hashlib.sha256(_canonical_bytes(ordered)).hexdigest(),
    }


def build_documentary_closure(
    *,
    bundles: list[dict[str, Any]],
    reconciliation: dict[str, Any],
    predecessor_closure: dict[str, Any],
    qualified_base_sha: str,
) -> dict[str, Any]:
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    blocking: list[str] = []
    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    ids = [str(row.get("occurrence_id") or "") for row in ordered]

    if qualified_base_sha != QUALIFIED_COL03A_SHA:
        blocking.append("QUALIFIED_BASE_SHA_DRIFT")
    if predecessor_closure.get("occurrence_ledger_complete") is not True:
        blocking.append("PREDECESSOR_NOT_COMPLETE")
    if ids != expected_ids or len(ordered) != 22:
        blocking.append("OCCURRENCE_SET_DRIFT")
    if reconciliation.get("occurrence_count") != 22:
        blocking.append("RECONCILIATION_COUNT_DRIFT")
    if reconciliation.get("historical_provenance_complete") is not True:
        blocking.append("HISTORICAL_ARTIFACT_PROVENANCE_MISSING")

    if any(row.get("documentary_evidence_state") != "COMPLETE" or row.get("missing_channels") not in ([], None) for row in ordered):
        blocking.append("EVIDENCE_COLLECTION_INCOMPLETE")
    if any(row.get("exact_source_reconstructible") is not True for row in ordered):
        blocking.append("SOURCE_RECONSTRUCTION_FAILED")
    if any(row.get("lineage_complete") is not True for row in ordered):
        blocking.append("COL03A_LINEAGE_DRIFT")
    if any(any(row.get(key) is not False for key in CLOSED_AUTHORITY_KEYS) for row in ordered):
        blocking.append("AUTHORITY_DRIFT")

    blocking = sorted(set(blocking))
    all_resolved = bool(ordered) and all(row.get("documentary_identity_resolved") is True for row in ordered)
    return {
        "qualified_col03a_sha": qualified_base_sha,
        "documentary_identity_evidence_collection_complete": not blocking,
        "all_occurrences_identity_resolved": all_resolved,
        "occurrence_count": len(ordered),
        "blocking_reasons": blocking,
        "human_review_required": bool(reconciliation.get("human_review_required")),
        "authority": {key: False for key in CLOSED_AUTHORITY_KEYS},
        "bundle_digest": reconciliation.get("bundle_digest"),
    }


def write_col03b_artifacts(
    output_dir: Path,
    *,
    bundles: list[dict[str, Any]],
    reconciliation: dict[str, Any],
    closure: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    hypotheses = sorted(
        [deepcopy(hypothesis) for bundle in ordered for hypothesis in bundle.get("hypotheses", []) if isinstance(hypothesis, dict)],
        key=lambda row: (str(row.get("occurrence_id") or ""), str(row.get("hypothesis_id") or "")),
    )
    payloads = {
        "documentary-identity-evidence-ledger.json": {
            "occurrence_count": len(ordered),
            "occurrences": ordered,
        },
        "documentary-identity-hypotheses.json": {
            "hypothesis_count": len(hypotheses),
            "hypotheses": hypotheses,
        },
        "documentary-identity-reconciliation.json": deepcopy(reconciliation),
        "documentary-identity-evidence-closure.json": deepcopy(closure),
    }
    digests: dict[str, str] = {}
    for filename, payload in sorted(payloads.items()):
        data = _pretty_bytes(payload)
        (output_dir / filename).write_bytes(data)
        digests[filename] = _digest_bytes(data)
    return digests


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _replay_exact_source_text() -> tuple[list[dict[str, Any]], str, int, int, str]:
    import cv2

    from experiments.cew_col02.axis_aware_whole_symbol_exact_source import (
        _regenerate_source_analysis_and_proposals,
    )
    from experiments.cew_col02.exact_source_audit import (
        _normalized_text_observations,
        _tesseract_tsv,
        canonical_bytes,
    )

    image, analysis, _proposals = _regenerate_source_analysis_and_proposals()
    runner_temp = Path(os.environ["RUNNER_TEMP"])
    analysis_path = runner_temp / "cew-col03b-structural-workarea.png"
    if not cv2.imwrite(str(analysis_path), analysis):
        raise RuntimeError("cannot write deterministic COL-03B analysis raster")

    tsv_a, version_a = _tesseract_tsv(analysis_path)
    tsv_b, version_b = _tesseract_tsv(analysis_path)
    if version_a != version_b:
        raise ValueError("Tesseract version drift during COL-03B replay")

    height, width = image.shape[:2]
    text_a = _normalized_text_observations(tsv_a, width, height)
    text_b = _normalized_text_observations(tsv_b, width, height)
    if canonical_bytes(text_a) != canonical_bytes(text_b):
        raise ValueError("COL-03B text observation replay is not deterministic")

    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("cannot encode exact-source raster for provenance digest")
    raster_sha256 = hashlib.sha256(encoded.tobytes()).hexdigest()
    return text_a, raster_sha256, width, height, version_a


def main() -> None:
    predecessor_root = Path("evidence/cew-col03a")
    ledger = _load_json(predecessor_root / "column-occurrence-ledger.json")
    reconciliation_a = _load_json(predecessor_root / "column-occurrence-reconciliation.json")
    closure_a = _load_json(predecessor_root / "column-occurrence-ledger-closure.json")

    validate_col03a_predecessor(
        ledger=ledger,
        reconciliation=reconciliation_a,
        closure=closure_a,
        expected_sha=QUALIFIED_COL03A_SHA,
    )

    text_observations, raster_sha256, width, height, tesseract_version = _replay_exact_source_text()
    bundles_a = build_exact_source_bundles(
        ledger=ledger,
        text_observations=text_observations,
        raster_sha256=raster_sha256,
        raster_width_px=width,
        raster_height_px=height,
    )
    bundles_b = build_exact_source_bundles(
        ledger=deepcopy(ledger),
        text_observations=list(reversed(deepcopy(text_observations))),
        raster_sha256=raster_sha256,
        raster_width_px=width,
        raster_height_px=height,
    )
    if _canonical_bytes(bundles_a) != _canonical_bytes(bundles_b):
        raise ValueError("COL-03B bundle replay is not deterministic")

    historical_manifest = {
        "artifacts": [],
        "inventory_ref": "archive/ARTEFATTI_STORICI.md",
        "materialized_artifacts": False,
        "reason": "INVENTORY_PRESENT_HISTORICAL_DXF_CSV_NOT_MATERIALIZED_ON_QUALIFIED_BRANCH",
    }
    reconciliation_b = build_documentary_reconciliation(
        bundles_a,
        historical_manifest=historical_manifest,
    )
    closure_b = build_documentary_closure(
        bundles=bundles_a,
        reconciliation=reconciliation_b,
        predecessor_closure=closure_a,
        qualified_base_sha=QUALIFIED_COL03A_SHA,
    )
    if closure_b["documentary_identity_evidence_collection_complete"] is not True:
        raise ValueError(f"COL-03B closure blocked: {closure_b['blocking_reasons']}")

    output_root = Path("evidence/cew-col03b")
    digests = write_col03b_artifacts(
        output_root,
        bundles=bundles_a,
        reconciliation=reconciliation_b,
        closure=closure_b,
    )
    print(
        json.dumps(
            {
                "status": "CEW_COL03B_EXACT_SOURCE_EVIDENCE_COLLECTION_PASS",
                "occurrence_count": len(bundles_a),
                "text_observation_count": len(text_observations),
                "hypothesis_count": sum(len(row.get("hypotheses", [])) for row in bundles_a),
                "human_review_required": reconciliation_b["human_review_required"],
                "historical_artifacts_materialized": False,
                "tesseract_version": tesseract_version,
                "digests": digests,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
