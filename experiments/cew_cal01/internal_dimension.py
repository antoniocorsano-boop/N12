from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text, proposal_from_ocr_token
from experiments.cew_cal01.exact_source import SOURCE_SHA256, _canonical_digest
from experiments.cew_cal01.numeric_role import classify_numeric_graphic_role
from experiments.cew_cal01.oriented_discovery import _map_oriented_bbox_to_page, _rotate_image
from experiments.cew_cal01.oriented_refinement import cluster_numeric_observations_by_location
from experiments.cew_cal01.perimeter_dimension import _prepare_ocr_variant, _run_numeric_tesseract
from experiments.cew_cal01.role_verification import detect_nearby_closed_frame, select_ocr_consensus
from experiments.cew_cal01.semantic_exact_source import collect_local_line_evidence


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}

OCR_PREPROCESS_MODES = ("RAW_GRAYSCALE", "CLAHE", "BINARY_OTSU")
OCR_ROTATIONS = (0, 90, 180, 270)
OCR_SCALE = 1.0
OCR_PSM = 11
LOCATION_TOLERANCE_PX = 18.0


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return prefix + hashlib.sha256(encoded).hexdigest()[:20]


def select_internal_search_roi(perimeter_payload: dict[str, Any]) -> list[int]:
    """Return the exact-source structural envelope only after perimeter search closes empty."""

    if perimeter_payload.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_INTERNAL_SOURCE_DIGEST_DRIFT")
    if perimeter_payload.get("historical_comparator_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_HISTORICAL_INPUT_FORBIDDEN")
    if perimeter_payload.get("historical_affine_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_HISTORICAL_INPUT_FORBIDDEN")
    if perimeter_payload.get("tav02s_evidence_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_TAV02_INPUT_FORBIDDEN")
    if int(perimeter_payload.get("primary_anchor_count", -1)) != 0:
        raise RuntimeError("CAL01_INTERNAL_UPSTREAM_AUTHORITY_DRIFT")

    candidate_count = int(perimeter_payload.get("candidate_count", -1))
    status = str(perimeter_payload.get("status") or "")
    if candidate_count != 0 or status != "PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED":
        raise RuntimeError("CAL01_INTERNAL_SEARCH_DEFERRED_PERIMETER_CANDIDATES_PRESENT")

    raw_bbox = perimeter_payload.get("structural_plan_envelope", {}).get("envelope_bbox_source_px")
    if not isinstance(raw_bbox, (list, tuple)) or len(raw_bbox) != 4:
        raise RuntimeError("CAL01_INTERNAL_SOURCE_ENVELOPE_REQUIRED")
    bbox = [int(round(float(value))) for value in raw_bbox]
    left, top, right, bottom = bbox
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise RuntimeError("CAL01_INTERNAL_SOURCE_ENVELOPE_INVALID")
    return bbox


