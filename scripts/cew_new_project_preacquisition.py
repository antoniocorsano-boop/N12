#!/usr/bin/env python3
"""CEW new-project document pre-acquisition.

This module intentionally starts with ZERO semantic object prior. It analyzes
arbitrary PDF bytes, builds source/page-bound graphic primitive candidates,
clusters them by non-semantic geometry, and optionally compares clusters with a
governed graphic reference pack. Library matches are proposals only.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pymupdf

SCHEMA = "CEW_NEW_PROJECT_PREACQUISITION_REPORT_v1"
EXTRACTOR_VERSION = "CEW_NEW_PROJECT_PREFLIGHT_PYMUPDF_v2"
CONTRACT_SCHEMA = "CEW_NEW_PROJECT_PREACQUISITION_CONTRACT_v1"
LIBRARY_SCHEMA = "CEW_GRAPHIC_REFERENCE_LIBRARY_INDEX_v1"

PRIMITIVE_FAMILIES = {
    "TEXT_BLOCK",
    "LINEAR_STROKE_GROUP",
    "RECTILINEAR_CLOSED_SHAPE",
    "CURVED_OR_ARC_SHAPE",
    "FILLED_OR_HATCHED_REGION",
    "RASTER_IMAGE_REGION",
    "COMPLEX_VECTOR_GROUP",
    "UNKNOWN_GRAPHIC_GROUP",
}

AUTHORITY = {
    "semantic_authority": "NONE_UNTIL_PROJECT_HUMAN_VALIDATION",
    "oar_human_confirmation": False,
    "oar_classification_confirmed": False,
    "f2_registry_written": False,
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_id(prefix: str, payload: Any, length: int = 20) -> str:
    digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    return f"{prefix}{digest[:length]}"


def _normalized_bbox(rect: pymupdf.Rect, page_rect: pymupdf.Rect) -> dict[str, float]:
    """Normalize a source geometry bbox while preserving linear primitives.

    PyMuPDF legitimately returns zero-height / zero-width rectangles for exact
    horizontal or vertical strokes. Those are valid graphic primitives, not
    empty evidence. Expand only degenerate dimensions by a deterministic
    sub-point halo before clipping to the page.
    """
    if page_rect.width <= 0 or page_rect.height <= 0:
        raise ValueError("INVALID_PAGE_GEOMETRY")
    working = pymupdf.Rect(rect)
    pad_x = max(0.25, float(page_rect.width) * 1e-6)
    pad_y = max(0.25, float(page_rect.height) * 1e-6)
    if working.width <= 0:
        working.x0 -= pad_x
        working.x1 += pad_x
    if working.height <= 0:
        working.y0 -= pad_y
        working.y1 += pad_y
    clipped = working & page_rect
    if clipped.is_empty or clipped.width <= 0 or clipped.height <= 0:
        raise ValueError("EMPTY_GRAPHIC_BBOX")
    x = max(0.0, min(1.0, clipped.x0 / page_rect.width))
    y = max(0.0, min(1.0, clipped.y0 / page_rect.height))
    x2 = max(x, min(1.0, clipped.x1 / page_rect.width))
    y2 = max(y, min(1.0, clipped.y1 / page_rect.height))
    return {
        "x": round(x, 10),
        "y": round(y, 10),
        "w": round(x2 - x, 10),
        "h": round(y2 - y, 10),
    }


def _aspect_bucket(bbox: dict[str, float]) -> str:
    ratio = bbox["w"] / max(bbox["h"], 1e-12)
    if ratio < 0.35:
        return "VERY_TALL"
    if ratio < 0.75:
        return "TALL"
    if ratio <= 1.35:
        return "SQUAREISH"
    if ratio <= 2.85:
        return "WIDE"
    return "VERY_WIDE"


def _area_bucket(bbox: dict[str, float]) -> str:
    area = bbox["w"] * bbox["h"]
    if area < 0.0001:
        return "TINY"
    if area < 0.001:
        return "SMALL"
    if area < 0.01:
        return "MEDIUM"
    return "LARGE"


def _complexity_bucket(item_count: int) -> str:
    if item_count <= 1:
        return "ONE"
    if item_count <= 4:
        return "FEW"
    if item_count <= 12:
        return "MEDIUM"
    return "MANY"


def _drawing_family(drawing: dict[str, Any]) -> str:
    items = drawing.get("items") or []
    ops = [str(item[0]) for item in items if item]
    if drawing.get("fill") is not None:
        return "FILLED_OR_HATCHED_REGION"
    if any(op in {"re", "qu"} for op in ops) and not any(op == "c" for op in ops):
        return "RECTILINEAR_CLOSED_SHAPE"
    if any(op == "c" for op in ops):
        return "CURVED_OR_ARC_SHAPE"
    if ops and all(op == "l" for op in ops) and len(ops) <= 6:
        return "LINEAR_STROKE_GROUP"
    if items:
        return "COMPLEX_VECTOR_GROUP"
    return "UNKNOWN_GRAPHIC_GROUP"


def _candidate(
    *,
    source_version_id: str,
    source_sha256: str,
    page_index: int,
    bbox: dict[str, float],
    primitive_family: str,
    detector: str,
    stats: dict[str, Any],
) -> dict[str, Any]:
    if primitive_family not in PRIMITIVE_FAMILIES:
        raise ValueError("UNKNOWN_PRIMITIVE_FAMILY")
    signature = {
        "primitive_family": primitive_family,
        "aspect_bucket": _aspect_bucket(bbox),
        "area_bucket": _area_bucket(bbox),
        "complexity_bucket": _complexity_bucket(int(stats.get("item_count", 1))),
        "filled": bool(stats.get("filled", False)),
        "stroke_width_bucket": stats.get("stroke_width_bucket", "NA"),
    }
    identity = {
        "source_sha256": source_sha256,
        "page_index": page_index,
        "bbox": bbox,
        "detector": detector,
        "extractor_version": EXTRACTOR_VERSION,
        "signature": signature,
    }
    return {
        "candidate_id": _stable_id("GPC-", identity),
        "source_version_id": source_version_id,
        "source_sha256": source_sha256,
        "page_index": page_index,
        "coordinate_system": "NORMALIZED_0_1",
        "bbox": bbox,
        "primitive_family": primitive_family,
        "detector": detector,
        "extractor_version": EXTRACTOR_VERSION,
        "feature_signature": signature,
        "statistics": stats,
        "semantic_meaning": None,
        "semantic_authority": "NONE",
    }


def _stroke_width_bucket(width: Any) -> str:
    try:
        value = float(width)
    except (TypeError, ValueError):
        return "NA"
    if value <= 0.5:
        return "THIN"
    if value <= 1.5:
        return "MEDIUM"
    return "THICK"


def _extract_page_candidates(
    page: pymupdf.Page,
    *,
    source_version_id: str,
    source_sha256: str,
    page_index: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page_rect = page.rect
    candidates: list[dict[str, Any]] = []

    drawings = page.get_drawings()
    for drawing_index, drawing in enumerate(drawings):
        rect = drawing.get("rect")
        if rect is None:
            continue
        try:
            bbox = _normalized_bbox(pymupdf.Rect(rect), page_rect)
        except ValueError:
            continue
        items = drawing.get("items") or []
        family = _drawing_family(drawing)
        candidates.append(
            _candidate(
                source_version_id=source_version_id,
                source_sha256=source_sha256,
                page_index=page_index,
                bbox=bbox,
                primitive_family=family,
                detector="PYMUPDF_GET_DRAWINGS",
                stats={
                    "drawing_index": drawing_index,
                    "item_count": len(items),
                    "filled": drawing.get("fill") is not None,
                    "stroke_width_bucket": _stroke_width_bucket(drawing.get("width")),
                },
            )
        )

    text_blocks = page.get_text("blocks")
    for block_index, block in enumerate(text_blocks):
        if len(block) < 4:
            continue
        rect = pymupdf.Rect(float(block[0]), float(block[1]), float(block[2]), float(block[3]))
        try:
            bbox = _normalized_bbox(rect, page_rect)
        except ValueError:
            continue
        text = str(block[4]) if len(block) > 4 else ""
        candidates.append(
            _candidate(
                source_version_id=source_version_id,
                source_sha256=source_sha256,
                page_index=page_index,
                bbox=bbox,
                primitive_family="TEXT_BLOCK",
                detector="PYMUPDF_TEXT_BLOCK",
                stats={
                    "block_index": block_index,
                    "item_count": 1,
                    "text_length_bucket": "EMPTY" if not text.strip() else ("SHORT" if len(text) < 40 else "LONG"),
                },
            )
        )

    image_regions = 0
    seen_image_boxes: set[tuple[float, float, float, float]] = set()
    for image in page.get_images(full=True):
        if not image:
            continue
        xref = int(image[0])
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        for rect in rects:
            try:
                bbox = _normalized_bbox(pymupdf.Rect(rect), page_rect)
            except ValueError:
                continue
            key = (bbox["x"], bbox["y"], bbox["w"], bbox["h"])
            if key in seen_image_boxes:
                continue
            seen_image_boxes.add(key)
            image_regions += 1
            candidates.append(
                _candidate(
                    source_version_id=source_version_id,
                    source_sha256=source_sha256,
                    page_index=page_index,
                    bbox=bbox,
                    primitive_family="RASTER_IMAGE_REGION",
                    detector="PYMUPDF_IMAGE_RECT",
                    stats={"xref": xref, "item_count": 1},
                )
            )

    vector_count = len(drawings)
    text_count = len(text_blocks)
    if vector_count >= 8 and image_regions == 0:
        modality = "NATIVE_VECTOR"
    elif image_regions > 0 and vector_count < 5:
        modality = "RASTER_OR_SCANNED"
    elif image_regions > 0 and vector_count >= 5:
        modality = "MIXED"
    else:
        modality = "TEXT_OR_SPARSE"

    preflight = {
        "page_index": page_index,
        "width_pt": round(float(page_rect.width), 6),
        "height_pt": round(float(page_rect.height), 6),
        "rotation": int(page.rotation),
        "modality": modality,
        "vector_drawing_count": vector_count,
        "text_block_count": text_count,
        "raster_image_region_count": image_regions,
        "primitive_candidate_count": len(candidates),
        "semantic_object_prior_used": False,
    }
    return candidates, preflight


def cluster_primitives(candidates: list[dict[str, Any]], source_sha256: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        signature = candidate["feature_signature"]
        cluster_key = _canonical(
            {
                "primitive_family": signature["primitive_family"],
                "aspect_bucket": signature["aspect_bucket"],
                "area_bucket": signature["area_bucket"],
                "complexity_bucket": signature["complexity_bucket"],
                "filled": signature["filled"],
                "stroke_width_bucket": signature["stroke_width_bucket"],
            }
        )
        grouped[cluster_key].append(candidate)

    clusters: list[dict[str, Any]] = []
    for key, members in grouped.items():
        feature = json.loads(key)
        identity = {
            "source_sha256": source_sha256,
            "feature": feature,
            "member_candidate_ids": sorted(m["candidate_id"] for m in members),
        }
        page_indices = sorted({int(m["page_index"]) for m in members})
        clusters.append(
            {
                "cluster_id": _stable_id("GC-", identity, length=14),
                "cluster_kind": "NON_SEMANTIC_GRAPHIC_CLUSTER",
                "feature_signature": feature,
                "occurrence_count": len(members),
                "page_indices": page_indices,
                "member_candidate_ids": sorted(m["candidate_id"] for m in members),
                "semantic_meaning": None,
                "automatic_structural_label": False,
                "human_review_required": True,
            }
        )
    clusters.sort(key=lambda c: (-c["occurrence_count"], c["cluster_id"]))
    return clusters


def _library_entries_fingerprint(entries: list[dict[str, Any]]) -> str:
    return _sha256(_canonical(entries).encode("utf-8"))


def match_clusters_to_library(
    clusters: list[dict[str, Any]], library_pack: dict[str, Any] | None
) -> tuple[str, list[dict[str, Any]], dict[str, Any] | None]:
    if library_pack is None:
        return "LIBRARY_NOT_CONFIGURED", [], None
    if library_pack.get("schema") != LIBRARY_SCHEMA:
        raise ValueError("GRAPHIC_LIBRARY_SCHEMA_INVALID")
    state = str(library_pack.get("status") or "LIBRARY_NOT_CONFIGURED")
    entries = library_pack.get("entries") or []
    if not entries:
        return ("LIBRARY_EMPTY" if state != "LIBRARY_NOT_CONFIGURED" else state), [], {
            "generation_id": library_pack.get("generation_id"),
            "content_sha256": library_pack.get("content_sha256"),
        }
    generation_id = str(library_pack.get("generation_id") or "").strip()
    fingerprint = str(library_pack.get("content_sha256") or "").strip().lower()
    if not generation_id or not fingerprint:
        raise ValueError("GRAPHIC_LIBRARY_GENERATION_OR_FINGERPRINT_REQUIRED")
    if fingerprint != _library_entries_fingerprint(entries):
        raise ValueError("GRAPHIC_LIBRARY_FINGERPRINT_MISMATCH")

    proposals: list[dict[str, Any]] = []
    for cluster in clusters:
        feature = cluster["feature_signature"]
        ranked: list[dict[str, Any]] = []
        for entry in entries:
            primitive_families = set(entry.get("primitive_families") or [])
            if primitive_families and feature["primitive_family"] not in primitive_families:
                continue
            score = 0.45
            aspect_buckets = set(entry.get("aspect_buckets") or [])
            area_buckets = set(entry.get("area_buckets") or [])
            if not aspect_buckets or feature["aspect_bucket"] in aspect_buckets:
                score += 0.30
            if not area_buckets or feature["area_bucket"] in area_buckets:
                score += 0.15
            if entry.get("filled") is None or bool(entry.get("filled")) == bool(feature["filled"]):
                score += 0.10
            ranked.append(
                {
                    "meaning": str(entry["meaning"]),
                    "score": round(min(1.0, score), 6),
                    "library_entry_id": str(entry["entry_id"]),
                    "library_tier": str(entry.get("tier") or "EXTERNAL_REFERENCE"),
                    "support_refs": list(entry.get("source_refs") or []),
                    "counterexample_refs": list(entry.get("counterexample_refs") or []),
                }
            )
        ranked.sort(key=lambda x: (-x["score"], x["meaning"], x["library_entry_id"]))
        if ranked:
            proposals.append(
                {
                    "cluster_id": cluster["cluster_id"],
                    "matches": ranked[:5],
                    "library_generation_id": generation_id,
                    "library_content_sha256": fingerprint,
                    "project_semantic_authority": "NONE",
                    "human_project_validation_required": True,
                }
            )
    return "LIBRARY_MATCHES_AVAILABLE" if proposals else "LIBRARY_AVAILABLE_UNVERIFIED_FOR_CONTEXT", proposals, {
        "generation_id": generation_id,
        "content_sha256": fingerprint,
    }


def build_human_triage_queue(
    clusters: list[dict[str, Any]], proposals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    proposal_map = {p["cluster_id"]: p for p in proposals}
    queue: list[dict[str, Any]] = []
    for cluster in clusters:
        proposal = proposal_map.get(cluster["cluster_id"])
        queue.append(
            {
                "cluster_id": cluster["cluster_id"],
                "occurrence_count": cluster["occurrence_count"],
                "page_indices": cluster["page_indices"],
                "feature_signature": cluster["feature_signature"],
                "library_suggestions": proposal["matches"] if proposal else [],
                "question": "What does this recurring graphic family mean in this project?",
                "allowed_actions": [
                    "TEACH_THIS_IS",
                    "NOT_THIS",
                    "UNCERTAIN",
                    "SPLIT_CLUSTER",
                    "MERGE_CLUSTERS",
                    "IGNORE_FOR_NOW",
                ],
                "semantic_authority_before_action": "NONE",
            }
        )
    return queue


def preacquire_pdf(
    payload: bytes,
    *,
    source_version_id: str,
    expected_sha256: str | None = None,
    library_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not payload.startswith(b"%PDF"):
        raise ValueError("PREACQUISITION_INPUT_NOT_PDF")
    source_version_id = str(source_version_id).strip()
    if not source_version_id:
        raise ValueError("SOURCE_VERSION_ID_REQUIRED")
    digest = _sha256(payload)
    if expected_sha256 and digest.lower() != expected_sha256.strip().lower():
        raise ValueError("SOURCE_SHA256_MISMATCH")

    all_candidates: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            candidates, preflight = _extract_page_candidates(
                page,
                source_version_id=source_version_id,
                source_sha256=digest,
                page_index=page_index,
            )
            all_candidates.extend(candidates)
            pages.append(preflight)

    clusters = cluster_primitives(all_candidates, digest)
    library_state, proposals, library_generation = match_clusters_to_library(clusters, library_pack)
    triage = build_human_triage_queue(clusters, proposals)
    report_identity = {
        "source_sha256": digest,
        "extractor_version": EXTRACTOR_VERSION,
        "candidate_ids": [c["candidate_id"] for c in all_candidates],
        "cluster_ids": [c["cluster_id"] for c in clusters],
        "library_generation": library_generation,
    }
    return {
        "schema": SCHEMA,
        "contract_schema": CONTRACT_SCHEMA,
        "mode": "NEW_PROJECT_ZERO_SEMANTIC_PRIOR",
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "extractor_version": EXTRACTOR_VERSION,
        "report_fingerprint": "sha256:" + _sha256(_canonical(report_identity).encode("utf-8")),
        "page_count": len(pages),
        "pages": pages,
        "primitive_candidate_count": len(all_candidates),
        "primitive_candidates": all_candidates,
        "graphic_cluster_count": len(clusters),
        "graphic_clusters": clusters,
        "library_state": library_state,
        "library_generation": library_generation,
        "knowledge_match_proposals": proposals,
        "human_triage_queue": triage,
        "known_object_types_required": False,
        "semantic_labels_assigned_automatically": False,
        "authority": dict(AUTHORITY),
        "next_gate": "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CEW zero-prior new-project PDF pre-acquisition")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--source-version-id", required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--library", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = args.pdf.read_bytes()
    library = json.loads(args.library.read_text(encoding="utf-8")) if args.library else None
    report = preacquire_pdf(
        payload,
        source_version_id=args.source_version_id,
        expected_sha256=args.expected_sha256,
        library_pack=library,
    )
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
