"""
Task 5: Terrace Case — Document Map + Evidence Crops
Generate evidence crops for the terrace region test case.
Links 4 pillars (N002, N005, N039 confirmed; N041 candidate)
to the original carpenteria PDF via evidence chain.
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import pypdfium2 as pdfium
from PIL import Image

from model.etwin.document_engine import (
    OriginalDocument, DocumentMap, SemanticRegion, Tile, EvidenceCrop,
    GeometricCoords, BBoxNative, BBoxNormalized, PixelCoords,
    SemanticRegionType, EvidenceStatus, save_json
)
from model.etwin.document_registry import load_registry
from model.etwin.document_map import build_document_map

CROPS_DIR = Path(r"docs\FOGLIO_LAVORO\etwin_crops")

# Terrace pillar positions from DXF TAV5 (in mm, DXF coordinate system)
TERRACE_PILLARS = {
    "N002": {"x_mm": 36481, "y_mm": 12234, "status": "LINE", "verify": "A", "type": "A02/N002/ES"},
    "N005": {"x_mm": 36484, "y_mm": 7840, "status": "LINE", "verify": "A", "type": "A03/N005/ES"},
    "N039": {"x_mm": 35456, "y_mm": 3226, "status": "LINE", "verify": "A", "type": "A22/N039/EN"},
    "N041": {"x_mm": 34119, "y_mm": 18523, "status": "TERM", "verify": "B", "type": "NONE"},
}

# DXF coordinate range for terrace region (estimated from node positions)
DXF_TERRACE_BOUNDS = {
    "x_min": 33000, "x_max": 38000,
    "y_min": 2500, "y_max": 19500,
}

# TAV-05S page dimensions (from registry)
TAV05S_WIDTH_MM = 594.0
TAV05S_HEIGHT_MM = 1061.0
TAV05S_WIDTH_PTS = 1683.7
TAV05S_HEIGHT_PTS = 2987.3


def dxf_to_pdf_coords(dxf_x: float, dxf_y: float) -> tuple[float, float]:
    """Convert DXF coordinates to PDF points (approximate mapping).
    
    This is an approximate affine transform. The DXF coordinate system
    has origin at lower-left, Y increases upward.
    PDF coordinate system has origin at top-left, Y increases downward.
    
    For accurate mapping, we'd need control points. For now, we use
    the known pillar positions as approximate anchors.
    """
    # Normalize DXF coords to [0,1] within terrace bounds
    nx = (dxf_x - DXF_TERRACE_BOUNDS["x_min"]) / (DXF_TERRACE_BOUNDS["x_max"] - DXF_TERRACE_BOUNDS["x_min"])
    ny = (dxf_y - DXF_TERRACE_BOUNDS["y_min"]) / (DXF_TERRACE_BOUNDS["y_max"] - DXF_TERRACE_BOUNDS["y_min"])

    # Map to PDF coords (plan area: top 85% of page)
    # X: left to right
    pdf_x = nx * TAV05S_WIDTH_PTS
    # Y: inverted (PDF Y=0 at top, DXF Y=0 at bottom of terrace)
    plan_height = TAV05S_HEIGHT_PTS * 0.85
    pdf_y = (1.0 - ny) * plan_height

    return round(pdf_x, 1), round(pdf_y, 1)


def generate_terrace_crops(pdf_path: str, output_dir: Path) -> list[dict]:
    """Generate evidence crops for the terrace region."""
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[0]
    w_pts, h_pts = page.get_size()

    DPI = 300
    scale = DPI / 72.0

    # Render full page at 300 DPI
    print("  Rendering full page at 300 DPI...")
    bitmap = page.render(scale=scale)
    img = bitmap.to_pil()
    page_w, page_h = img.size
    print(f"  Full page: {page_w}x{page_h} px")

    crops = []

    # 1. Terrace region overview (upper-right quadrant)
    print("  Generating terrace overview crop...")
    terrace_bbox_pdf = (w_pts * 0.45, 0, w_pts, h_pts * 0.65)
    terrace_px = tuple(int(c * scale) for c in terrace_bbox_pdf)
    terrace_crop = img.crop(terrace_px)
    terrace_path = output_dir / "EV_TERRACE_overview.png"
    terrace_crop.save(str(terrace_path), "PNG")
    crops.append({
        "evidence_id": "EV-TERRACE-OVERVIEW",
        "description": "Terrace region overview",
        "crop_path": str(terrace_path),
        "bbox_native": list(terrace_bbox_pdf),
        "bbox_normalized": [0.45, 0.0, 1.0, 0.65],
        "pixel_bbox": list(terrace_px),
    })

    # 2. Cartiglio (title block)
    print("  Generating cartiglio crop...")
    cart_bbox_pdf = (0, h_pts * 0.86, w_pts, h_pts)
    cart_px = tuple(int(c * scale) for c in cart_bbox_pdf)
    cart_crop = img.crop(cart_px)
    cart_path = output_dir / "EV_CARTIGLIO.png"
    cart_crop.save(str(cart_path), "PNG")
    crops.append({
        "evidence_id": "EV-CARTIGLIO",
        "description": "Title block / cartiglio",
        "crop_path": str(cart_path),
        "bbox_native": list(cart_bbox_pdf),
        "bbox_normalized": [0.0, 0.86, 1.0, 1.0],
        "pixel_bbox": list(cart_px),
    })

    # 3. Level label (from DXF: S-TEXT-E layer text near top)
    print("  Generating level label crop...")
    level_bbox_pdf = (0, 0, w_pts * 0.5, h_pts * 0.05)
    level_px = tuple(int(c * scale) for c in level_bbox_pdf)
    level_crop = img.crop(level_px)
    level_path = output_dir / "EV_LEVEL_LABEL.png"
    level_crop.save(str(level_path), "PNG")
    crops.append({
        "evidence_id": "EV-LEVEL-LABEL",
        "description": "Level/impalcato label",
        "crop_path": str(level_path),
        "bbox_native": list(level_bbox_pdf),
        "bbox_normalized": [0.0, 0.0, 0.5, 0.05],
        "pixel_bbox": list(level_px),
    })

    # 4. Pillar crops (N002, N005, N039, N041)
    pillar_crops_px = 400  # pixels around each pillar
    for pillar_id, info in TERRACE_PILLARS.items():
        print(f"  Generating pillar crop: {pillar_id} ({info['status']})...")
        pdf_x, pdf_y = dxf_to_pdf_coords(info["x_mm"], info["y_mm"])

        # Center crop around pillar position
        half = pillar_crops_px / 2 / scale  # convert px to PDF pts
        crop_x0 = max(0, pdf_x - half)
        crop_y0 = max(0, pdf_y - half)
        crop_x1 = min(w_pts, pdf_x + half)
        crop_y1 = min(h_pts, pdf_y + half)

        crop_px = (
            int(crop_x0 * scale), int(crop_y0 * scale),
            int(crop_x1 * scale), int(crop_y1 * scale),
        )
        pillar_crop = img.crop(crop_px)

        status_tag = "CANDIDATE" if pillar_id == "N041" else "CONFIRMED"
        pillar_path = output_dir / f"EV_PILLAR_{pillar_id}_{status_tag}.png"
        pillar_crop.save(str(pillar_path), "PNG")

        crops.append({
            "evidence_id": f"EV-PILLAR-{pillar_id}",
            "description": f"Pillar {pillar_id} annotation ({info['status']}, {status_tag})",
            "crop_path": str(pillar_path),
            "dxf_handle": pillar_id,
            "dxf_status": info["status"],
            "dxf_verify": info["verify"],
            "dxf_type": info["type"],
            "identity_status": status_tag,
            "bbox_native": [round(crop_x0, 1), round(crop_y0, 1), round(crop_x1, 1), round(crop_y1, 1)],
            "bbox_normalized": [
                round(crop_x0 / w_pts, 6), round(crop_y0 / h_pts, 6),
                round(crop_x1 / w_pts, 6), round(crop_y1 / h_pts, 6),
            ],
            "pixel_bbox": list(crop_px),
        })

    # 5. Dimension annotations (3 representative)
    dim_regions = [
        ("EV-DIM-01", "Dimension annotation 1", (w_pts * 0.3, h_pts * 0.15, w_pts * 0.5, h_pts * 0.25)),
        ("EV-DIM-02", "Dimension annotation 2", (w_pts * 0.6, h_pts * 0.1, w_pts * 0.8, h_pts * 0.2)),
        ("EV-DIM-03", "Dimension annotation 3", (w_pts * 0.1, h_pts * 0.3, w_pts * 0.35, h_pts * 0.4)),
    ]
    for dim_id, dim_desc, dim_bbox in dim_regions:
        print(f"  Generating dimension crop: {dim_id}...")
        dim_px = tuple(int(c * scale) for c in dim_bbox)
        dim_crop = img.crop(dim_px)
        dim_path = output_dir / f"{dim_id}.png"
        dim_crop.save(str(dim_path), "PNG")
        crops.append({
            "evidence_id": dim_id,
            "description": dim_desc,
            "crop_path": str(dim_path),
            "bbox_native": list(dim_bbox),
            "bbox_normalized": [
                round(dim_bbox[0] / w_pts, 6), round(dim_bbox[1] / h_pts, 6),
                round(dim_bbox[2] / w_pts, 6), round(dim_bbox[3] / h_pts, 6),
            ],
            "pixel_bbox": list(dim_px),
        })

    # 6. Beam labels (3 representative from corridor)
    beam_regions = [
        ("EV-BEAM-01", "Beam label in N002-N005 corridor", (w_pts * 0.55, h_pts * 0.25, w_pts * 0.75, h_pts * 0.35)),
        ("EV-BEAM-02", "Beam label near N005", (w_pts * 0.5, h_pts * 0.35, w_pts * 0.7, h_pts * 0.45)),
        ("EV-BEAM-03", "Beam label near N039", (w_pts * 0.4, h_pts * 0.5, w_pts * 0.6, h_pts * 0.6)),
    ]
    for beam_id, beam_desc, beam_bbox in beam_regions:
        print(f"  Generating beam crop: {beam_id}...")
        beam_px = tuple(int(c * scale) for c in beam_bbox)
        beam_crop = img.crop(beam_px)
        beam_path = output_dir / f"{beam_id}.png"
        beam_crop.save(str(beam_path), "PNG")
        crops.append({
            "evidence_id": beam_id,
            "description": beam_desc,
            "crop_path": str(beam_path),
            "bbox_native": list(beam_bbox),
            "bbox_normalized": [
                round(beam_bbox[0] / w_pts, 6), round(beam_bbox[1] / h_pts, 6),
                round(beam_bbox[2] / w_pts, 6), round(beam_bbox[3] / h_pts, 6),
            ],
            "pixel_bbox": list(beam_px),
        })

    pdf.close()
    return crops


def main():
    print("=" * 60)
    print("TASK 5: TERRACE PROBE — EVIDENCE CROPS")
    print("=" * 60)

    # Load registry to get TAV-05S
    documents = load_registry()
    target_doc = None
    for doc in documents:
        if doc.document_id == "TAV-05S":
            target_doc = doc
            break

    if not target_doc:
        print("FATAL: TAV-05S not found")
        sys.exit(1)

    print(f"\nSource: {target_doc.file_path}")
    print(f"Size: {target_doc.page_width_mm:.0f}x{target_doc.page_height_mm:.0f}mm")

    # Generate evidence crops
    crop_dir = CROPS_DIR / "terrace_evidence"
    crops = generate_terrace_crops(target_doc.file_path, crop_dir)

    # Save crops manifest
    manifest_path = crop_dir / "evidence_crops.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(crops, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n--- Summary ---")
    print(f"  Evidence crops generated: {len(crops)}")
    print(f"  Output directory: {crop_dir}")

    # Categorize
    categories = {}
    for c in crops:
        cat = c["evidence_id"].split("-")[1] if "-" in c["evidence_id"] else "OTHER"
        categories[cat] = categories.get(cat, 0) + 1
    print(f"  Categories: {categories}")

    # Verify all crops exist
    missing = [c for c in crops if not Path(c["crop_path"]).exists()]
    if missing:
        print(f"  WARNING: {len(missing)} missing crops!")
    else:
        print(f"  All crops verified: OK")

    return crops


if __name__ == "__main__":
    crops = main()
    print(f"\nDONE: {len(crops)} evidence crops generated")