def classify_internal_role_result(cluster: dict[str, Any], role_result: dict[str, Any]) -> dict[str, Any]:
    """Admit only semantic LINEAR_DIMENSION results to human-review candidate state."""

    cluster_index = int(cluster.get("cluster_index", -1))
    role = str(role_result.get("role") or "UNRESOLVED")
    reason = role_result.get("reason")

    if role != "LINEAR_DIMENSION":
        return {
            "accepted": False,
            "rejected": {
                "cluster_index": cluster_index,
                "role": role,
                "reason": reason,
                "engineering_authority_effect": "NONE",
            },
        }

    relation = role_result.get("dimension_relation")
    if not isinstance(relation, dict) or relation.get("confirmed") is not True:
        return {
            "accepted": False,
            "rejected": {
                "cluster_index": cluster_index,
                "role": "UNRESOLVED",
                "reason": "LINEAR_DIMENSION_WITHOUT_CONFIRMED_RELATION",
                "engineering_authority_effect": "NONE",
            },
        }
    endpoint_a = relation.get("endpoint_a_px")
    endpoint_b = relation.get("endpoint_b_px")
    if not isinstance(endpoint_a, (list, tuple)) or not isinstance(endpoint_b, (list, tuple)):
        return {
            "accepted": False,
            "rejected": {
                "cluster_index": cluster_index,
                "role": "UNRESOLVED",
                "reason": "LINEAR_DIMENSION_ENDPOINTS_REQUIRED",
                "engineering_authority_effect": "NONE",
            },
        }

    identity = {
        "cluster_index": cluster_index,
        "documented_text": role_result.get("documented_text"),
        "endpoint_a_px": [float(value) for value in endpoint_a],
        "endpoint_b_px": [float(value) for value in endpoint_b],
    }
    representative = cluster.get("representative") or {}
    candidate = {
        "candidate_id": _stable_id("CEW-CAL01-INTDIM-", identity),
        "cluster_index": cluster_index,
        "semantic_role": "INTERNAL_LINEAR_DIMENSION_CANDIDATE",
        "documented_text": role_result.get("documented_text"),
        "source_bbox_px": list(representative.get("bbox_px") or []),
        "role_reason": reason,
        "dimension_relation": dict(relation),
        "primary_visual_validation_required": True,
        "validation_state": "HUMAN_REVIEW_REQUIRED",
        "fit_eligible": False,
        "eligible_for_anchor": False,
        "metric_anchor_promoted": False,
        "engineering_authority_effect": "NONE",
    }
    normalized = normalize_dimension_text(role_result.get("documented_text"))
    if normalized is not None:
        candidate["normalized_metric_text"] = normalized[0]
        candidate["proposed_metric_value_m"] = normalized[1]
    return {"accepted": True, "candidate": candidate}


