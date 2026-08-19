"""ETW-2 Task 3: targeted G4/G3 evidence probe.

Renders only the two source sheets required by the first differential probe,
then crops identical normalized regions inherited from validated ETW-1 G4
evidence. No structural identity or property is promoted here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pypdfium2 as pdfium

from model.etwin.document_registry import load_registry

OUT_DIR = Path("docs") / "FOGLIO_LAVORO" / "etwin_crops" / "ETW-2" / "G4_G3_probe"
DPI = 300

# Reuse ETW-1 normalized evidence windows, not ad-hoc new regions.
REGIONS = {
    "TERRACE_OVERVIEW": (0.45, 0.00, 1.00, 0.65),
    "BEAM_01": (0.55, 0.25, 0.75, 0.35),
    "BEAM_02": (0.50, 0.35, 0.70, 0.45),
    "BEAM_03": (0.40, 0.50, 0.60, 0.60),
    "SLAB_TERRACE": (0.50, 0.05, 0.90, 0.30),
    "DETAIL_STRUCT": (0.35, 0.20, 0.65, 0.40),
}

LEVEL_DOCS = {
    "G3": "TAV-04S",
    "G4": "TAV-05S",
}


def render_page(doc, dpi: int = DPI):
    pdf = pdfium.PdfDocument(doc.file_path)
    page = pdf[0]
    scale = dpi / 72.0
    bitmap = page.render(scale=scale)
    image = bitmap.to_pil().copy()
    pdf.close()
    return image


def crop_normalized(image, bbox):
    x0, y0, x1, y1 = bbox
    w, h = image.size
    px = (
        round(x0 * w),
        round(y0 * h),
        round(x1 * w),
        round(y1 * h),
    )
    return image.crop(px), px


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = {d.document_id: d for d in load_registry()}

    manifest = {
        "schema": "ETW2-G4-G3-PROBE-1",
        "dpi": DPI,
        "identity_promotion": False,
        "property_promotion": False,
        "region_origin": "ETW-1 terrace evidence normalized bboxes",
        "levels": {},
        "regions": {},
    }

    for level, doc_id in LEVEL_DOCS.items():
        doc = registry[doc_id]
        image = render_page(doc)
        manifest["levels"][level] = {
            "document_id": doc_id,
            "source_path": doc.file_path,
            "sha256": doc.sha256,
            "page_pixels": list(image.size),
        }

        for region_id, bbox in REGIONS.items():
            crop, px = crop_normalized(image, bbox)
            filename = f"{region_id}_{level}_{doc_id}.png"
            output = OUT_DIR / filename
            crop.save(output, "PNG")
            manifest["regions"].setdefault(region_id, {
                "bbox_normalized": list(bbox),
                "crops": {},
            })
            manifest["regions"][region_id]["crops"][level] = {
                "path": output.as_posix(),
                "pixel_bbox": list(px),
                "crop_pixels": list(crop.size),
            }

    manifest_path = OUT_DIR / "probe_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"Probe manifest: {manifest_path}")


if __name__ == "__main__":
    main()
