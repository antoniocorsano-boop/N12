from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Iterable

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_authority(authority: dict[str, Any]) -> dict[str, Any]:
    if not authority:
        raise ValueError("CAL01_INTERVAL_OCR_AUTHORITY_MISSING")
    for key, value in authority.items():
        if key.endswith("_authorized") and value is not False:
            raise ValueError("CAL01_INTERVAL_OCR_AUTHORITY_ESCALATION")
    if authority.get("engineering_authority_effect", "NONE") != "NONE":
        raise ValueError("CAL01_INTERVAL_OCR_AUTHORITY_ESCALATION")
    return dict(authority)


def _review_request_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    requests = [dict(row) for row in manifest.get("review_requests", [])]
    request_by_id: dict[str, dict[str, Any]] = {}
    for request in requests:
        review_id = str(request.get("review_id") or "")
        crop_sha256 = str(request.get("crop_sha256") or "")
        if not review_id or review_id in request_by_id:
            raise ValueError("CAL01_INTERVAL_OCR_REVIEW_ID_INVALID")
        if not crop_sha256.startswith("sha256:"):
            raise ValueError("CAL01_INTERVAL_OCR_CROP_DIGEST_INVALID")
        request_by_id[review_id] = request
    if int(manifest.get("review_request_count", len(requests))) != len(requests):
        raise ValueError("CAL01_INTERVAL_OCR_REVIEW_COUNT_DRIFT")
    return request_by_id


