from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


_TIGHT_PREPROCESS_MODES = ("RAW_GRAYSCALE", "LINE_SUPPRESSED", "BINARY_OTSU")
_TIGHT_PSMS = (6, 7, 13)


def _canonical_numeric_text(value: Any) -> str:
    return str(value or "").strip().replace(" ", "").replace(",", ".")


def build_tight_confirmation_plan(
    cluster: dict[str, Any],
    *,
    page_width: int,
    page_height: int,
) -> list[dict[str, Any]]:
    """Build bounded OCR passes around one already observed source location.

    This stage never searches for new page locations. It only re-reads the
    numeric token already present in the oriented discovery inventory.
    """

    if page_width <= 0 or page_height <= 0:
        raise ValueError("CAL01_TIGHT_PAGE_FRAME_INVALID")
    representative = cluster.get("representative") or {}
    bbox = representative.get("bbox_px")
    rotation = representative.get("ocr_rotation_degrees")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("CAL01_TIGHT_TARGET_BBOX_REQUIRED")
    if rotation is None:
        raise ValueError("CAL01_TIGHT_ROTATION_REQUIRED")
    rotation = int(rotation) % 360
    if rotation not in {0, 90, 180, 270}:
        raise ValueError("CAL01_TIGHT_ROTATION_INVALID")

    left, top, right, bottom = (float(value) for value in bbox)
    if left < 0 or top < 0 or right <= left or bottom <= top or right > page_width or bottom > page_height:
        raise ValueError("CAL01_TIGHT_TARGET_BBOX_INVALID")

    width = right - left
    height = bottom - top
    pad_x = max(16.0, width * 0.85)
    pad_y = max(16.0, height * 0.55)
    crop = [
        max(0.0, left - pad_x),
        max(0.0, top - pad_y),
        min(float(page_width), right + pad_x),
        min(float(page_height), bottom + pad_y),
    ]

    plan: list[dict[str, Any]] = []
    for preprocess_mode in _TIGHT_PREPROCESS_MODES:
        for psm in _TIGHT_PSMS:
            plan.append(
                {
                    "scope": "TIGHT_LOCAL_SAME_SOURCE_LOCATION",
                    "target_bbox_px": [left, top, right, bottom],
                    "crop_bbox_px": list(crop),
                    "rotation_degrees": rotation,
                    "preprocess_mode": preprocess_mode,
                    "psm": psm,
                    "ocr_scale": 3.0,
                }
            )
    return plan


def select_diverse_tight_consensus(
    observations: Iterable[dict[str, Any]],
    *,
    minimum_families: int = 3,
    minimum_margin: int = 1,
) -> dict[str, Any]:
    """Select OCR consensus using independent preprocessing/PSM families.

    Repeated observations from the same family count once. A family that emits
    conflicting texts is ignored rather than being allowed to vote twice.
    """

    if minimum_families < 1 or minimum_margin < 1:
        raise ValueError("CAL01_TIGHT_CONSENSUS_POLICY_INVALID")

    family_texts: dict[tuple[str, int], set[str]] = defaultdict(set)
    observation_count = 0
    for observation in observations:
        observation_count += 1
        text = _canonical_numeric_text(observation.get("text"))
        if not text:
            continue
        mode = str(observation.get("preprocess_mode") or "").strip()
        try:
            psm = int(observation.get("psm"))
        except (TypeError, ValueError):
            continue
        if not mode:
            continue
        family_texts[(mode, psm)].add(text)

    family_votes: dict[tuple[str, int], str] = {
        family: next(iter(texts))
        for family, texts in family_texts.items()
        if len(texts) == 1
    }
    counts = Counter(family_votes.values())
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    top_text = ranked[0][0] if ranked else None
    top_count = ranked[0][1] if ranked else 0
    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    confirmed = (
        top_text is not None
        and top_count >= minimum_families
        and top_count > runner_up
        and top_count - runner_up >= minimum_margin
    )

    return {
        "confirmed": confirmed,
        "text": top_text if confirmed else None,
        "family_count": top_count,
        "runner_up_family_count": runner_up,
        "eligible_family_count": len(family_votes),
        "ambiguous_family_count": sum(1 for texts in family_texts.values() if len(texts) > 1),
        "observation_count": observation_count,
        "reason": "TIGHT_OCR_DIVERSE_CONSENSUS_CONFIRMED" if confirmed else "TIGHT_OCR_DIVERSE_CONSENSUS_INSUFFICIENT",
    }
