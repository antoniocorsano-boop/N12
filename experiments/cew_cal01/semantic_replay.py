from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Sequence

from experiments.cew_cal01.numeric_role import classify_numeric_graphic_role, expected_dimension_orientation
from experiments.cew_cal01.role_verification import select_ocr_consensus


def _canonical_numeric_text(value: Any) -> str:
    return str(value or "").strip().replace(" ", "").replace(",", ".")


def refine_numeric_proposal(
    proposal: dict[str, Any],
    *,
    local_readings: Iterable[Any],
    line_segments: Iterable[Sequence[float]],
    nearby_closed_frame: bool,
) -> dict[str, Any]:
    proposal_id = str(proposal.get("proposal_id") or "").strip()
    raw_text = str(proposal.get("raw_ocr_text") or "").strip()
    bbox = proposal.get("bbox_px")
    rotation = proposal.get("ocr_rotation_degrees")
    if not proposal_id:
        raise ValueError("CAL01_SEMANTIC_PROPOSAL_ID_REQUIRED")
    if not raw_text:
        raise ValueError("CAL01_SEMANTIC_RAW_TEXT_REQUIRED")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("CAL01_SEMANTIC_BBOX_REQUIRED")
    if rotation is None:
        raise ValueError("CAL01_SEMANTIC_ROTATION_REQUIRED")

    readings = list(local_readings)
    consensus = select_ocr_consensus(readings, minimum_count=3, minimum_margin=2)
    role = classify_numeric_graphic_role(
        raw_text=raw_text,
        consensus_text=consensus["text"],
        consensus_count=consensus["count"],
        ocr_rotation_degrees=int(rotation),
        token_bbox_px=bbox,
        line_segments=line_segments,
        nearby_closed_frame=bool(nearby_closed_frame),
    )
    return {
        "proposal_id": proposal_id,
        "raw_ocr_text": raw_text,
        "source_bbox_px": [float(value) for value in bbox],
        "ocr_rotation_degrees": int(rotation) % 360,
        "local_readings": [str(value) for value in readings],
        "consensus": consensus,
        **role,
        "primary_anchor_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "m0g_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def refine_location_cluster(
    cluster: dict[str, Any],
    *,
    line_segments: Iterable[Sequence[float]],
    nearby_closed_frame: bool,
) -> dict[str, Any]:
    readings = list(cluster.get("readings") or [])
    observations = [dict(item) for item in (cluster.get("observations") or [])]
    representative = dict(cluster.get("representative") or {})
    if not readings or not observations or not representative:
        raise ValueError("CAL01_SEMANTIC_CLUSTER_INCOMPLETE")

    consensus = select_ocr_consensus(readings, minimum_count=3, minimum_margin=2)
    if not consensus["confirmed"]:
        result = refine_numeric_proposal(
            representative,
            local_readings=readings,
            line_segments=line_segments,
            nearby_closed_frame=nearby_closed_frame,
        )
        result["consensus_orientation"] = None
        result["selected_proposal_id"] = representative.get("proposal_id")
        return result

    consensus_text = _canonical_numeric_text(consensus["text"])
    matching = [
        item for item in observations
        if _canonical_numeric_text(item.get("raw_ocr_text")) == consensus_text
    ]
    orientation_counts = Counter(
        expected_dimension_orientation(int(item.get("ocr_rotation_degrees", 0)))
        for item in matching
    )
    ranked = sorted(orientation_counts.items(), key=lambda item: (-item[1], item[0]))
    top_count = ranked[0][1] if ranked else 0
    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    if not ranked or top_count < 2 or top_count == runner_up:
        return {
            "proposal_id": str(representative.get("proposal_id") or ""),
            "selected_proposal_id": None,
            "raw_ocr_text": str(representative.get("raw_ocr_text") or ""),
            "source_bbox_px": [float(value) for value in representative.get("bbox_px", [])],
            "ocr_rotation_degrees": int(representative.get("ocr_rotation_degrees", 0)) % 360,
            "local_readings": [str(value) for value in readings],
            "consensus": consensus,
            "consensus_orientation": None,
            "role": "UNRESOLVED",
            "reason": "OCR_ORIENTATION_CONSENSUS_INSUFFICIENT",
            "documented_text": consensus["text"],
            "metric_value_m": None,
            "dimension_relation": None,
            "primary_anchor_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        }

    consensus_orientation = ranked[0][0]
    eligible = [
        item for item in matching
        if expected_dimension_orientation(int(item.get("ocr_rotation_degrees", 0))) == consensus_orientation
    ]
    selected = max(
        eligible,
        key=lambda item: (
            float(item.get("ocr_confidence", 0.0)),
            str(item.get("proposal_id") or ""),
        ),
    )
    result = refine_numeric_proposal(
        selected,
        local_readings=readings,
        line_segments=line_segments,
        nearby_closed_frame=nearby_closed_frame,
    )
    result["consensus_orientation"] = consensus_orientation
    result["selected_proposal_id"] = selected.get("proposal_id")
    return result
