from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable

from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED


SIDE_ORDER = ["TOP", "RIGHT", "BOTTOM", "LEFT"]
_OUTWARD_NORMAL = {
    "TOP": "NEGATIVE_Y",
    "RIGHT": "POSITIVE_X",
    "BOTTOM": "POSITIVE_Y",
    "LEFT": "NEGATIVE_X",
}


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _source(refined: dict[str, Any]) -> dict[str, str]:
    source = dict(refined.get("source") or {})
    source_id = str(source.get("source_id") or "")
    sha256 = str(source.get("sha256") or "")
    if not source_id or len(sha256) != 64:
        raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_SOURCE_INVALID")
    return {"source_id": source_id, "sha256": sha256}


def _sorted_sides(refined: dict[str, Any]) -> list[dict[str, Any]]:
    side_rows = [dict(row) for row in refined.get("sides", [])]
    by_side: dict[str, dict[str, Any]] = {}
    for row in side_rows:
        side = str(row.get("side") or "").upper()
        if side not in SIDE_ORDER or side in by_side:
            raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_SIDE_INVALID")
        by_side[side] = row
    if set(by_side) != set(SIDE_ORDER):
        raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_SIDE_SET_INVALID")
    return [by_side[side] for side in SIDE_ORDER]


def _request_rows(refined: dict[str, Any], source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for side_row in _sorted_sides(refined):
        side = str(side_row["side"]).upper()
        chains = sorted(
            [dict(row) for row in side_row.get("chains", [])],
            key=lambda row: str(row.get("chain_id") or ""),
        )
        for chain in chains:
            chain_id = str(chain.get("chain_id") or "")
            orientation = str(chain.get("orientation") or "")
            if not chain_id or orientation not in {"HORIZONTAL", "VERTICAL"}:
                raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_CHAIN_INVALID")
            carrier_axis = float(chain.get("carrier_axis_px"))
            intervals = sorted(
                [dict(row) for row in chain.get("intervals", [])],
                key=lambda row: int(row.get("interval_index", -1)),
            )
            seen_interval_indexes: set[int] = set()
            for interval in intervals:
                interval_index = int(interval.get("interval_index", -1))
                if interval_index < 0 or interval_index in seen_interval_indexes:
                    raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_INTERVAL_INDEX_INVALID")
                seen_interval_indexes.add(interval_index)
                start_px = float(interval.get("start_px"))
                end_px = float(interval.get("end_px"))
                if end_px <= start_px:
                    raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_INTERVAL_SPAN_INVALID")
                rows.append(
                    {
                        "review_id": f"{source_id}:{side}:{chain_id}:I{interval_index}",
                        "side": side,
                        "chain_id": chain_id,
                        "interval_index": interval_index,
                        "orientation": orientation,
                        "carrier_axis_px": carrier_axis,
                        "interval_start_px": start_px,
                        "interval_end_px": end_px,
                        "crop_policy": {
                            "outward_normal": _OUTWARD_NORMAL[side],
                            "carrier_realign_radius_px": 48,
                            "longitudinal_inset_px": 15,
                            "outward_depth_px": 220,
                            "inward_guard_px": 40,
                            "review_rotation_degrees": 0 if orientation == "HORIZONTAL" else 90,
                            "carrier_realign_changes_governed_geometry": False,
                        },
                        "recognition_status": "HANDWRITTEN_RECOGNIZER_REQUIRED",
                        "recognition_provider": None,
                        "text_proposals": [],
                        "primary_anchor_authorized": False,
                        "eligible_for_metric_calibration": False,
                    }
                )
    return rows


def _refresh_digest(manifest: dict[str, Any]) -> None:
    payload = {key: value for key, value in manifest.items() if key != "review_digest"}
    manifest["review_digest"] = _canonical_digest(payload)


def build_interval_text_review_manifest(refined: dict[str, Any]) -> dict[str, Any]:
    source = _source(refined)
    rows = _request_rows(refined, source["source_id"])
    manifest: dict[str, Any] = {
        "schema": "CEW_CAL01_INTERVAL_TEXT_REVIEW_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "side_order": list(SIDE_ORDER),
        "review_request_count": len(rows),
        "review_requests": rows,
        "recognizer_binding_status": "HANDWRITTEN_RECOGNIZER_NOT_BOUND",
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    _refresh_digest(manifest)
    return manifest


def _proposal_rows(alternatives: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for alternative in alternatives:
        row = dict(alternative)
        raw_text = str(row.get("raw_text") or "").strip()
        if not raw_text:
            continue
        confidence = float(row.get("confidence", 0.0))
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_CONFIDENCE_INVALID")
        proposals.append({"raw_text": raw_text, "confidence": confidence})
    proposals.sort(key=lambda row: (-float(row["confidence"]), str(row["raw_text"])))
    return proposals


def attach_text_proposal(
    manifest: dict[str, Any],
    *,
    review_id: str,
    provider: dict[str, Any],
    alternatives: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    updated = copy.deepcopy(manifest)
    provider_id = str(provider.get("provider_id") or "")
    model_id = str(provider.get("model_id") or "")
    if not provider_id or not model_id:
        raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_PROVIDER_INVALID")

    matching = [row for row in updated.get("review_requests", []) if str(row.get("review_id")) == review_id]
    if len(matching) != 1:
        raise ValueError("CAL01_INTERVAL_TEXT_REVIEW_ID_NOT_UNIQUE")

    proposals = _proposal_rows(alternatives)
    row = matching[0]
    row["recognition_provider"] = {"provider_id": provider_id, "model_id": model_id}
    row["text_proposals"] = proposals
    row["recognition_status"] = "OCR_PROPOSAL_ONLY" if proposals else "MANUAL_OR_MULTIMODAL_REVIEW_REQUIRED"
    row["primary_anchor_authorized"] = False
    row["eligible_for_metric_calibration"] = False

    updated["primary_anchor_count"] = 0
    updated["eligible_for_metric_calibration"] = False
    updated["authority"] = dict(AUTHORITY_CLOSED)
    _refresh_digest(updated)
    return updated
