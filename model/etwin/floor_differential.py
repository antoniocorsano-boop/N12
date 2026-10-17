"""
ETW-2: Floor Differential Reconstruction.

Applies the validated ETW-1 document engine to G1-G4 carpenteria sheets
without assuming a typical floor. Task 1-2 deliberately generate metadata
only: deterministic DocumentMaps and a common normalized registration frame.
High-resolution raster rendering is deferred to Task 3 and performed only for
homologous regions needed by the evidence sweep.

This module does not promote structural identities or write canonical
structural data.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from model.etwin.document_map import build_document_map
from model.etwin.document_registry import load_registry

CROPS_DIR = Path("docs") / "FOGLIO_LAVORO" / "etwin_crops"
ETW2_DIR = CROPS_DIR / "ETW-2"

LEVEL_DOCS = {
    "G1": "TAV-02S",
    "G2": "TAV-03S",
    "G3": "TAV-04S",
    "G4": "TAV-05S",
}

MAP_DPI = 300
TARGET_TILE_PX = 2000
OVERLAP_FRACTION = 0.10


def _json_ready(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    try:
        return asdict(obj)
    except TypeError:
        return obj


def prepare_floor_maps(render_tiles: bool = False) -> dict[str, dict]:
    """Build deterministic ETW DocumentMaps for G1-G4.

    Task 1-2 are metadata-only by default. Every level gets its own map from
    the original source PDF using the same geometric policy, but no tile PNGs
    are rendered until Task 3 requests an evidence region.
    """
    documents = {d.document_id: d for d in load_registry()}
    missing = [doc_id for doc_id in LEVEL_DOCS.values() if doc_id not in documents]
    if missing:
        raise RuntimeError(f"Missing source documents in verified registry: {missing}")

    result: dict[str, dict] = {}
    for level, doc_id in LEVEL_DOCS.items():
        doc = documents[doc_id]
        doc_map = build_document_map(
            doc,
            dpi=MAP_DPI,
            target_tile_px=TARGET_TILE_PX,
            overlap_fraction=OVERLAP_FRACTION,
            render_tiles=render_tiles,
        )

        level_dir = CROPS_DIR / doc_id
        level_dir.mkdir(parents=True, exist_ok=True)
        map_path = level_dir / "document_map.json"
        map_path.write_text(
            json.dumps(_json_ready(doc_map), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        result[level] = {
            "document_id": doc_id,
            "source_path": doc.file_path,
            "sha256": doc.sha256,
            "page_width_pts": doc.page_width_pts,
            "page_height_pts": doc.page_height_pts,
            "document_map": map_path.as_posix(),
            "dpi": MAP_DPI,
            "target_tile_px": TARGET_TILE_PX,
            "overlap_fraction": OVERLAP_FRACTION,
            "tile_rasterization": "DEFERRED_TO_TASK3",
            "regions": len(doc_map.regions),
            "tiles": len(doc_map.tiles),
        }
    return result


def build_floor_registration(map_summary: dict[str, dict]) -> dict:
    """Create the ETW-2 common comparison frame.

    Registration is normalized to each sheet's PLAN semantic region. G4 is a
    reference surface only: it is NOT declared a typical floor and no entity
    identity is inferred from spatial proximity.
    """
    return {
        "schema": "ETW2-FLOOR-REGISTRATION-1",
        "reference_level": "G4",
        "reference_role": "coordinate_registration_only",
        "typical_floor_assumption": False,
        "levels": map_summary,
        "coordinate_policy": {
            "primary": "PLAN_region_normalized_bbox",
            "native_preserved": True,
            "source_round_trip_required": True,
            "identity_from_proximity_forbidden": True,
        },
        "render_policy": {
            "task_1_2": "metadata_only",
            "task_3": "on_demand_homologous_region_tiles",
            "default_dpi": MAP_DPI,
            "escalation_dpi": 600,
        },
        "comparison_statuses": [
            "MATCH",
            "SECTION_CHANGE",
            "GEOMETRY_CHANGE",
            "ELEMENT_ADDED",
            "ELEMENT_REMOVED",
            "POSITION_SHIFT",
            "IDENTITY_UNRESOLVED",
            "UNREADABLE",
        ],
        "first_probe": {
            "pair": ["G4", "G3"],
            "documents": ["TAV-05S", "TAV-04S"],
            "objective": "one verified cross-level difference end-to-end",
            "status": "READY_FOR_EVIDENCE_SWEEP",
        },
    }


def main(render_tiles: bool = False) -> dict:
    ETW2_DIR.mkdir(parents=True, exist_ok=True)
    maps = prepare_floor_maps(render_tiles=render_tiles)
    registration = build_floor_registration(maps)
    output = ETW2_DIR / "floor_registration.json"
    output.write_text(
        json.dumps(registration, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"ETW-2 registration written: {output}")
    for level, info in maps.items():
        print(f"{level}: {info['document_id']} -> {info['tiles']} metadata tiles")
    print("Task 1-2 rendering policy: metadata only")
    print("First evidence sweep: G4/TAV-05S <-> G3/TAV-04S")
    return registration


if __name__ == "__main__":
    main(render_tiles=False)
