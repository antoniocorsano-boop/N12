from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED_REVIEWER_ROLE = "HUMAN_PROFESSIONAL_USER"
REQUIRED_METRIC_RELATION_STATE = "PRIMARY_VISUAL_VALIDATED"
REQUIRED_CALIBRATION_ROLE = "LINEAR_DIMENSION"


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _closed_authority(authority: dict[str, Any]) -> dict[str, Any]:
    result = dict(authority)
    if not result:
        raise ValueError("CAL01_HUMAN_REVIEW_AUTHORITY_MISSING")
    for key, value in result.items():
        if key.endswith("_authorized") and value is not False:
            raise ValueError("CAL01_HUMAN_REVIEW_AUTHORITY_ESCALATION")
    if result.get("engineering_authority_effect", "NONE") != "NONE":
        raise ValueError("CAL01_HUMAN_REVIEW_AUTHORITY_ESCALATION")
    return result


def normalize_source_bbox_ccw(
    bbox_source_px: list[float] | tuple[float, float, float, float],
    *,
    source_width_px: float,
) -> list[float]:
    if len(bbox_source_px) != 4:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_BBOX_INVALID")
    x1, y1, x2, y2 = (float(value) for value in bbox_source_px)
    width = float(source_width_px)
    if width <= 0 or x2 < x1 or y2 < y1:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_BBOX_INVALID")
    return [y1, width - x2, y2, width - x1]


def _bbox_center(bbox: list[float] | tuple[float, float, float, float]) -> tuple[float, float]:
    x1, y1, x2, y2 = (float(value) for value in bbox)
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _point_inside_bbox(point: tuple[float, float], bbox: list[float]) -> bool:
    x, y = point
    x1, y1, x2, y2 = (float(value) for value in bbox)
    return x1 <= x <= x2 and y1 <= y <= y2


def _source_bbox(receipt: dict[str, Any]) -> list[float] | None:
    value = receipt.get("source_bbox_px")
    if value is None:
        value = receipt.get("source_bbox_union_px")
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_BBOX_INVALID")
    return [float(item) for item in value]


def _is_reusable_human_receipt(receipt: dict[str, Any]) -> bool:
    return (
        receipt.get("reviewer_role") == REQUIRED_REVIEWER_ROLE
        and receipt.get("metric_relation_state") == REQUIRED_METRIC_RELATION_STATE
        and receipt.get("calibration_role") == REQUIRED_CALIBRATION_ROLE
        and receipt.get("eligible_for_metric_relation_network") is True
        and receipt.get("eligible_for_metric_calibration") is False
        and receipt.get("primary_anchor_authorized") is False
    )


def _receipt_value_m(receipt: dict[str, Any]) -> float:
    value = receipt.get("value")
    if not isinstance(value, dict) or value.get("length_m") is None:
        raise ValueError("CAL01_HUMAN_RECEIPT_LINEAR_VALUE_MISSING")
    result = float(value["length_m"])
    if result <= 0:
        raise ValueError("CAL01_HUMAN_RECEIPT_LINEAR_VALUE_INVALID")
    return result


