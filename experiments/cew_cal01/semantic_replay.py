from __future__ import annotations

from typing import Any, Iterable, Sequence

from experiments.cew_cal01.numeric_role import classify_numeric_graphic_role
from experiments.cew_cal01.role_verification import select_ocr_consensus


def refine_numeric_proposal(
    proposal: dict[str, Any],
    *,
    local_readings: Iterable[Any],
    line_segments: Iterable[Sequence[float]],
    nearby_closed_frame: bool,
) -> dict[str, Any]:
    """Refine one oriented OCR proposal using repeated local readings and graphic role.

    This stage can classify document role, but it cannot create a primary metric
    anchor, metric coordinate, canonical geometry, or engineering authority.
    """

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
    consensus = select_ocr_consensus(
        readings,
        minimum_count=3,
        minimum_margin=2,
    )
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
