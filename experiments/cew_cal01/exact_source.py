from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from cew_b01.source_contract import load_source_contract, materialize_source, validate_frozen_n12_tav5
from experiments.cew_cal01.anchor_discovery import normalize_dimension_text, proposal_from_ocr_token
from experiments.cew_cal01.numeric_role import dimension_tick_relation


SOURCE_CONTRACT_PATH = Path("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
RENDER_DPI = 300
AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + _sha256_bytes(payload)


def _render_primary_pdf(pdf_path: Path, output_png: Path) -> dict[str, Any]:
    import cv2
    import numpy as np
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(str(pdf_path))
    try:
        page = document[0]
        try:
            scale = RENDER_DPI / 72.0
            bitmap = page.render(scale=scale, rotation=0)
            try:
                array = bitmap.to_numpy()
            finally:
                close_bitmap = getattr(bitmap, "close", None)
                if callable(close_bitmap):
                    close_bitmap()
        finally:
            close_page = getattr(page, "close", None)
            if callable(close_page):
                close_page()
    finally:
        close_document = getattr(document, "close", None)
        if callable(close_document):
            close_document()

    if array.ndim == 2:
        gray = array.astype(np.uint8)
    elif array.shape[2] == 4:
        gray = cv2.cvtColor(array, cv2.COLOR_BGRA2GRAY)
    else:
        gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_png), gray):
        raise RuntimeError("CAL01_RENDER_WRITE_FAILED")
    return {
        "width_px": int(gray.shape[1]),
        "height_px": int(gray.shape[0]),
        "png_sha256": _sha256_file(output_png),
        "pixel_sha256": _sha256_bytes(f"{gray.shape[1]}x{gray.shape[0]}|GRAY|".encode("ascii") + gray.tobytes()),
        "gray": gray,
    }


def _run_tesseract_tsv(image_path: Path, *, psm: int) -> list[dict[str, Any]]:
    command = ["tesseract", str(image_path), "stdout", "--psm", str(psm), "tsv"]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"CAL01_TESSERACT_FAILED:{proc.stderr.strip()}")
    rows: list[dict[str, Any]] = []
    reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t")
    for row in reader:
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        try:
            confidence = float(row.get("conf") or -1)
            left = int(row.get("left") or 0)
            top = int(row.get("top") or 0)
            width = int(row.get("width") or 0)
            height = int(row.get("height") or 0)
        except (TypeError, ValueError):
            continue
        if width <= 0 or height <= 0:
            continue
        rows.append(
            {
                "text": text,
                "confidence": confidence,
                "bbox_px": [left, top, left + width, top + height],
                "psm": psm,
            }
        )
    return rows


def _normalize_hough_lines(raw_lines: Any) -> list[tuple[float, float, float, float]]:
    """Normalize OpenCV HoughLinesP outputs across (N,4) and (N,1,4) shapes."""

    if raw_lines is None:
        return []
    normalized: list[tuple[float, float, float, float]] = []
    for item in raw_lines:
        candidate = item
        if isinstance(candidate, (list, tuple)) and len(candidate) == 1 and isinstance(candidate[0], (list, tuple)):
            candidate = candidate[0]
        if not isinstance(candidate, (list, tuple)) or len(candidate) != 4:
            raise ValueError("CAL01_HOUGH_LINE_SHAPE_INVALID")
        try:
            normalized.append(tuple(float(value) for value in candidate))
        except (TypeError, ValueError) as exc:
            raise ValueError("CAL01_HOUGH_LINE_VALUE_INVALID") from exc
    return normalized