def reconcile_human_receipts(
    manifest: dict[str, Any],
    receipts: Iterable[dict[str, Any]],
    *,
    source_width_px: float,
) -> dict[str, Any]:
    source = dict(manifest.get("source") or {})
    source_id = str(source.get("source_id") or "")
    source_sha = str(source.get("sha256") or "")
    if not source_id or not source_sha:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_INVALID")

    requests = [dict(row) for row in manifest.get("review_requests", [])]
    if int(manifest.get("review_request_count", len(requests))) != len(requests):
        raise ValueError("CAL01_HUMAN_RECEIPT_REVIEW_COUNT_DRIFT")

    request_by_id: dict[str, dict[str, Any]] = {}
    for row in requests:
        review_id = str(row.get("review_id") or "")
        bbox = row.get("crop_bbox_normalized_px")
        if not review_id or review_id in request_by_id:
            raise ValueError("CAL01_HUMAN_RECEIPT_REVIEW_ID_INVALID")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError("CAL01_HUMAN_RECEIPT_INTERVAL_BBOX_INVALID")
        request_by_id[review_id] = row

    bindings: dict[str, dict[str, Any]] = {}
    unmatched: list[str] = []
    ineligible: list[str] = []
    source_mismatch: list[str] = []
    candidate_bindings: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for raw in receipts:
        receipt = dict(raw)
        receipt_id = str(receipt.get("review_id") or "")
        if not receipt_id:
            raise ValueError("CAL01_HUMAN_RECEIPT_REVIEW_ID_MISSING")

        if not _is_reusable_human_receipt(receipt):
            ineligible.append(receipt_id)
            continue

        if receipt.get("source_document") != source_id or receipt.get("source_sha256") != source_sha:
            source_mismatch.append(receipt_id)
            continue

        source_bbox = _source_bbox(receipt)
        if source_bbox is None:
            ineligible.append(receipt_id)
            continue
        normalized_bbox = normalize_source_bbox_ccw(source_bbox, source_width_px=source_width_px)
        center = _bbox_center(normalized_bbox)
        matched_review_ids = sorted(
            review_id
            for review_id, request in request_by_id.items()
            if _point_inside_bbox(center, request["crop_bbox_normalized_px"])
        )
        if not matched_review_ids:
            unmatched.append(receipt_id)
            continue
        if len(matched_review_ids) != 1:
            raise ValueError("CAL01_HUMAN_RECEIPT_INTERVAL_AMBIGUOUS")

        interval_review_id = matched_review_ids[0]
        candidate_bindings[interval_review_id].append(
            {
                "receipt_review_id": receipt_id,
                "source_bbox_px": source_bbox,
                "normalized_bbox_px": normalized_bbox,
                "value_m": _receipt_value_m(receipt),
                "human_reading": receipt.get("human_reading"),
                "metric_relation_state": receipt.get("metric_relation_state"),
                "metric_source_kind": receipt.get("metric_source_kind"),
                "qualified_discovery_basis": receipt.get("qualified_discovery_basis"),
                "eligible_for_metric_calibration": False,
                "primary_anchor_authorized": False,
            }
        )

    for interval_review_id, rows in sorted(candidate_bindings.items()):
        values = {float(row["value_m"]) for row in rows}
        if len(values) > 1:
            raise ValueError("CAL01_HUMAN_RECEIPT_VALUE_CONFLICT")
        bindings[interval_review_id] = sorted(
            rows,
            key=lambda row: str(row["receipt_review_id"]),
        )[0]

    return {
        "source": source,
        "reused_count": len(bindings),
        "bindings": bindings,
        "unmatched_receipt_ids": sorted(unmatched),
        "ineligible_receipt_ids": sorted(ineligible),
        "source_mismatch_receipt_ids": sorted(source_mismatch),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
    }


