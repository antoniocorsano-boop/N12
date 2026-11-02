from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED, RENDER_DPI, _canonical_digest, _render_primary_pdf


FROZEN_SOURCE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"

STRUCTURAL_GRID_SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "TAV-01S",
        "path": "archive/documentazione_originaria/tavola1-2.pdf",
        "sha256": "abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8",
        "source_commit": FROZEN_SOURCE_COMMIT,
        "functional_role": "STRUCTURAL_GRID_PRIMARY_SOURCE",
        "document_class": "CARPENTERIA_STRUTTURALE",
    },
    {
        "source_id": "TAV-02S",
        "path": "archive/documentazione_originaria/tavola2-2.pdf",
        "sha256": "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f",
        "source_commit": FROZEN_SOURCE_COMMIT,
        "functional_role": "STRUCTURAL_GRID_PRIMARY_SOURCE",
        "document_class": "CARPENTERIA_STRUTTURALE",
    },
]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_source_registry(sources: Iterable[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = [dict(row) for row in (STRUCTURAL_GRID_SOURCES if sources is None else sources)]
    ids: set[str] = set()
    paths: set[str] = set()
    for row in rows:
        source_id = str(row.get("source_id") or "")
        path = str(row.get("path") or "")
        sha256 = str(row.get("sha256") or "")
        commit = str(row.get("source_commit") or "")
        if not source_id or not path or len(sha256) != 64 or commit != FROZEN_SOURCE_COMMIT:
            raise ValueError("CAL01_STRUCTURAL_GRID_SOURCE_REGISTRY_INVALID")
        if source_id in ids:
            raise ValueError("CAL01_STRUCTURAL_GRID_SOURCE_ID_DUPLICATE")
        if path in paths:
            raise ValueError("CAL01_STRUCTURAL_GRID_SOURCE_PATH_DUPLICATE")
        ids.add(source_id)
        paths.add(path)
    return rows


def build_structural_grid_manifest(renders: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in renders]
    by_id = {str(row.get("source_id") or ""): row for row in rows}
    sources: list[dict[str, Any]] = []
    for source in validate_source_registry():
        source_id = source["source_id"]
        render = by_id.get(source_id)
        if render is None:
            raise ValueError("CAL01_STRUCTURAL_GRID_RENDER_RECORD_MISSING")
        if str(render.get("source_sha256") or "") != source["sha256"]:
            raise ValueError("CAL01_STRUCTURAL_GRID_RENDER_SOURCE_DIGEST_DRIFT")
        if int(render.get("width_px") or 0) <= 0 or int(render.get("height_px") or 0) <= 0:
            raise ValueError("CAL01_STRUCTURAL_GRID_RENDER_FRAME_INVALID")
        sources.append(
            {
                **source,
                "raster": {
                    "path": str(render.get("raster_path") or ""),
                    "dpi": RENDER_DPI,
                    "width_px": int(render["width_px"]),
                    "height_px": int(render["height_px"]),
                    "pixel_sha256": str(render.get("pixel_sha256") or ""),
                    "png_sha256": str(render.get("png_sha256") or ""),
                },
                "primary_visual_validation_required": True,
                "fit_eligible": False,
            }
        )
    result = {
        "schema": "CEW_CAL01_STRUCTURAL_GRID_PRIMARY_SOURCES_v1",
        "program": "CEW-CAL-01",
        "source_commit": FROZEN_SOURCE_COMMIT,
        "source_count": len(sources),
        "sources": sources,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "primary_anchor_count": 0,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["manifest_digest"] = _canonical_digest(result)
    return result


def render_structural_grid_sources(*, source_repo: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    render_records: list[dict[str, Any]] = []
    for source in validate_source_registry():
        pdf_path = source_repo / source["path"]
        if not pdf_path.is_file():
            raise RuntimeError(f"CAL01_STRUCTURAL_GRID_SOURCE_MISSING:{source['source_id']}")
        actual_sha256 = _sha256_file(pdf_path)
        if actual_sha256 != source["sha256"]:
            raise RuntimeError(f"CAL01_STRUCTURAL_GRID_SOURCE_DIGEST_DRIFT:{source['source_id']}")
        raster_path = output_dir / f"{source['source_id']}-primary-300dpi.png"
        rendered = _render_primary_pdf(pdf_path, raster_path)
        render_records.append(
            {
                "source_id": source["source_id"],
                "source_sha256": actual_sha256,
                "raster_path": raster_path.name,
                "width_px": int(rendered["width_px"]),
                "height_px": int(rendered["height_px"]),
                "pixel_sha256": str(rendered["pixel_sha256"]),
                "png_sha256": str(rendered["png_sha256"]),
            }
        )
    manifest = build_structural_grid_manifest(render_records)
    (output_dir / "structural-grid-primary-sources.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Render frozen CEW-CAL-01 structural-grid primary sources")
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = render_structural_grid_sources(source_repo=Path(args.source_repo), output_dir=Path(args.output_dir))
    print(json.dumps({"source_count": manifest["source_count"], "manifest_digest": manifest["manifest_digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
