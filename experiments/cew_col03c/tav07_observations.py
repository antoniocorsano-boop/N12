from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalized_bbox(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError("TAV.7 observation bbox missing")
    try:
        box = {key: float(value[key]) for key in ("x", "y", "width", "height")}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("TAV.7 observation bbox invalid") from exc
    if (
        box["x"] < 0.0
        or box["y"] < 0.0
        or box["width"] <= 0.0
        or box["height"] <= 0.0
        or box["x"] + box["width"] > 1.000001
        or box["y"] + box["height"] > 1.000001
    ):
        raise ValueError("TAV.7 observation bbox outside normalized page")
    return {key: round(box[key], 8) for key in ("x", "y", "width", "height")}


def _validate_source_metadata(source_metadata: dict[str, Any]) -> None:
    if not isinstance(source_metadata, dict):
        raise ValueError("TAV.7 source metadata missing")
    required = ("catalogue_id", "archive_commit", "source_path", "sha256", "page_count")
    if any(not source_metadata.get(key) for key in required):
        raise ValueError("TAV.7 source metadata incomplete")
    if source_metadata.get("materialization_state") != "MATERIALIZED_VERIFIED":
        raise ValueError("TAV.7 source is not materialized and verified")
    if int(source_metadata["page_count"]) <= 0:
        raise ValueError("TAV.7 source page count invalid")


def normalize_tav07_text_observations(
    raw_observations: list[dict[str, Any]],
    *,
    source_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    _validate_source_metadata(source_metadata)
    if not isinstance(raw_observations, list):
        raise ValueError("TAV.7 raw observations must be a list")

    seeds: list[dict[str, Any]] = []
    page_count = int(source_metadata["page_count"])
    for raw in raw_observations:
        if not isinstance(raw, dict):
            raise ValueError("TAV.7 raw observation must be a mapping")
        normalized_text = _normalize_text(raw.get("raw_text"))
        if not normalized_text:
            continue
        try:
            page_index = int(raw.get("page_index"))
        except (TypeError, ValueError) as exc:
            raise ValueError("TAV.7 observation page invalid") from exc
        if page_index < 0 or page_index >= page_count:
            raise ValueError("TAV.7 observation page outside source")
        box = _normalized_bbox(raw.get("bbox"))
        seed: dict[str, Any] = {
            "source_catalogue_id": str(source_metadata["catalogue_id"]),
            "archive_commit": str(source_metadata["archive_commit"]),
            "source_path": str(source_metadata["source_path"]),
            "source_sha256": str(source_metadata["sha256"]),
            "page_index": page_index,
            "bbox": box,
            "raw_text": str(raw.get("raw_text") or ""),
            "normalized_text": normalized_text,
            "confidence": raw.get("confidence"),
            "binding_state": "UNBOUND",
            "identity_promotion_authorized": False,
        }
        seeds.append(seed)

    seeds.sort(
        key=lambda row: (
            row["page_index"],
            row["bbox"]["y"],
            row["bbox"]["x"],
            row["bbox"]["height"],
            row["bbox"]["width"],
            row["normalized_text"],
            row["raw_text"],
            str(row.get("confidence")),
        )
    )

    occurrence_by_fingerprint: dict[str, int] = {}
    normalized: list[dict[str, Any]] = []
    for seed in seeds:
        fingerprint_payload = {
            "source_catalogue_id": seed["source_catalogue_id"],
            "archive_commit": seed["archive_commit"],
            "source_sha256": seed["source_sha256"],
            "page_index": seed["page_index"],
            "bbox": seed["bbox"],
            "raw_text": seed["raw_text"],
            "normalized_text": seed["normalized_text"],
            "confidence": seed.get("confidence"),
        }
        fingerprint = hashlib.sha256(_canonical_bytes(fingerprint_payload)).hexdigest()
        duplicate_index = occurrence_by_fingerprint.get(fingerprint, 0) + 1
        occurrence_by_fingerprint[fingerprint] = duplicate_index
        row = deepcopy(seed)
        row["observation_id"] = f"TAV07-OBS-{fingerprint[:16].upper()}-{duplicate_index:02d}"
        row["provenance_ref"] = (
            f"{row['archive_commit']}:{row['source_path']}:page={row['page_index']}:"
            f"bbox={row['bbox']['x']},{row['bbox']['y']},{row['bbox']['width']},{row['bbox']['height']}"
        )
        normalized.append(row)
    return normalized


def build_tav07_observation_inventory(
    observations: list[dict[str, Any]],
    *,
    extraction_method: str,
    extraction_version: str,
) -> dict[str, Any]:
    if not isinstance(observations, list):
        raise ValueError("TAV.7 observations must be a list")
    if not extraction_method or not extraction_version:
        raise ValueError("TAV.7 extractor provenance missing")
    ordered = sorted((deepcopy(row) for row in observations), key=lambda row: str(row.get("observation_id") or ""))
    if len({str(row.get("observation_id") or "") for row in ordered}) != len(ordered):
        raise ValueError("TAV.7 observation ID collision")
    if any(row.get("binding_state") != "UNBOUND" or row.get("identity_promotion_authorized") is not False for row in ordered):
        raise ValueError("TAV.7 observation authority drift")
    return {
        "observation_state": "MACHINE_OBSERVATIONS_PRESENT" if ordered else "NO_MACHINE_TEXT_OBSERVED",
        "observation_count": len(ordered),
        "extraction_method": extraction_method,
        "extraction_version": extraction_version,
        "observations": ordered,
        "observation_digest": hashlib.sha256(_canonical_bytes(ordered)).hexdigest(),
        "identity_promotion_authorized": False,
    }