def build_human_review_packet(
    manifest: dict[str, Any],
    comparison: dict[str, Any],
    receipts: Iterable[dict[str, Any]],
    *,
    source_width_px: float,
) -> dict[str, Any]:
    source = dict(manifest.get("source") or {})
    comparison_source = dict(comparison.get("source") or {})
    if source != comparison_source:
        raise ValueError("CAL01_HUMAN_REVIEW_SOURCE_DRIFT")
    if comparison.get("review_manifest_digest") != manifest.get("review_digest"):
        raise ValueError("CAL01_HUMAN_REVIEW_MANIFEST_DIGEST_DRIFT")

    authority = _closed_authority(dict(manifest.get("authority") or {}))
    _closed_authority(dict(comparison.get("authority") or {}))

    requests = [dict(row) for row in manifest.get("review_requests", [])]
    comparison_rows = [dict(row) for row in comparison.get("reviews", [])]
    if int(manifest.get("review_request_count", len(requests))) != len(requests):
        raise ValueError("CAL01_HUMAN_REVIEW_REVIEW_COUNT_DRIFT")
    if int(comparison.get("review_count", len(comparison_rows))) != len(comparison_rows):
        raise ValueError("CAL01_HUMAN_REVIEW_COMPARISON_COUNT_DRIFT")
    if len(requests) != len(comparison_rows):
        raise ValueError("CAL01_HUMAN_REVIEW_COMPARISON_COUNT_DRIFT")

    request_by_id: dict[str, dict[str, Any]] = {}
    for request in requests:
        review_id = str(request.get("review_id") or "")
        if not review_id or review_id in request_by_id:
            raise ValueError("CAL01_HUMAN_REVIEW_REVIEW_ID_INVALID")
        request_by_id[review_id] = request

    comparison_by_id: dict[str, dict[str, Any]] = {}
    for row in comparison_rows:
        review_id = str(row.get("review_id") or "")
        if not review_id or review_id in comparison_by_id:
            raise ValueError("CAL01_HUMAN_REVIEW_COMPARISON_ID_INVALID")
        comparison_by_id[review_id] = row

    if set(request_by_id) != set(comparison_by_id):
        raise ValueError("CAL01_HUMAN_REVIEW_COMPARISON_ID_DRIFT")

    reconciliation = reconcile_human_receipts(
        manifest,
        receipts,
        source_width_px=source_width_px,
    )

    reviews: list[dict[str, Any]] = []
    for review_id in sorted(request_by_id):
        request = request_by_id[review_id]
        ocr = comparison_by_id[review_id]
        if (
            ocr.get("crop_sha256") != request.get("crop_sha256")
            or ocr.get("crop_file") != request.get("crop_file")
        ):
            raise ValueError("CAL01_HUMAN_REVIEW_CROP_BINDING_DRIFT")

        binding = reconciliation["bindings"].get(review_id)
        if binding is None:
            review_state = "PENDING_HUMAN_REVIEW"
            validated_value_m = None
            human_receipt_ref = None
            existing_human_reading = None
        else:
            review_state = "REUSED_HUMAN_RECEIPT"
            validated_value_m = float(binding["value_m"])
            human_receipt_ref = str(binding["receipt_review_id"])
            existing_human_reading = binding.get("human_reading")

        reviews.append(
            {
                "review_id": review_id,
                "side": request.get("side"),
                "chain_id": request.get("chain_id"),
                "interval_index": request.get("interval_index"),
                "crop_file": request.get("crop_file"),
                "crop_sha256": request.get("crop_sha256"),
                "crop_bbox_normalized_px": request.get("crop_bbox_normalized_px"),
                "ocr_comparison_status": ocr.get("comparison_status"),
                "ocr_normalized_texts": list(ocr.get("normalized_texts") or []),
                "ocr_observations": list(ocr.get("observations") or []),
                "review_state": review_state,
                "validated_value_m": validated_value_m,
                "human_receipt_ref": human_receipt_ref,
                "existing_human_reading": existing_human_reading,
                "human_decision_required": binding is None,
                "eligible_for_metric_calibration": False,
                "primary_anchor_authorized": False,
            }
        )

    packet = {
        "schema": "CEW_CAL01_EXTERNAL_CHAIN_HUMAN_REVIEW_PACKET_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "review_manifest_digest": manifest.get("review_digest"),
        "ocr_comparison_digest": comparison.get("comparison_digest"),
        "review_count": len(reviews),
        "reused_human_receipt_count": sum(
            1 for row in reviews if row["review_state"] == "REUSED_HUMAN_RECEIPT"
        ),
        "pending_human_review_count": sum(
            1 for row in reviews if row["review_state"] == "PENDING_HUMAN_REVIEW"
        ),
        "reconciliation": {
            "unmatched_receipt_ids": reconciliation["unmatched_receipt_ids"],
            "ineligible_receipt_ids": reconciliation["ineligible_receipt_ids"],
            "source_mismatch_receipt_ids": reconciliation["source_mismatch_receipt_ids"],
        },
        "reviews": reviews,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": authority,
    }
    packet["packet_digest"] = _canonical_digest(packet)
    return packet


