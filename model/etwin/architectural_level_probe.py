"""ETW architectural/elevation overview probe for physical-level binding.

Renders the architectural plans and elevation/section sources needed to map
human level terminology (ground floor, first level, sub-roof) to structural
impalcato IDs without inferring the correspondence from file numbering alone.

The outputs are documentary rasters only; no structural identity promotion.
"""
from __future__ import annotations

import json
from pathlib import Path

import pypdfium2 as pdfium

from model.etwin.document_registry import load_registry

OUT = Path("docs") / "FOGLIO_LAVORO" / "etwin_crops" / "architectural_level_probe"
DOC_IDS = ["TAV-01", "TAV-02", "TAV-03", "TAV-04", "TAV-05E", "TAV-06E"]
DPI = 150


def render(path: str, out_path: Path) -> tuple[int, int]:
    pdf = pdfium.PdfDocument(path)
    page = pdf[0]
    img = page.render(scale=DPI / 72.0).to_pil().convert("L")
    img.save(out_path, "PNG")
    size = img.size
    pdf.close()
    return size


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    docs = {d.document_id: d for d in load_registry()}
    rows = []
    for document_id in DOC_IDS:
        doc = docs[document_id]
        out_path = OUT / f"{document_id}_OVERVIEW_{DPI}DPI.png"
        width_px, height_px = render(doc.file_path, out_path)
        rows.append({
            "document_id": document_id,
            "discipline": doc.discipline,
            "source_path": doc.file_path,
            "sha256": doc.sha256,
            "dpi": DPI,
            "pixel_size": [width_px, height_px],
            "output": str(out_path),
            "interpretation_status": "REVIEW_REQUIRED",
            "identity_promotion": False,
        })
    manifest = {
        "schema": "ETW-ARCHITECTURAL-LEVEL-PROBE-1",
        "purpose": "Bind physical level terminology to documentary plan/elevation evidence before terrace structural identity resolution.",
        "documents": rows,
        "property_promotion": False,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