def import_trocr_observations(
    manifest: dict[str, Any],
    observations: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    request_by_id = _review_request_map(manifest)
    imported: list[dict[str, Any]] = []
    for raw in observations:
        row = dict(raw)
        if str(row.get("provider_id") or "").strip() != "TROCR":
            raise ValueError("CAL01_INTERVAL_OCR_EXTERNAL_PROVIDER_INVALID")
        review_id = str(row.get("review_id") or "").strip()
        request = request_by_id.get(review_id)
        if request is None:
            raise ValueError("CAL01_INTERVAL_OCR_REVIEW_ID_UNKNOWN")
        crop_sha256 = str(row.get("crop_sha256") or "").strip()
        if crop_sha256 != str(request["crop_sha256"]):
            raise ValueError("CAL01_INTERVAL_OCR_CROP_DIGEST_MISMATCH")
        model_id = str(row.get("model_id") or "").strip()
        if not model_id:
            raise ValueError("CAL01_INTERVAL_OCR_EXTERNAL_MODEL_ID_INVALID")
        imported_row = {
            "review_id": review_id,
            "crop_sha256": crop_sha256,
            "provider_id": "TROCR",
            "family_id": f"TROCR:{model_id}",
            "model_id": model_id,
            "raw_text": str(row.get("raw_text") or "").strip(),
            "confidence": row.get("confidence"),
        }
        if row.get("provider_version") is not None:
            imported_row["provider_version"] = str(row.get("provider_version"))
        imported.append(imported_row)
    return sorted(
        imported,
        key=lambda row: (
            str(row["review_id"]),
            str(row["family_id"]),
            str(row["raw_text"]),
        ),
    )


def _normalize_observation(
    observation: dict[str, Any],
    *,
    expected_crop_sha256: str,
) -> dict[str, Any]:
    crop_sha256 = str(observation.get("crop_sha256") or "")
    if crop_sha256 != expected_crop_sha256:
        raise ValueError("CAL01_INTERVAL_OCR_CROP_DIGEST_MISMATCH")

    provider_id = str(observation.get("provider_id") or "").strip()
    family_id = str(observation.get("family_id") or "").strip()
    model_id = str(observation.get("model_id") or "").strip()
    if not provider_id or not family_id or not model_id:
        raise ValueError("CAL01_INTERVAL_OCR_PROVIDER_METADATA_INVALID")

    raw_text = str(observation.get("raw_text") or "").strip()
    confidence_value = observation.get("confidence")
    confidence: float | None
    if confidence_value is None:
        confidence = None
    else:
        confidence = float(confidence_value)
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("CAL01_INTERVAL_OCR_CONFIDENCE_INVALID")

    normalized = normalize_dimension_text(raw_text)
    normalized_text: str | None = None
    metric_value_m: float | None = None
    if normalized is not None:
        normalized_text, metric_value_m = normalized

    row = {
        "provider_id": provider_id,
        "family_id": family_id,
        "model_id": model_id,
        "raw_text": raw_text,
        "confidence": confidence,
        "normalized_text": normalized_text,
        "metric_value_m": metric_value_m,
        "crop_sha256": crop_sha256,
    }
    if observation.get("provider_version") is not None:
        row["provider_version"] = str(observation.get("provider_version"))
    return row


def _comparison_status(rows: list[dict[str, Any]]) -> tuple[str, str | None, int, list[str]]:
    by_family: dict[tuple[str, str], set[str]] = defaultdict(set)
    normalized_texts: set[str] = set()
    for row in rows:
        normalized = row.get("normalized_text")
        if not normalized:
            continue
        text = str(normalized)
        normalized_texts.add(text)
        by_family[(str(row["provider_id"]), str(row["family_id"]))].add(text)

    family_votes = [next(iter(values)) for values in by_family.values() if len(values) == 1]
    distinct_family_count = len(by_family)
    sorted_texts = sorted(normalized_texts)

    if not sorted_texts:
        return "OCR_NO_PROPOSAL", None, 0, []
    if len(sorted_texts) > 1:
        return "OCR_COMPARATIVE_CONFLICT", None, distinct_family_count, sorted_texts
    if len(family_votes) < 2:
        return "OCR_COMPARATIVE_INSUFFICIENT", None, distinct_family_count, sorted_texts
    if len(set(family_votes)) == 1 and all(len(values) == 1 for values in by_family.values()):
        return "OCR_COMPARATIVE_AGREEMENT", family_votes[0], distinct_family_count, sorted_texts
    return "OCR_COMPARATIVE_CONFLICT", None, distinct_family_count, sorted_texts


def build_interval_ocr_comparison(
    manifest: dict[str, Any],
    observations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    source = dict(manifest.get("source") or {})
    if not source.get("source_id") or not source.get("sha256"):
        raise ValueError("CAL01_INTERVAL_OCR_SOURCE_INVALID")

    authority = _validate_authority(dict(manifest.get("authority") or {}))
    request_by_id = _review_request_map(manifest)

    observations_by_review: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_observation in observations:
        observation = dict(raw_observation)
        review_id = str(observation.get("review_id") or "")
        request = request_by_id.get(review_id)
        if request is None:
            raise ValueError("CAL01_INTERVAL_OCR_REVIEW_ID_UNKNOWN")
        normalized = _normalize_observation(
            observation,
            expected_crop_sha256=str(request["crop_sha256"]),
        )
        observations_by_review[review_id].append(normalized)

    review_rows: list[dict[str, Any]] = []
    for review_id in sorted(request_by_id):
        request = request_by_id[review_id]
        rows = sorted(
            observations_by_review.get(review_id, []),
            key=lambda row: (
                str(row["provider_id"]),
                str(row["family_id"]),
                str(row["raw_text"]),
                -1.0 if row["confidence"] is None else -float(row["confidence"]),
            ),
        )
        status, consensus, family_count, normalized_texts = _comparison_status(rows)
        review_rows.append(
            {
                "review_id": review_id,
                "crop_file": request.get("crop_file"),
                "crop_sha256": request["crop_sha256"],
                "observation_count": len(rows),
                "valid_numeric_observation_count": sum(
                    1 for row in rows if row.get("normalized_text") is not None
                ),
                "distinct_family_count": family_count,
                "normalized_texts": normalized_texts,
                "comparison_status": status,
                "consensus_normalized_text": consensus,
                "observations": rows,
                "human_review_required": True,
                "primary_anchor_authorized": False,
                "eligible_for_metric_calibration": False,
            }
        )

    result = {
        "schema": "CEW_CAL01_INTERVAL_OCR_COMPARISON_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "review_manifest_digest": manifest.get("review_digest"),
        "review_count": len(review_rows),
        "reviews": review_rows,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": authority,
    }
    result["comparison_digest"] = _canonical_digest(result)
    return result