def build_internal_manifest(
    *,
    source: dict[str, Any],
    perimeter: dict[str, Any],
    search_roi_px: list[int],
    location_clusters: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    ocr_pass_count: int,
) -> dict[str, Any]:
    """Build deterministic non-authoritative internal-discovery evidence."""

    ordered_candidates = sorted((dict(item) for item in candidates), key=lambda item: str(item.get("candidate_id") or ""))
    ordered_rejected = sorted((dict(item) for item in rejected), key=lambda item: int(item.get("cluster_index", -1)))
    ordered_clusters = sorted((dict(item) for item in location_clusters), key=lambda item: int(item.get("cluster_index", -1)))
    observation_count = sum(int(item.get("observation_count", 0)) for item in ordered_clusters)
    role_counts = {"LINEAR_DIMENSION": len(ordered_candidates), "SECTION_MEASURE": 0, "UNRESOLVED": 0}
    for item in ordered_rejected:
        role = str(item.get("role") or "UNRESOLVED")
        role_counts[role] = role_counts.get(role, 0) + 1

    result = {
        "schema": "CEW_CAL01_INTERNAL_DIMENSION_DISCOVERY_v1",
        "program": "CEW-CAL-01",
        "source": dict(source),
        "perimeter_trigger": {
            "perimeter_discovery_digest": perimeter.get("perimeter_discovery_digest"),
            "status": perimeter.get("status"),
            "candidate_count": int(perimeter.get("candidate_count", 0)),
        },
        "search_roi_source_px": [int(value) for value in search_roi_px],
        "ocr_strategy": {
            "preprocess_modes": list(OCR_PREPROCESS_MODES),
            "rotations_degrees": list(OCR_ROTATIONS),
            "psm": OCR_PSM,
            "scale": OCR_SCALE,
            "line_suppression": False,
            "numeric_whitelist": "0123456789.,",
            "location_tolerance_px": LOCATION_TOLERANCE_PX,
        },
        "ocr_pass_count": int(ocr_pass_count),
        "numeric_observation_count": observation_count,
        "location_cluster_count": len(ordered_clusters),
        "role_counts": role_counts,
        "candidate_count": len(ordered_candidates),
        "candidates": ordered_candidates,
        "rejected_location_count": len(ordered_rejected),
        "rejected_locations": ordered_rejected,
        "location_clusters": ordered_clusters,
        "status": "INTERNAL_LINEAR_DIMENSION_CANDIDATES_OBSERVED" if ordered_candidates else "INTERNAL_DIMENSION_CHAINS_NOT_OBSERVED",
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    digest_payload = dict(result)
    result["internal_discovery_digest"] = _canonical_digest(digest_payload)
    return result


def _canonical_reading(value: Any) -> str:
    return str(value or "").strip().replace(" ", "").replace(",", ".")


def _representative_for_consensus(cluster: dict[str, Any], consensus_text: str | None) -> dict[str, Any]:
    observations = [dict(item) for item in (cluster.get("observations") or [])]
    if consensus_text:
        matching = [item for item in observations if _canonical_reading(item.get("raw_ocr_text")) == consensus_text]
        if matching:
            return max(matching, key=lambda item: (float(item.get("ocr_confidence", 0.0)), str(item.get("proposal_id") or "")))
    representative = cluster.get("representative")
    if isinstance(representative, dict):
        return dict(representative)
    if observations:
        return max(observations, key=lambda item: (float(item.get("ocr_confidence", 0.0)), str(item.get("proposal_id") or "")))
    raise RuntimeError("CAL01_INTERNAL_CLUSTER_REPRESENTATIVE_REQUIRED")


def build_internal_dimension_discovery(
    *,
    image_path: Path,
    base_discovery_path: Path,
    perimeter_discovery_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    import cv2

    base = json.loads(base_discovery_path.read_text(encoding="utf-8"))
    perimeter = json.loads(perimeter_discovery_path.read_text(encoding="utf-8"))
    if base.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_INTERNAL_BASE_SOURCE_DIGEST_DRIFT")
    if base.get("historical_comparator_loaded") is not False or base.get("historical_affine_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_BASE_HISTORICAL_INPUT_FORBIDDEN")
    if base.get("tav02s_evidence_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_BASE_TAV02_INPUT_FORBIDDEN")

    search_roi = select_internal_search_roi(perimeter)
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError("CAL01_INTERNAL_RASTER_UNREADABLE")
    page_height, page_width = gray.shape[:2]
    expected_width = int(base.get("raster", {}).get("width_px") or 0)
    expected_height = int(base.get("raster", {}).get("height_px") or 0)
    if (page_width, page_height) != (expected_width, expected_height):
        raise RuntimeError("CAL01_INTERNAL_RASTER_FRAME_DRIFT")

    left, top, right, bottom = search_roi
    if right > page_width or bottom > page_height:
        raise RuntimeError("CAL01_INTERNAL_ROI_OUT_OF_FRAME")
    crop = gray[top:bottom, left:right]
    if crop.size == 0:
        raise RuntimeError("CAL01_INTERNAL_ROI_EMPTY")

    observations: list[dict[str, Any]] = []
    ocr_pass_count = 0
    for preprocess_mode in OCR_PREPROCESS_MODES:
        prepared = _prepare_ocr_variant(crop, preprocess_mode)
        for rotation in OCR_ROTATIONS:
            oriented = _rotate_image(prepared, rotation)
            ocr_pass_count += 1
            for token in _run_numeric_tesseract(oriented, psm=OCR_PSM):
                if normalize_dimension_text(token.get("text")) is None:
                    continue
                source_bbox = _map_oriented_bbox_to_page(
                    token["bbox_px"],
                    tile_bounds=(left, top, right, bottom),
                    rotation_degrees=rotation,
                    ocr_scale=OCR_SCALE,
                )
                proposal = proposal_from_ocr_token(
                    {"text": token["text"], "confidence": token["confidence"], "bbox_px": source_bbox},
                    page_width=page_width,
                    page_height=page_height,
                )
                proposal.update(
                    {
                        "raw_ocr_text": str(token["text"]),
                        "ocr_rotation_degrees": int(rotation),
                        "preprocess_mode": preprocess_mode,
                        "ocr_method": f"INTERNAL_{preprocess_mode}_PSM{OCR_PSM}",
                        "ocr_scale": OCR_SCALE,
                        "tile_index": 0,
                        "tile_bounds_px": list(search_roi),
                    }
                )
                observations.append(proposal)

    raw_clusters = cluster_numeric_observations_by_location(observations, centroid_tolerance_px=LOCATION_TOLERANCE_PX)
    clusters: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for cluster_index, raw_cluster in enumerate(raw_clusters):
        cluster = dict(raw_cluster)
        cluster["cluster_index"] = cluster_index
        consensus = select_ocr_consensus(cluster.get("readings") or [], minimum_count=2, minimum_margin=1)
        representative = _representative_for_consensus(cluster, consensus.get("text"))
        cluster["representative"] = representative
        bbox = [float(value) for value in representative.get("bbox_px", [])]
        if len(bbox) != 4:
            raise RuntimeError("CAL01_INTERNAL_CLUSTER_BBOX_REQUIRED")
        line_segments, line_evidence = collect_local_line_evidence(gray, bbox)
        closed_frame = detect_nearby_closed_frame(line_segments, token_bbox_px=bbox)
        role_result = classify_numeric_graphic_role(
            raw_text=str(representative.get("raw_ocr_text") or ""),
            consensus_text=consensus.get("text"),
            consensus_count=int(consensus.get("count", 0)),
            ocr_rotation_degrees=int(representative.get("ocr_rotation_degrees", 0)),
            token_bbox_px=bbox,
            line_segments=line_segments,
            nearby_closed_frame=bool(closed_frame.get("detected")),
        )
        cluster["ocr_consensus"] = consensus
        cluster["line_evidence"] = {key: value for key, value in line_evidence.items() if not key.startswith("_")}
        cluster["nearby_closed_frame"] = closed_frame
        cluster["semantic_role"] = role_result
        clusters.append(cluster)

        classified = classify_internal_role_result(cluster, role_result)
        if classified["accepted"]:
            candidate = dict(classified["candidate"])
            candidate["ocr_consensus"] = consensus
            candidate["readings"] = list(cluster.get("readings") or [])
            candidates.append(candidate)
        else:
            rejected_row = dict(classified["rejected"])
            rejected_row["source_bbox_px"] = bbox
            rejected_row["readings"] = list(cluster.get("readings") or [])
            rejected_row["ocr_consensus"] = consensus
            rejected.append(rejected_row)

    result = build_internal_manifest(
        source=dict(base["source"]),
        perimeter=perimeter,
        search_roi_px=search_roi,
        location_clusters=clusters,
        candidates=candidates,
        rejected=rejected,
        ocr_pass_count=ocr_pass_count,
    )
    result["base_discovery_digest"] = base.get("discovery_digest")
    digest_payload = dict(result)
    digest_payload.pop("internal_discovery_digest", None)
    result["internal_discovery_digest"] = _canonical_digest(digest_payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "internal-dimension-discovery.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(overlay, (left, top), (right, bottom), (140, 140, 140), 3)
    candidate_ids = {str(item.get("candidate_id")) for item in candidates}
    for cluster in clusters:
        role = str((cluster.get("semantic_role") or {}).get("role") or "UNRESOLVED")
        bbox = [int(round(float(value))) for value in (cluster.get("representative") or {}).get("bbox_px", [])]
        if len(bbox) != 4:
            continue
        color = (0, 170, 0) if role == "LINEAR_DIMENSION" else ((0, 150, 230) if role == "SECTION_MEASURE" else (180, 100, 0))
        cv2.rectangle(overlay, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
        if role == "LINEAR_DIMENSION":
            relation = (cluster.get("semantic_role") or {}).get("dimension_relation") or {}
            a = relation.get("endpoint_a_px")
            b = relation.get("endpoint_b_px")
            if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
                cv2.line(overlay, (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1]))), color, 2)
    overlay_path = output_dir / "internal-dimension-search-overlay.png"
    if not cv2.imwrite(str(overlay_path), overlay):
        raise RuntimeError("CAL01_INTERNAL_OVERLAY_WRITE_FAILED")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--base-discovery", required=True)
    parser.add_argument("--perimeter-discovery", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_internal_dimension_discovery(
        image_path=Path(args.image),
        base_discovery_path=Path(args.base_discovery),
        perimeter_discovery_path=Path(args.perimeter_discovery),
        output_dir=Path(args.output_dir),
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "ocr_pass_count": result["ocr_pass_count"],
                "numeric_observation_count": result["numeric_observation_count"],
                "location_cluster_count": result["location_cluster_count"],
                "role_counts": result["role_counts"],
                "candidate_count": result["candidate_count"],
                "primary_anchor_count": result["primary_anchor_count"],
                "internal_discovery_digest": result["internal_discovery_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
