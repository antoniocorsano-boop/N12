from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "cew_docintel" / "cli.py"
IMPORTER = ROOT / "tools" / "cew_docintel" / "import_scan2dxf.py"
DEFAULT_MANIFEST = ROOT / "automation" / "CEW_TAV07_DOCINTEL_IMPORT_MANIFEST_v0.json"


def run(*args: str) -> str:
    return subprocess.run([sys.executable, *args], text=True, capture_output=True, check=True).stdout.strip()


def git_blob(path: Path) -> str:
    return subprocess.run(["git", "hash-object", str(path)], text=True, capture_output=True, check=True).stdout.strip()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    p = argparse.ArgumentParser(description="Import the pinned real TAV07 Scan2DXF pilot into generation-safe CEW Document Intelligence")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--geometry", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--metrics", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    manifest = load(a.manifest)
    source = manifest["source"]
    extraction = manifest["extraction_source"]
    artifacts = extraction["artifacts"]
    source_path = ROOT / source["path"]

    require(source_path.is_file(), f"source tile missing: {source_path}")
    require(source_path.stat().st_size == source["expected_bytes"], "source byte count drift")
    require(git_blob(source_path) == source["git_blob_sha"], "source git blob drift")
    for path, key in [(a.geometry, "geometry"), (a.text, "text"), (a.metrics, "metrics")]:
        require(path.is_file(), f"missing extraction artifact: {path}")
        require(git_blob(path) == artifacts[key]["git_blob_sha"], f"{key} extraction git blob drift")

    metrics = load(a.metrics)
    geometry = load(a.geometry)
    text = load(a.text)
    require(metrics["representative_tile"] == "r1_c3.jpg", "representative tile drift")
    tile_metric = next(x for x in metrics["tiles"] if x["tile"] == "r1_c3.jpg")
    require(tile_metric["width_px"] == source["native_width_px"], "native width drift")
    require(tile_metric["height_px"] == source["native_height_px"], "native height drift")
    require(len(geometry) == artifacts["geometry"]["expected_count"], "geometry count drift")
    require(len(text) == artifacts["text"]["expected_count"], "text count drift")
    require(tile_metric["line_count"] == len(geometry), "metrics/geometry count mismatch")
    require(tile_metric["ocr_candidate_count"] == len(text), "metrics/text count mismatch")

    run(str(CLI), "--db", str(a.db), "init")
    ingest = json.loads(run(str(CLI), "--db", str(a.db), "ingest", str(source_path), "--source-id", source["source_id"], "--label", source["label"]))
    sv = ingest["source_version_id"]
    metadata = json.dumps({
        "manifest": str(a.manifest.relative_to(ROOT)),
        "extraction_ref": extraction["ref"],
        "coordinate_system": extraction["coordinate_system"],
        "whole_drawing_metrics": manifest["whole_drawing_metrics"],
        "detailed_scope": manifest["import_policy"]["detailed_observation_scope"],
        "git_blobs": {k: v["git_blob_sha"] for k, v in artifacts.items()},
    }, ensure_ascii=False)
    generation = json.loads(run(str(CLI), "--db", str(a.db), "generation-start", "--source-version-id", sv, "--processor", extraction["processor"], "--processor-version", "v0.2", "--metadata", metadata))
    gid = generation["generation_id"]

    imported = json.loads(run(str(IMPORTER), "--db", str(a.db), "--source-version-id", sv, "--generation-id", gid, "--page", "1", "--geometry", str(a.geometry), "--text", str(a.text), "--detector", extraction["processor"]))
    require(imported["imported"] == len(geometry) + len(text), "imported observation count mismatch")
    run(str(CLI), "--db", str(a.db), "generation-succeed", gid)
    validation = json.loads(run(str(CLI), "--db", str(a.db), "validate"))
    require(validation["status"] == "PASS", "document intelligence validation failed")

    with sqlite3.connect(a.db) as c:
        c.row_factory = sqlite3.Row
        counts = {r["kind"]: r["n"] for r in c.execute('''SELECT o.kind,COUNT(*) n FROM observations o JOIN observation_generation_bindings b ON b.observation_id=o.id WHERE b.generation_id=? GROUP BY o.kind''',(gid,))}
        states = {r["state"]: r["n"] for r in c.execute('''SELECT o.state,COUNT(*) n FROM observations o JOIN observation_generation_bindings b ON b.observation_id=o.id WHERE b.generation_id=? GROUP BY o.state''',(gid,))}
        bbox = c.execute('''SELECT MIN(o.x0),MIN(o.y0),MAX(o.x1),MAX(o.y1) FROM observations o JOIN observation_generation_bindings b ON b.observation_id=o.id WHERE b.generation_id=?''',(gid,)).fetchone()
        current = c.execute('SELECT current_generation_id FROM source_version_processing WHERE source_version_id=?',(sv,)).fetchone()[0]

    require(counts.get("line") == 441 and counts.get("text") == 39, "kind counts incorrect")
    require(states == {"CANDIDATE": 480}, f"unexpected promotion state: {states}")
    require(current == gid, "successful import generation is not current")

    output = {
        "schema_version": "0.1.0",
        "work_item_id": "DOC-002",
        "status": "PASS",
        "source_id": source["source_id"],
        "source_version_id": sv,
        "source_sha256": ingest["sha256"],
        "source_git_blob_sha": source["git_blob_sha"],
        "processing_generation_id": gid,
        "coordinate_system": extraction["coordinate_system"],
        "detailed_observation_scope": manifest["import_policy"]["detailed_observation_scope"],
        "whole_drawing_metrics": manifest["whole_drawing_metrics"],
        "detailed_import": {
            "geometry_candidates": counts.get("line", 0),
            "text_candidates": counts.get("text", 0),
            "total": sum(counts.values()),
            "states": states,
            "native_bbox_union": list(bbox),
        },
        "rejected": 0,
        "canonical_promotion": "DISABLED",
        "millimetre_authority": "NOT_AUTHORIZED",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