def render_human_review_board(packet: dict[str, Any]) -> str:
    source_id = html.escape(str((packet.get("source") or {}).get("source_id") or ""))
    rows: list[str] = []
    for row in packet.get("reviews", []):
        review_id = html.escape(str(row.get("review_id") or ""))
        crop_file = html.escape(str(row.get("crop_file") or ""), quote=True)
        review_state = html.escape(str(row.get("review_state") or ""))
        ocr_status = html.escape(str(row.get("ocr_comparison_status") or ""))
        proposals = ", ".join(str(value) for value in row.get("ocr_normalized_texts") or []) or "—"
        proposals = html.escape(proposals)
        value = row.get("validated_value_m")
        value_text = "—" if value is None else html.escape(f"{float(value):.2f} m")
        rows.append(
            "<tr>"
            f"<td><code>{review_id}</code></td>"
            f"<td><img src=\"{crop_file}\" alt=\"{review_id}\" loading=\"lazy\"></td>"
            f"<td>{review_state}</td>"
            f"<td>{ocr_status}</td>"
            f"<td>{proposals}</td>"
            f"<td>{value_text}</td>"
            "</tr>"
        )

    return (
        "<!doctype html><html lang=\"it\"><head><meta charset=\"utf-8\">"
        f"<title>CEW-CAL-01 — revisione catene esterne — {source_id}</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:24px;line-height:1.35}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #bbb;padding:8px;vertical-align:top}"
        "img{max-width:520px;max-height:180px;object-fit:contain;background:#fff}code{font-size:.9em}"
        "</style></head><body>"
        f"<h1>CEW-CAL-01 — revisione catene esterne — {source_id}</h1>"
        f"<p>Righe: {int(packet.get('review_count', 0))}; ricevute umane riusate: "
        f"{int(packet.get('reused_human_receipt_count', 0))}; da revisionare: "
        f"{int(packet.get('pending_human_review_count', 0))}.</p>"
        "<p>Questa tavola è un ausilio di revisione. I valori OCR non sono autoritativi e le righe pendenti non contengono valori umani precompilati.</p>"
        "<table><thead><tr><th>ID</th><th>Ritaglio esatto</th><th>Stato</th><th>OCR</th><th>Proposte OCR</th><th>Valore umano già qualificato</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>"
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_human_review_packet(
    review_dir: Path,
    *,
    receipt_paths: Iterable[Path],
    source_width_px: float,
) -> dict[str, Any]:
    manifest = _load_json(review_dir / "interval-text-review-manifest.json")
    comparison = _load_json(review_dir / "interval-ocr-comparison.json")
    receipts = [_load_json(path) for path in receipt_paths]
    packet = build_human_review_packet(
        manifest,
        comparison,
        receipts,
        source_width_px=source_width_px,
    )
    (review_dir / "external-chain-human-review-packet.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (review_dir / "external-chain-human-review.html").write_text(
        render_human_review_board(packet),
        encoding="utf-8",
    )
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the CEW-CAL-01 governed human-review packet for exact external-chain intervals"
    )
    parser.add_argument("--review-dir", required=True)
    parser.add_argument("--source-width-px", required=True, type=float)
    parser.add_argument("--receipt", action="append", default=[])
    args = parser.parse_args()
    packet = materialize_human_review_packet(
        Path(args.review_dir),
        receipt_paths=[Path(value) for value in args.receipt],
        source_width_px=args.source_width_px,
    )
    print(
        json.dumps(
            {
                "source_id": packet["source"]["source_id"],
                "review_count": packet["review_count"],
                "reused_human_receipt_count": packet["reused_human_receipt_count"],
                "pending_human_review_count": packet["pending_human_review_count"],
                "packet_digest": packet["packet_digest"],
                "primary_anchor_count": packet["primary_anchor_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
