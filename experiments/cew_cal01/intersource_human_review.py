from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


CANDIDATE_SCHEMA = "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1"
TARGETED_REVIEW_SCHEMA = "CEW_CAL01_INTERSOURCE_TARGETED_HUMAN_REVIEW_v1"
SELECTION_STRATEGY = "SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1"
DECISION_REQUIRED = "IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT"
SUPPORTED_NORMALIZATION_TRANSFORMS = {
    "IDENTITY",
    "ROTATE_90_COUNTERCLOCKWISE",
    "ROTATE_90_CLOCKWISE",
    "ROTATE_180",
}


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _point(value: Any, error_code: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(error_code)
    try:
        return [float(value[0]), float(value[1])]
    except (TypeError, ValueError) as exc:
        raise ValueError(error_code) from exc


def _require_candidate_contract(candidates: dict[str, Any]) -> tuple[list[dict[str, Any]], float, float]:
    if candidates.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_CANDIDATE_SCHEMA_INVALID")
    if dict(candidates.get("authority") or {}) != AUTHORITY_CLOSED:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_AUTHORITY_ESCALATION")
    if candidates.get("historical_comparator_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_HISTORICAL_INPUT_FORBIDDEN")
    if candidates.get("historical_affine_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_HISTORICAL_INPUT_FORBIDDEN")
    if candidates.get("eligible_for_registration_fit") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_AUTHORITY_ESCALATION")

    raster = dict(candidates.get("tav5_raster") or {})
    if raster.get("frame") != "RASTER_PIXEL" or not raster.get("raster_sha256"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_INVALID")
    try:
        width = float(raster.get("width_px", 0))
        height = float(raster.get("height_px", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_INVALID") from exc
    if width <= 0 or height <= 0:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_INVALID")

    tav5_source = dict(candidates.get("tav5_source") or {})
    tav02_source = dict(candidates.get("tav02_source") or {})
    if not tav5_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_SOURCE_INVALID")
    if tav02_source.get("source_id") != "TAV-02S" or not tav02_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV02_SOURCE_INVALID")
    if candidates.get("tav02_coordinate_frame") != "LOCAL_RELATIVE_METRIC":
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV02_FRAME_INVALID")
    if not candidates.get("tav02_lattice_digest"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_DIGEST_INVALID")

    rows = [dict(row) for row in candidates.get("candidates", [])]
    if int(candidates.get("source_candidate_count", len(rows))) != len(rows):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_CANDIDATE_COUNT_DRIFT")
    seen: set[str] = set()
    for row in rows:
        occurrence_id = str(row.get("occurrence_id") or "")
        if not occurrence_id or occurrence_id in seen:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_OCCURRENCE_INVALID")
        seen.add(occurrence_id)
        x, y = _point(row.get("source_point_px"), "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
        if row.get("source_frame") != "RASTER_PIXEL" or x < 0 or y < 0 or x > width or y > height:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
        evidence_refs = sorted(set(str(v) for v in row.get("source_evidence_refs", []) if str(v)))
        if not evidence_refs:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_EVIDENCE_MISSING")
        if row.get("governed_correspondence") is not False or row.get("fit_eligible") is not False:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_AUTHORITY_ESCALATION")

    nodes = [dict(row) for row in candidates.get("target_lattice_nodes", [])]
    if int(candidates.get("target_lattice_node_count", len(nodes))) != len(nodes):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_COUNT_DRIFT")
    node_ids = [str(row.get("lattice_node_id") or "") for row in nodes]
    if any(not value for value in node_ids) or len(set(node_ids)) != len(node_ids):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID")
    return rows, width, height


def select_targeted_review_batch(candidates: dict[str, Any], batch_size: int = 8) -> list[str]:
    """Select TAV.5 review occurrences without reading target lattice geometry."""

    rows, width, height = _require_candidate_contract(candidates)
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1 or batch_size > len(rows):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_BATCH_SIZE_INVALID")

    by_id = {str(row["occurrence_id"]): row for row in rows}

    def evidence_strength(occurrence_id: str) -> int:
        return len(set(str(v) for v in by_id[occurrence_id].get("source_evidence_refs", []) if str(v)))

    def normalized_point(occurrence_id: str) -> tuple[float, float]:
        x, y = _point(by_id[occurrence_id]["source_point_px"], "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
        return x / width, y / height

    remaining = set(by_id)
    seed = sorted(remaining, key=lambda occurrence_id: (-evidence_strength(occurrence_id), occurrence_id))[0]
    selected = [seed]
    remaining.remove(seed)

    while remaining and len(selected) < batch_size:
        scored: list[tuple[float, int, str]] = []
        selected_points = [normalized_point(occurrence_id) for occurrence_id in selected]
        for occurrence_id in remaining:
            x, y = normalized_point(occurrence_id)
            minimum_distance = min(
                math.hypot(x - selected_x, y - selected_y)
                for selected_x, selected_y in selected_points
            )
            scored.append((minimum_distance, evidence_strength(occurrence_id), occurrence_id))
        best = sorted(scored, key=lambda row: (-row[0], -row[1], row[2]))[0][2]
        selected.append(best)
        remaining.remove(best)

    return selected


def compute_context_crop_bbox(
    source_point_px: list[float],
    width_px: int,
    height_px: int,
    *,
    half_span_px: int = 700,
) -> list[int]:
    if width_px <= 0 or height_px <= 0 or half_span_px <= 0:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_CROP_GEOMETRY_INVALID")
    x, y = _point(source_point_px, "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
    if x < 0 or y < 0 or x > width_px or y > height_px:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
    cx = int(round(x))
    cy = int(round(y))
    return [
        max(0, cx - half_span_px),
        max(0, cy - half_span_px),
        min(int(width_px), cx + half_span_px),
        min(int(height_px), cy + half_span_px),
    ]


def resolve_normalized_dimensions(
    source_width_px: int,
    source_height_px: int,
    transform: str,
) -> tuple[int, int]:
    if source_width_px <= 0 or source_height_px <= 0 or transform not in SUPPORTED_NORMALIZATION_TRANSFORMS:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_NORMALIZATION_UNSUPPORTED")
    if transform in {"ROTATE_90_COUNTERCLOCKWISE", "ROTATE_90_CLOCKWISE"}:
        return int(source_height_px), int(source_width_px)
    return int(source_width_px), int(source_height_px)


def _validate_asset_record(raw: dict[str, Any], *, require_bbox: bool) -> dict[str, Any]:
    row = dict(raw)
    if not row.get("file") or not str(row.get("sha256") or "").startswith("sha256:"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_ASSET_INVALID")
    if require_bbox:
        bbox = row.get("crop_bbox_px")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_ASSET_INVALID")
    return row


def build_targeted_review_manifest(
    candidates: dict[str, Any],
    selected_occurrence_ids: list[str],
    source_assets: dict[str, dict[str, Any]],
    target_overview: dict[str, Any],
) -> dict[str, Any]:
    rows, _, _ = _require_candidate_contract(candidates)
    candidate_by_id = {str(row["occurrence_id"]): row for row in rows}
    selected = [str(value) for value in selected_occurrence_ids]
    if not selected or len(set(selected)) != len(selected) or any(value not in candidate_by_id for value in selected):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_SELECTION_INVALID")
    if set(source_assets) != set(selected):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_ASSET_SET_DRIFT")

    overview = _validate_asset_record(target_overview, require_bbox=False)
    nodes = sorted(
        [dict(row) for row in candidates.get("target_lattice_nodes", [])],
        key=lambda row: str(row.get("lattice_node_id") or ""),
    )
    lattice_context = []
    for row in nodes:
        lattice_context.append(
            {
                "lattice_node_id": str(row["lattice_node_id"]),
                "source_point_normalized_px": _point(
                    row.get("source_point_normalized_px"),
                    "CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID",
                ),
                "local_metric_xy_m": _point(
                    row.get("local_metric_xy_m"),
                    "CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID",
                ),
            }
        )

    review_items = []
    for occurrence_id in selected:
        source_row = candidate_by_id[occurrence_id]
        review_items.append(
            {
                "review_item_id": f"CEW-CAL01-TARGETED-INTERSOURCE:{occurrence_id}",
                "occurrence_id": occurrence_id,
                "source_point_px": _point(
                    source_row.get("source_point_px"),
                    "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID",
                ),
                "source_frame": "RASTER_PIXEL",
                "source_evidence_refs": sorted(
                    set(str(v) for v in source_row.get("source_evidence_refs", []) if str(v))
                ),
                "source_context_asset": _validate_asset_record(
                    source_assets[occurrence_id], require_bbox=True
                ),
                "decision_required": DECISION_REQUIRED,
                "human_confirmation_required": True,
            }
        )

    result: dict[str, Any] = {
        "schema": TARGETED_REVIEW_SCHEMA,
        "program": "CEW-CAL-01",
        "candidate_digest": candidates.get("candidate_digest"),
        "tav5_source": dict(candidates["tav5_source"]),
        "tav5_raster": dict(candidates["tav5_raster"]),
        "tav02_source": dict(candidates["tav02_source"]),
        "tav02_lattice_digest": candidates.get("tav02_lattice_digest"),
        "tav02_coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "source_candidate_count": len(rows),
        "target_lattice_node_count": len(lattice_context),
        "selection_strategy": SELECTION_STRATEGY,
        "target_geometry_used_for_selection": False,
        "target_node_ranking_performed": False,
        "automatic_homology_proposed": False,
        "selected_occurrence_ids": selected,
        "review_item_count": len(review_items),
        "review_items": review_items,
        "target_overview_asset": overview,
        "target_lattice_context": lattice_context,
        "decision_required": DECISION_REQUIRED,
        "human_confirmation_required": True,
        "eligible_for_registration_fit": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["review_package_digest"] = _canonical_digest(result)
    return result


def build_review_board_html(manifest: dict[str, Any]) -> str:
    if manifest.get("schema") != TARGETED_REVIEW_SCHEMA:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_MANIFEST_SCHEMA_INVALID")
    if manifest.get("target_geometry_used_for_selection") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TARGET_LEAKAGE")
    if manifest.get("target_node_ranking_performed") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TARGET_LEAKAGE")
    if manifest.get("automatic_homology_proposed") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TARGET_LEAKAGE")

    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    source_cards = []
    for item in manifest.get("review_items", []):
        evidence = "<br>".join(esc(value) for value in item.get("source_evidence_refs", []))
        source_cards.append(
            "<article class='card'>"
            f"<h3>{esc(item.get('occurrence_id'))}</h3>"
            f"<img src='{esc(item.get('source_context_asset', {}).get('file'))}' alt='TAV.5 source context'>"
            f"<p><strong>Primary evidence</strong><br>{evidence}</p>"
            "<p><strong>Professional action:</strong> identify one exact TAV-02S lattice node only when the documentary/structural evidence justifies the same physical support; otherwise reject.</p>"
            "</article>"
        )

    lattice_rows = []
    for node in manifest.get("target_lattice_context", []):
        local_xy = node.get("local_metric_xy_m", ["", ""])
        source_xy = node.get("source_point_normalized_px", ["", ""])
        lattice_rows.append(
            "<tr>"
            f"<td>{esc(node.get('lattice_node_id'))}</td>"
            f"<td>{esc(local_xy[0])}, {esc(local_xy[1])}</td>"
            f"<td>{esc(source_xy[0])}, {esc(source_xy[1])}</td>"
            "</tr>"
        )

    overview_file = manifest.get("target_overview_asset", {}).get("file", "")
    digest = manifest.get("review_package_digest", "")
    return """<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>CEW-CAL-01 Targeted Inter-Source Human Review</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;padding:24px;line-height:1.45;background:#f6f6f6;color:#111}
main{max-width:1500px;margin:auto}.warning{padding:14px;border:2px solid #444;background:#fff;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}.card{background:#fff;padding:14px;border:1px solid #aaa}.card img,.overview img{max-width:100%;height:auto;border:1px solid #bbb}.overview{background:#fff;padding:14px;margin:18px 0}table{width:100%;border-collapse:collapse;background:#fff}th,td{border:1px solid #bbb;padding:7px;text-align:left;font-size:14px}code{overflow-wrap:anywhere}
</style>
</head>
<body><main>
<h1>CEW-CAL-01 — Targeted Inter-Source Human Review</h1>
<p><strong>Review package digest:</strong> <code>""" + esc(digest) + """</code></p>
<div class='warning'><strong>No target identity is suggested by the system.</strong> The TAV.5 batch was selected only from TAV.5 evidence and spatial coverage. The TAV-02S lattice is shown only as a professional comparison surface.</div>
<div class='warning'>TAV-02S local metric coordinates are <strong>not surveyed or project coordinates</strong>. They are a relative reference frame and do not authorize structural identity, canonical geometry, M0-G or engineering use.</div>
<section><h2>TAV.5 source contexts</h2><div class='grid'>""" + "".join(source_cards) + """</div></section>
<section class='overview'><h2>TAV-02S normalized lattice context</h2><img src='""" + esc(overview_file) + """' alt='TAV-02S lattice context with all nodes labelled'></section>
<section><h2>TAV-02S lattice node register</h2><table><thead><tr><th>Node ID</th><th>Local relative metric XY (m)</th><th>Normalized source XY (px)</th></tr></thead><tbody>""" + "".join(lattice_rows) + """</tbody></table></section>
</main></body></html>"""


def _rotate_image_for_normalization(image: Any, transform: str, cv2: Any) -> Any:
    if transform == "IDENTITY":
        return image.copy()
    if transform == "ROTATE_90_COUNTERCLOCKWISE":
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if transform == "ROTATE_90_CLOCKWISE":
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if transform == "ROTATE_180":
        return cv2.rotate(image, cv2.ROTATE_180)
    raise ValueError("CAL01_INTERSOURCE_REVIEW_NORMALIZATION_UNSUPPORTED")


def materialize_targeted_review_package(
    candidates_path: Path,
    tav5_image_path: Path,
    tav02_image_path: Path,
    tav02_discovery_path: Path,
    output_dir: Path,
    *,
    batch_size: int = 8,
    half_span_px: int = 700,
    overview_max_width_px: int = 2600,
) -> dict[str, Any]:
    import cv2

    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    rows, tav5_width, tav5_height = _require_candidate_contract(candidates)
    selected = select_targeted_review_batch(candidates, batch_size)
    row_by_id = {str(row["occurrence_id"]): row for row in rows}

    tav5_image = cv2.imread(str(tav5_image_path), cv2.IMREAD_COLOR)
    if tav5_image is None:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_IMAGE_UNREADABLE")
    actual_tav5_height, actual_tav5_width = tav5_image.shape[:2]
    if (actual_tav5_width, actual_tav5_height) != (int(tav5_width), int(tav5_height)):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_DIMENSION_DRIFT")

    discovery = json.loads(tav02_discovery_path.read_text(encoding="utf-8"))
    normalization = dict((discovery.get("plan_envelope") or {}).get("normalization") or {})
    transform = str(normalization.get("transform") or "")
    source_width = int(normalization.get("source_width_px") or 0)
    source_height = int(normalization.get("source_height_px") or 0)
    expected_normalized_width, expected_normalized_height = resolve_normalized_dimensions(
        source_width,
        source_height,
        transform,
    )
    if (
        int(normalization.get("normalized_width_px") or 0),
        int(normalization.get("normalized_height_px") or 0),
    ) != (expected_normalized_width, expected_normalized_height):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_NORMALIZATION_DIMENSION_DRIFT")

    tav02_image = cv2.imread(str(tav02_image_path), cv2.IMREAD_COLOR)
    if tav02_image is None:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV02_IMAGE_UNREADABLE")
    actual_tav02_height, actual_tav02_width = tav02_image.shape[:2]
    if (actual_tav02_width, actual_tav02_height) != (source_width, source_height):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV02_RASTER_DIMENSION_DRIFT")
    normalized = _rotate_image_for_normalization(tav02_image, transform, cv2)
    if (normalized.shape[1], normalized.shape[0]) != (expected_normalized_width, expected_normalized_height):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_NORMALIZATION_DIMENSION_DRIFT")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_assets: dict[str, dict[str, Any]] = {}
    for occurrence_id in selected:
        source_point = _point(
            row_by_id[occurrence_id].get("source_point_px"),
            "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID",
        )
        bbox = compute_context_crop_bbox(
            source_point,
            actual_tav5_width,
            actual_tav5_height,
            half_span_px=half_span_px,
        )
        x0, y0, x1, y1 = bbox
        crop = tav5_image[y0:y1, x0:x1].copy()
        local_x = int(round(source_point[0])) - x0
        local_y = int(round(source_point[1])) - y0
        cv2.drawMarker(crop, (local_x, local_y), (0, 0, 255), cv2.MARKER_CROSS, 44, 3)
        cv2.rectangle(
            crop,
            (max(0, local_x - 32), max(0, local_y - 32)),
            (min(crop.shape[1] - 1, local_x + 32), min(crop.shape[0] - 1, local_y + 32)),
            (0, 0, 255),
            2,
        )
        file_name = f"tav5-{occurrence_id.lower()}-context.png"
        asset_path = output_dir / file_name
        if not cv2.imwrite(str(asset_path), crop):
            raise ValueError("CAL01_INTERSOURCE_REVIEW_ASSET_WRITE_FAILED")
        source_assets[occurrence_id] = {
            "file": file_name,
            "sha256": _file_digest(asset_path),
            "crop_bbox_px": bbox,
            "source_point_px": source_point,
            "source_frame": "RASTER_PIXEL",
        }

    scale = min(1.0, float(overview_max_width_px) / float(expected_normalized_width))
    if scale < 1.0:
        overview = cv2.resize(
            normalized,
            (int(round(expected_normalized_width * scale)), int(round(expected_normalized_height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    else:
        overview = normalized.copy()

    for node in sorted(candidates.get("target_lattice_nodes", []), key=lambda row: str(row.get("lattice_node_id") or "")):
        point = _point(
            node.get("source_point_normalized_px"),
            "CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID",
        )
        if point[0] < 0 or point[1] < 0 or point[0] > expected_normalized_width or point[1] > expected_normalized_height:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_OUTSIDE_NORMALIZED_RASTER")
        px = int(round(point[0] * scale))
        py = int(round(point[1] * scale))
        cv2.circle(overview, (px, py), 8, (0, 0, 255), 2)
        cv2.putText(
            overview,
            str(node["lattice_node_id"]),
            (px + 10, py - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

    overview_path = output_dir / "tav02-lattice-overview.png"
    if not cv2.imwrite(str(overview_path), overview):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_ASSET_WRITE_FAILED")
    target_overview = {
        "file": overview_path.name,
        "sha256": _file_digest(overview_path),
        "normalization_transform": transform,
        "normalized_width_px": expected_normalized_width,
        "normalized_height_px": expected_normalized_height,
        "render_scale": scale,
        "render_width_px": int(overview.shape[1]),
        "render_height_px": int(overview.shape[0]),
    }

    manifest = build_targeted_review_manifest(candidates, selected, source_assets, target_overview)
    manifest["review_board_file"] = "targeted-intersource-human-review.html"
    manifest["review_package_digest"] = _canonical_digest(
        {key: value for key, value in manifest.items() if key != "review_package_digest"}
    )

    manifest_path = output_dir / "targeted-intersource-human-review.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    board_path = output_dir / "targeted-intersource-human-review.html"
    board_path.write_text(build_review_board_html(manifest), encoding="utf-8")

    return {
        "manifest": manifest,
        "manifest_file": str(manifest_path),
        "manifest_sha256": _file_digest(manifest_path),
        "review_board_file": str(board_path),
        "review_board_sha256": _file_digest(board_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize CEW-CAL-01 targeted inter-source human review assets")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--tav5-image", required=True)
    parser.add_argument("--tav02-image", required=True)
    parser.add_argument("--tav02-discovery", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--half-span-px", type=int, default=700)
    args = parser.parse_args()

    result = materialize_targeted_review_package(
        Path(args.candidates),
        Path(args.tav5_image),
        Path(args.tav02_image),
        Path(args.tav02_discovery),
        Path(args.output_dir),
        batch_size=args.batch_size,
        half_span_px=args.half_span_px,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
