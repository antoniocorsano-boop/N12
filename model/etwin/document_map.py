"""
Task 3: Adaptive Document Map Generator
Generates semantic regions and adaptive tile grids for any PDF page.
Uses pypdfium2 for rendering. Tiles have deterministic overlap.
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import pypdfium2 as pdfium
from PIL import Image

from model.etwin.document_engine import (
    OriginalDocument, DocumentMap, SemanticRegion, Tile, GeometricCoords,
    BBoxNative, BBoxNormalized, PixelCoords, SemanticRegionType, TileReadStatus,
    save_json
)
from model.etwin.document_registry import load_registry

CROPS_DIR = Path("docs") / "FOGLIO_LAVORO" / "etwin_crops"


def create_semantic_regions(doc: OriginalDocument) -> list[SemanticRegion]:
    """Define semantic regions for a carpenteria structural drawing.
    These are heuristics based on typical Italian structural drawing layout."""
    regions = []
    w = doc.page_width_pts
    h = doc.page_height_pts

    cartiglio_h = h * 0.14
    regions.append(SemanticRegion(
        region_id=f"R-{doc.document_id}-TITLE",
        document_id=doc.document_id,
        page_number=1,
        region_type=SemanticRegionType.TITLE_BLOCK,
        label="Cartiglio",
        coords=GeometricCoords(
            bbox_native=BBoxNative(0, h - cartiglio_h, w, h),
            bbox_normalized=BBoxNormalized(0, 0.86, 1.0, 1.0),
        ),
    ))

    plan_h = h * 0.85
    regions.append(SemanticRegion(
        region_id=f"R-{doc.document_id}-PLAN",
        document_id=doc.document_id,
        page_number=1,
        region_type=SemanticRegionType.PLAN,
        label="Pianta strutturale",
        coords=GeometricCoords(
            bbox_native=BBoxNative(0, 0, w, plan_h),
            bbox_normalized=BBoxNormalized(0, 0, 1.0, 0.85),
        ),
    ))

    return regions


def generate_adaptive_tiles(
    region: SemanticRegion,
    dpi: int = 300,
    target_tile_px: int = 2000,
    overlap_fraction: float = 0.10,
    max_subdivisions: int = 3,
) -> list[Tile]:
    """Generate adaptive tile grid for a semantic region."""
    tiles = []
    bbox = region.coords.bbox_native

    scale = dpi / 72.0
    region_px_w = int(bbox.width * scale)
    region_px_h = int(bbox.height * scale)

    cols = max(1, (region_px_w + target_tile_px - 1) // target_tile_px)
    rows = max(1, (region_px_h + target_tile_px - 1) // target_tile_px)

    tile_w_pts = bbox.width / cols
    tile_h_pts = bbox.height / rows

    overlap_x = tile_w_pts * overlap_fraction
    overlap_y = tile_h_pts * overlap_fraction

    tile_idx = 0
    for row in range(rows):
        for col in range(cols):
            x0 = bbox.x0 + col * tile_w_pts - (overlap_x if col > 0 else 0)
            y0 = bbox.y0 + row * tile_h_pts - (overlap_y if row > 0 else 0)
            x1 = bbox.x0 + (col + 1) * tile_w_pts + (overlap_x if col < cols - 1 else 0)
            y1 = bbox.y0 + (row + 1) * tile_h_pts + (overlap_y if row < rows - 1 else 0)

            x0 = max(x0, bbox.x0)
            y0 = max(y0, bbox.y0)
            x1 = min(x1, bbox.x1)
            y1 = min(y1, bbox.y1)

            px_x = int((x0 - bbox.x0) * scale)
            px_y = int((y0 - bbox.y0) * scale)
            px_w = int((x1 - x0) * scale)
            px_h = int((y1 - y0) * scale)

            tile = Tile(
                tile_id=f"T-{region.region_id}-{tile_idx:02d}",
                region_id=region.region_id,
                document_id=region.document_id,
                page_number=region.page_number,
                coords=GeometricCoords(
                    bbox_native=BBoxNative(round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)),
                    bbox_normalized=BBoxNormalized(
                        round((x0 - bbox.x0) / bbox.width, 6),
                        round((y0 - bbox.y0) / bbox.height, 6),
                        round((x1 - bbox.x0) / bbox.width, 6),
                        round((y1 - bbox.y0) / bbox.height, 6),
                    ),
                    pixel_coords=PixelCoords(px_x, px_y, px_w, px_h, dpi),
                ),
                overlap_fraction=overlap_fraction,
            )
            tiles.append(tile)
            tile_idx += 1

    return tiles


def render_tile(pdf_path: str, tile: Tile, output_dir: Path) -> Path:
    """Render a single tile from PDF and save as PNG."""
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[0]

    dpi = tile.coords.pixel_coords.dpi
    scale = dpi / 72.0

    bitmap = page.render(scale=scale)
    img = bitmap.to_pil()

    px = tile.coords.pixel_coords
    crop = img.crop((px.x, px.y, px.x + px.width, px.y + px.height))

    output_dir.mkdir(parents=True, exist_ok=True)
    tile_path = output_dir / f"{tile.tile_id}.png"
    crop.save(str(tile_path), "PNG")

    pdf.close()
    return tile_path


def build_document_map(
    doc: OriginalDocument,
    dpi: int = 300,
    target_tile_px: int = 2000,
    overlap_fraction: float = 0.10,
    render_tiles: bool = True,
) -> DocumentMap:
    """Build complete DocumentMap for a document."""
    print(f"\n--- Building DocumentMap for {doc.document_id} ---")

    regions = create_semantic_regions(doc)
    print(f"  Semantic regions: {len(regions)}")
    for r in regions:
        print(f"    {r.region_id}: {r.region_type.value} ({r.label})")

    all_tiles = []
    for region in regions:
        tiles = generate_adaptive_tiles(region, dpi, target_tile_px, overlap_fraction)
        all_tiles.extend(tiles)
        print(f"  Tiles for {region.region_id}: {len(tiles)}")

    print(f"  Total tiles: {len(all_tiles)}")

    if render_tiles:
        pdf_path = doc.file_path
        tile_dir = CROPS_DIR / doc.document_id / "page1"
        print(f"  Rendering tiles to: {tile_dir}")

        for i, tile in enumerate(all_tiles):
            render_tile(pdf_path, tile, tile_dir)
            tile.read_status = TileReadStatus.NOT_READ
            if (i + 1) % 5 == 0 or i == len(all_tiles) - 1:
                print(f"    Rendered {i+1}/{len(all_tiles)} tiles")

    doc_map = DocumentMap(
        map_id=f"DM-{doc.document_id}-001",
        document_id=doc.document_id,
        version=1,
        regions=regions,
        tiles=all_tiles,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        notes=f"Generated at {dpi} DPI, tile size ~{target_tile_px}px, overlap {overlap_fraction*100:.0f}%",
    )

    return doc_map


def main():
    print("=" * 60)
    print("TASK 3: ADAPTIVE DOCUMENT MAP GENERATOR")
    print("=" * 60)

    documents = load_registry()

    target_doc = None
    for doc in documents:
        if doc.document_id == "TAV-05S":
            target_doc = doc
            break

    if not target_doc:
        print("FATAL: TAV-05S not found in registry")
        sys.exit(1)

    print(f"\nTarget: {target_doc.document_id} ({target_doc.discipline})")
    print(f"File: {target_doc.file_path}")
    print(f"Size: {target_doc.page_width_mm:.0f}x{target_doc.page_height_mm:.0f}mm")

    doc_map = build_document_map(
        target_doc,
        dpi=300,
        target_tile_px=2000,
        overlap_fraction=0.10,
        render_tiles=True,
    )

    map_dir = CROPS_DIR / target_doc.document_id
    map_path = map_dir / "document_map.json"
    save_json(doc_map, map_path)
    print(f"\nDocumentMap saved: {map_path}")

    print(f"\n--- Summary ---")
    print(f"  Document: {doc_map.document_id}")
    print(f"  Regions: {len(doc_map.regions)}")
    print(f"  Tiles: {len(doc_map.tiles)}")
    print(f"  Version: {doc_map.version}")

    return doc_map


if __name__ == "__main__":
    doc_map = main()
    print(f"\nDONE: DocumentMap with {len(doc_map.tiles)} tiles")