def _dimension_geometry_cv2(gray: Any, bbox: list[float]) -> dict[str, Any]:
    import cv2
    import numpy as np

    height, width = gray.shape[:2]
    left, top, right, bottom = [int(round(value)) for value in bbox]
    token_w = max(1, right - left)
    token_h = max(1, bottom - top)
    margin_x = max(140, token_w * 7)
    margin_y = max(140, token_h * 7)
    x0 = max(0, left - margin_x)
    y0 = max(0, top - margin_y)
    x1 = min(width, right + margin_x)
    y1 = min(height, bottom + margin_y)
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0:
        return {"geometrically_bound": False, "reason": "EMPTY_LOCAL_WINDOW"}

    blurred = cv2.GaussianBlur(crop, (3, 3), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        11,
    )
    lines = cv2.HoughLinesP(
        binary,
        1,
        np.pi / 180.0,
        threshold=35,
        minLineLength=max(35, min(crop.shape[:2]) // 12),
        maxLineGap=12,
    )
    if lines is None:
        return {"geometrically_bound": False, "reason": "NO_LOCAL_LINES"}

    global_lines: list[tuple[float, float, float, float]] = []
    raw_lines = lines.tolist() if hasattr(lines, "tolist") else lines
    for lx1, ly1, lx2, ly2 in _normalize_hough_lines(raw_lines):
        global_lines.append((lx1 + x0, ly1 + y0, lx2 + x0, ly2 + y0))

    cx = (left + right) / 2.0
    cy = (top + bottom) / 2.0
    horizontal: list[tuple[float, float, float, float]] = []
    vertical: list[tuple[float, float, float, float]] = []
    for line in global_lines:
        ax, ay, bx, by = line
        dx = abs(bx - ax)
        dy = abs(by - ay)
        if dx >= 45 and dy <= max(3.0, dx * 0.04):
            horizontal.append(line)
        elif dy >= 45 and dx <= max(3.0, dy * 0.04):
            vertical.append(line)

    horizontal.sort(key=lambda line: (abs(((line[1] + line[3]) / 2.0) - cy), -abs(line[2] - line[0])))
    for main in horizontal:
        ax, ay, bx, by = main
        min_x, max_x = sorted((ax, bx))
        y_line = (ay + by) / 2.0
        if not (min_x <= cx <= max_x):
            continue
        refs = []
        for target_x in (min_x, max_x):
            candidates = []
            for ref in vertical:
                rx1, ry1, rx2, ry2 = ref
                ref_x = (rx1 + rx2) / 2.0
                ref_min_y, ref_max_y = sorted((ry1, ry2))
                if abs(ref_x - target_x) <= 18 and ref_min_y - 8 <= y_line <= ref_max_y + 8:
                    candidates.append((abs(ref_x - target_x), ref_x, ref_min_y, ref_max_y))
            if candidates:
                candidates.sort()
                refs.append(candidates[0])
        if len(refs) == 2 and abs(refs[0][1] - refs[1][1]) >= 30:
            return {
                "geometrically_bound": True,
                "orientation": "HORIZONTAL",
                "endpoint_a_px": [refs[0][1], y_line],
                "endpoint_b_px": [refs[1][1], y_line],
                "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
                "reference_style": "HOUGH_ENDPOINT_REFERENCES",
                "metric_anchor_promoted": False,
            }

    vertical.sort(key=lambda line: (abs(((line[0] + line[2]) / 2.0) - cx), -abs(line[3] - line[1])))
    for main in vertical:
        ax, ay, bx, by = main
        x_line = (ax + bx) / 2.0
        min_y, max_y = sorted((ay, by))
        if not (min_y <= cy <= max_y):
            continue
        refs = []
        for target_y in (min_y, max_y):
            candidates = []
            for ref in horizontal:
                rx1, ry1, rx2, ry2 = ref
                ref_y = (ry1 + ry2) / 2.0
                ref_min_x, ref_max_x = sorted((rx1, rx2))
                if abs(ref_y - target_y) <= 18 and ref_min_x - 8 <= x_line <= ref_max_x + 8:
                    candidates.append((abs(ref_y - target_y), ref_y, ref_min_x, ref_max_x))
            if candidates:
                candidates.sort()
                refs.append(candidates[0])
        if len(refs) == 2 and abs(refs[0][1] - refs[1][1]) >= 30:
            return {
                "geometrically_bound": True,
                "orientation": "VERTICAL",
                "endpoint_a_px": [x_line, refs[0][1]],
                "endpoint_b_px": [x_line, refs[1][1]],
                "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
                "reference_style": "HOUGH_ENDPOINT_REFERENCES",
                "metric_anchor_promoted": False,
            }

    tick_relations = [
        dimension_tick_relation(global_lines, token_bbox_px=bbox, expected_orientation=orientation)
        for orientation in ("HORIZONTAL", "VERTICAL")
    ]
    confirmed = [relation for relation in tick_relations if relation.get("confirmed") is True]
    if len(confirmed) == 1:
        relation = confirmed[0]
        return {
            "geometrically_bound": True,
            "orientation": relation["orientation"],
            "endpoint_a_px": relation["endpoint_a_px"],
            "endpoint_b_px": relation["endpoint_b_px"],
            "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
            "reference_style": relation["tick_style"],
            "metric_anchor_promoted": False,
        }
    if len(confirmed) > 1:
        return {"geometrically_bound": False, "reason": "AMBIGUOUS_DIMENSION_ORIENTATION"}

    return {"geometrically_bound": False, "reason": "TWO_REFERENCE_LINES_NOT_OBSERVED"}


def build_exact_source_dimension_inventory(source_repo: Path, output_dir: Path) -> dict[str, Any]:
    import cv2

    output_dir.mkdir(parents=True, exist_ok=True)
    contract = load_source_contract(SOURCE_CONTRACT_PATH)
    validate_frozen_n12_tav5(contract)
    materialized = materialize_source(contract, source_repo, output_dir / "tav5-primary.pdf")
    if materialized.sha256 != SOURCE_SHA256:
        raise RuntimeError("CAL01_SOURCE_DIGEST_DRIFT")

    render = _render_primary_pdf(Path(materialized.destination), output_dir / "tav5-primary-300dpi.png")
    gray = render.pop("gray")
    page_width = int(render["width_px"])
    page_height = int(render["height_px"])

    tokens: list[dict[str, Any]] = []
    for psm in (11, 6):
        tokens.extend(_run_tesseract_tsv(output_dir / "tav5-primary-300dpi.png", psm=psm))

    proposals_by_key: dict[tuple[str, int, int, int, int], dict[str, Any]] = {}
    for token in tokens:
        if normalize_dimension_text(token["text"]) is None:
            continue
        proposal = proposal_from_ocr_token(token, page_width=page_width, page_height=page_height)
        proposal["ocr_psm"] = int(token["psm"])
        proposal["geometry"] = _dimension_geometry_cv2(gray, proposal["bbox_px"])
        key = (
            proposal["normalized_metric_text"],
            int(round(proposal["bbox_px"][0] / 8.0)),
            int(round(proposal["bbox_px"][1] / 8.0)),
            int(round(proposal["bbox_px"][2] / 8.0)),
            int(round(proposal["bbox_px"][3] / 8.0)),
        )
        existing = proposals_by_key.get(key)
        if existing is None or proposal["ocr_confidence"] > existing["ocr_confidence"]:
            proposals_by_key[key] = proposal

    proposals = sorted(
        proposals_by_key.values(),
        key=lambda item: (item["bbox_px"][1], item["bbox_px"][0], item["normalized_metric_text"]),
    )
    bound_count = sum(1 for item in proposals if item["geometry"].get("geometrically_bound") is True)

    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for item in proposals:
        left, top, right, bottom = [int(round(value)) for value in item["bbox_px"]]
        bound = item["geometry"].get("geometrically_bound") is True
        color = (0, 180, 0) if bound else (0, 140, 255)
        cv2.rectangle(overlay, (left, top), (right, bottom), color, 2)
        if bound:
            a = item["geometry"]["endpoint_a_px"]
            b = item["geometry"]["endpoint_b_px"]
            cv2.line(overlay, (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1]))), color, 2)
    cv2.imwrite(str(output_dir / "dimension-proposal-overlay.png"), overlay)

    result = {
        "schema": "CEW_CAL01_EXACT_SOURCE_DIMENSION_DISCOVERY_v1",
        "program": "CEW-CAL-01",
        "source": {
            "repository": contract.repository,
            "commit": contract.commit,
            "path": contract.path,
            "sha256": contract.sha256,
            "page_index": contract.page_index,
        },
        "raster": render,
        "ocr_role": "DERIVATIVE_LOCALIZER_ONLY",
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "numeric_proposal_count": len(proposals),
        "geometrically_bound_dimension_count": bound_count,
        "primary_anchor_count": 0,
        "calibration_sufficiency": "NOT_YET_EVALUATED_FROM_DIMENSION_RELATIONS",
        "proposals": proposals,
        "authority": dict(AUTHORITY_CLOSED),
    }
    digest_payload = dict(result)
    result["discovery_digest"] = _canonical_digest(digest_payload)
    (output_dir / "dimension-discovery.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_exact_source_dimension_inventory(Path(args.source_repo), Path(args.output_dir))
    print(json.dumps({
        "source_sha256": result["source"]["sha256"],
        "numeric_proposal_count": result["numeric_proposal_count"],
        "geometrically_bound_dimension_count": result["geometrically_bound_dimension_count"],
        "discovery_digest": result["discovery_digest"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
