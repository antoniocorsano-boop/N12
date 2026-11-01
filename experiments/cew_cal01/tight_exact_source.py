from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Iterable, Mapping

from experiments.cew_cal01.exact_source import SOURCE_SHA256


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "primary_anchor_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_tight_replay_manifest(
    *,
    source: Mapping[str, Any],
    rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Freeze tight-local OCR replay evidence without creating metric authority."""

    source_sha = str(source.get("sha256") or "").strip()
    if source_sha != SOURCE_SHA256:
        raise ValueError("CAL01_TIGHT_SOURCE_DIGEST_DRIFT")
    page_index = source.get("page_index")
    if isinstance(page_index, bool) or int(page_index) != 0:
        raise ValueError("CAL01_TIGHT_SOURCE_PAGE_DRIFT")

    ordered: list[dict[str, Any]] = []
    seen_indices: set[int] = set()
    for raw in rows:
        row = dict(raw)
        try:
            index = int(row["cluster_index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("CAL01_TIGHT_CLUSTER_INDEX_REQUIRED") from exc
        if index < 0 or index in seen_indices:
            raise ValueError("CAL01_TIGHT_CLUSTER_INDEX_INVALID")
        seen_indices.add(index)
        row["cluster_index"] = index

        bbox = row.get("target_bbox_px")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("CAL01_TIGHT_TARGET_BBOX_REQUIRED")
        left, top, right, bottom = (float(value) for value in bbox)
        if left < 0 or top < 0 or right <= left or bottom <= top:
            raise ValueError("CAL01_TIGHT_TARGET_BBOX_INVALID")
        row["target_bbox_px"] = [left, top, right, bottom]

        rotation = int(row.get("ocr_rotation_degrees")) % 360
        if rotation not in {0, 90, 180, 270}:
            raise ValueError("CAL01_TIGHT_ROTATION_INVALID")
        row["ocr_rotation_degrees"] = rotation

        pass_count = int(row.get("pass_count", 0))
        observation_count = int(row.get("observation_count", 0))
        if pass_count < 0 or observation_count < 0 or observation_count > pass_count:
            raise ValueError("CAL01_TIGHT_REPLAY_COUNTS_INVALID")
        row["pass_count"] = pass_count
        row["observation_count"] = observation_count

        consensus = row.get("consensus")
        if not isinstance(consensus, dict) or not isinstance(consensus.get("confirmed"), bool):
            raise ValueError("CAL01_TIGHT_CONSENSUS_REQUIRED")
        if consensus["confirmed"] and not str(consensus.get("text") or "").strip():
            raise ValueError("CAL01_TIGHT_CONFIRMED_TEXT_REQUIRED")

        row["primary_anchor_authorized"] = False
        row["canonical_geometry_authorized"] = False
        row["canonical_write_authorized"] = False
        row["engineering_authority_effect"] = "NONE"
        ordered.append(row)

    ordered.sort(key=lambda item: item["cluster_index"])
    confirmed_texts = [
        str(row["consensus"]["text"])
        for row in ordered
        if row["consensus"].get("confirmed") is True
    ]
    confirmed_counts = dict(sorted(Counter(confirmed_texts).items()))

    result = {
        "schema": "CEW_CAL01_TIGHT_EXACT_SOURCE_REPLAY_v1",
        "program": "CEW-CAL-01",
        "source": {
            "sha256": SOURCE_SHA256,
            "page_index": 0,
        },
        "cluster_count": len(ordered),
        "tight_consensus_confirmed_count": len(confirmed_texts),
        "confirmed_text_counts": confirmed_counts,
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "rows": ordered,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["tight_replay_digest"] = _canonical_digest(result)
    return result
