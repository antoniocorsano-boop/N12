#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any

import build_cew_managed_f3_assets as managed_f3_builder

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_professional_workbench_geometry"
MANIFEST = ASSET_ROOT / "manifest.json"
CONTRACT = ROOT / "automation/CEW_DUAL_VECTOR_AGREEMENT_CONTRACT_v1.json"
EVIDENCE_REGISTRY = ROOT / "data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
REQUIRED_SOURCES = ("TAV-05A", "TAV-06A", "TAV-05S", "TAV-06S")
PYMUPDF_BUILD_VERSION = "1.28.2"
DOCLING_PARSE_BUILD_VERSION = "7.16.0"
PDF_PAGE_NO = 1


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_revision() -> str:
    env = os.getenv("RENDER_GIT_COMMIT") or os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA")
    if env:
        return env.strip()
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _governed_regions(source_version_id: str) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    for row in _rows(EVIDENCE_REGISTRY):
        if row.get("source_version_id", "").strip() != source_version_id:
            continue
        if row.get("readiness_state", "").strip() != "READY":
            continue
        if row.get("geometry_type", "").strip() != "BBOX":
            raise AssertionError(f"unsupported governed EvidenceRegion geometry: {row.get('evidence_region_id')}")
        if row.get("coordinate_space", "").strip() != "NORMALIZED_0_1":
            raise AssertionError(f"unsupported governed EvidenceRegion coordinate space: {row.get('evidence_region_id')}")
        x = float(row["x"])
        y = float(row["y"])
        width = float(row["width"])
        height = float(row["height"])
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1.000001 or y + height > 1.000001:
            raise AssertionError(f"EvidenceRegion outside normalized page bounds: {row['evidence_region_id']}")
        regions.append(
            {
                "evidence_region_id": row["evidence_region_id"].strip(),
                "reference_item": row["reference_item"].strip(),
                "source_version_id": source_version_id,
                "page_id": row["page_id"].strip(),
                "transform_id": row["transform_id"].strip(),
                "coordinate_space": "NORMALIZED_0_1",
                "bbox_normalized": {"x": x, "y": y, "width": width, "height": height},
                "readiness_state": "READY",
                "localization_basis": row.get("localization_basis", "").strip(),
            }
        )
    return sorted(regions, key=lambda item: item["evidence_region_id"])


def build_plan() -> dict[str, Any]:
    f3_plan = managed_f3_builder.build_plan()
    sources: list[dict[str, Any]] = []
    for item in f3_plan["sources"]:
        if item["source_code"] not in REQUIRED_SOURCES:
            continue
        source = dict(item)
        source["evidence_regions"] = _governed_regions(source["source_version_id"])
        sources.append(source)
    if {source["source_code"] for source in sources} != set(REQUIRED_SOURCES):
        raise AssertionError("document-geometry source coverage must be exactly 4/4")
    region_ids = [region["evidence_region_id"] for source in sources for region in source["evidence_regions"]]
    if len(region_ids) != len(set(region_ids)):
        raise AssertionError("EvidenceRegion identity must be unique across document-geometry build plan")
    return {
        "schema_version": "1.1",
        "artifact_contract": "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1",
        "build_revision": build_revision(),
        "archive_commit": f3_plan["archive_commit"],
        "pdf_page_no": PDF_PAGE_NO,
        "comparison_scope": "GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE",
        "page_level_role": "DIAGNOSTIC_ONLY",
        "extractor_environment": "EPHEMERAL_BUILD_ONLY",
        "extractor_pins": {
            "pymupdf": PYMUPDF_BUILD_VERSION,
            "docling_parse": DOCLING_PARSE_BUILD_VERSION,
        },
        "sources": sources,
        "governed_region_count": len(region_ids),
        "runtime_docling_required": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _segment_overlaps_bbox(segment: Any, bbox: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = bbox
    sx0 = min(float(segment.x1), float(segment.x2))
    sx1 = max(float(segment.x1), float(segment.x2))
    sy0 = min(float(segment.y1), float(segment.y2))
    sy1 = max(float(segment.y1), float(segment.y2))
    return sx1 >= x0 and sx0 <= x1 and sy1 >= y0 and sy0 <= y1


def _filter_segments(segments: list[Any], bbox: tuple[float, float, float, float]) -> list[Any]:
    return [segment for segment in segments if _segment_overlaps_bbox(segment, bbox)]


def _comparison(dual: Any, reference: list[Any], candidate: list[Any], tol: dict[str, float]) -> dict[str, Any]:
    segments = dual.match_segments(reference, candidate, tol)
    ref_intersections = dual.unique_intersections(reference, tol["intersection_distance_pt"])
    cand_intersections = dual.unique_intersections(candidate, tol["intersection_distance_pt"])
    intersections = dual.match_points(ref_intersections, cand_intersections, tol["intersection_distance_pt"])
    outcome = dual.classify_outcome(segments["match_ratio"], intersections["match_ratio"], tol)
    effective_ratio = min(segments["match_ratio"], intersections["match_ratio"]) if intersections["match_ratio"] > 0 else segments["match_ratio"]
    return {
        "outcome": outcome,
        "effective_match_ratio": effective_ratio,
        "segments": segments,
        "intersections": intersections,
    }


def _select_region_mapping(
    dual: Any,
    py_all: list[Any],
    dp_all: list[Any],
    page_height: float,
    bbox: tuple[float, float, float, float],
    tol: dict[str, float],
) -> tuple[str, list[Any], list[Any], dict[str, Any], dict[str, Any]]:
    reference = _filter_segments(py_all, bbox)
    direct_candidate = _filter_segments(dp_all, bbox)
    flipped_all = [segment.flipped_y(page_height) for segment in dp_all]
    flipped_candidate = _filter_segments(flipped_all, bbox)
    direct = _comparison(dual, reference, direct_candidate, tol)
    flipped = _comparison(dual, reference, flipped_candidate, tol)
    rank = {"DISAGREE": 0, "PARTIAL": 1, "AGREE": 2}

    def score(result: dict[str, Any]) -> tuple[float, float, int, float]:
        median = result["segments"].get("median_endpoint_error_pt")
        return (
            float(rank[result["outcome"]]),
            float(result["effective_match_ratio"]),
            len(result["segments"]["matches"]),
            -float(median if median is not None else 1e12),
        )

    if score(flipped) > score(direct):
        return "DOCLING_VERTICAL_FLIP", reference, flipped_candidate, flipped, {
            "DIRECT": {"outcome": direct["outcome"], "effective_match_ratio": direct["effective_match_ratio"]},
            "DOCLING_VERTICAL_FLIP": {"outcome": flipped["outcome"], "effective_match_ratio": flipped["effective_match_ratio"]},
        }
    return "DIRECT", reference, direct_candidate, direct, {
        "DIRECT": {"outcome": direct["outcome"], "effective_match_ratio": direct["effective_match_ratio"]},
        "DOCLING_VERTICAL_FLIP": {"outcome": flipped["outcome"], "effective_match_ratio": flipped["effective_match_ratio"]},
    }


def _document_objects(
    *,
    source: dict[str, Any],
    region: dict[str, Any],
    mapping: str,
    reference: list[Any],
    comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    if comparison["outcome"] != "AGREE":
        return []
    objects: list[dict[str, Any]] = []
    for match in comparison["segments"]["matches"]:
        ref = reference[int(match["reference_index"])]
        object_id = stable_id(
            "DGP",
            source["source_version_id"],
            region["evidence_region_id"],
            round(ref.x1, 6),
            round(ref.y1, 6),
            round(ref.x2, 6),
            round(ref.y2, 6),
        )
        objects.append(
            {
                "object_id": object_id,
                "object_family": "DocumentGraphicPrimitive",
                "coordinate_space": "SOURCE_PAGE_PT",
                "authority_state": "DERIVED_DUAL_VECTOR_CORROBORATION",
                "selection_authorized": True,
                "technical_identity_authorized": False,
                "geometry": {
                    "type": "LINE",
                    "a": [round(ref.x1, 6), round(ref.y1, 6)],
                    "b": [round(ref.x2, 6), round(ref.y2, 6)],
                },
                "properties": {
                    "source_kind": ref.kind,
                    "length_pt": round(ref.length, 6),
                    "angle_deg": round(ref.angle_deg, 6),
                    "agreement": {
                        "endpoint_error_pt": match["endpoint_error_pt"],
                        "angle_error_deg": match["angle_error_deg"],
                        "relative_length_error": match["relative_length_error"],
                    },
                },
                "provenance": {
                    "source_id": source["source_id"],
                    "source_version_id": source["source_version_id"],
                    "source_sha256": source["sha256"],
                    "pdf_page_no": PDF_PAGE_NO,
                    "page_id": region["page_id"],
                    "evidence_region_id": region["evidence_region_id"],
                    "transform_id": region["transform_id"],
                    "coordinate_mapping": mapping,
                    "extractor_pair": ["PyMuPDF", "DoclingParse"],
                    "artifact_role": "CORROBORATED_CLAIM_SCOPED_DOCUMENT_GEOMETRY",
                },
                "canonical_write_authorized": False,
            }
        )
    return objects


def _artifact_payload(source: dict[str, Any], pdf: Path) -> dict[str, Any]:
    import cew_dual_vector_agreement as dual

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tol = contract["tolerance_profile"]
    py, py_width, py_height, py_version = dual.extract_pymupdf(pdf, PDF_PAGE_NO, tol["minimum_line_length_pt"])
    dp, dp_width, dp_height, dp_version = dual.extract_docling(pdf, PDF_PAGE_NO, tol["minimum_line_length_pt"])

    dimensions_comparable = (
        abs(py_width - dp_width) <= tol["endpoint_distance_pt"]
        and abs(py_height - dp_height) <= tol["endpoint_distance_pt"]
    )
    if dimensions_comparable:
        page_mapping, dp_mapped, page_segments = dual.choose_coordinate_mapping(py, dp, py_height, tol)
        page_py_intersections = dual.unique_intersections(py, tol["intersection_distance_pt"])
        page_dp_intersections = dual.unique_intersections(dp_mapped, tol["intersection_distance_pt"])
        page_intersections = dual.match_points(page_py_intersections, page_dp_intersections, tol["intersection_distance_pt"])
        page_outcome = dual.classify_outcome(page_segments["match_ratio"], page_intersections["match_ratio"], tol)
    else:
        page_mapping = None
        page_outcome = "UNCOMPARABLE"
        page_segments = {
            "matches": [],
            "match_ratio": 0.0,
            "reference_count": len(py),
            "candidate_count": len(dp),
            "unmatched_reference": len(py),
            "unmatched_candidate": len(dp),
            "median_endpoint_error_pt": None,
            "max_endpoint_error_pt": None,
        }
        page_intersections = {
            "reference_count": 0,
            "candidate_count": 0,
            "matches": 0,
            "match_ratio": 0.0,
            "median_error_pt": None,
            "max_error_pt": None,
        }

    region_results: list[dict[str, Any]] = []
    if dimensions_comparable:
        for region in source.get("evidence_regions", []):
            normalized = region["bbox_normalized"]
            bbox = (
                float(normalized["x"]) * py_width,
                float(normalized["y"]) * py_height,
                float(normalized["x"] + normalized["width"]) * py_width,
                float(normalized["y"] + normalized["height"]) * py_height,
            )
            mapping, reference, _candidate, comparison, mapping_candidates = _select_region_mapping(
                dual, py, dp, py_height, bbox, tol
            )
            objects = _document_objects(
                source=source,
                region=region,
                mapping=mapping,
                reference=reference,
                comparison=comparison,
            )
            region_results.append(
                {
                    "evidence_region_id": region["evidence_region_id"],
                    "reference_item": region["reference_item"],
                    "page_id": region["page_id"],
                    "transform_id": region["transform_id"],
                    "coordinate_space": region["coordinate_space"],
                    "bbox_normalized": normalized,
                    "bbox_source_pt": {
                        "x0": round(bbox[0], 6),
                        "y0": round(bbox[1], 6),
                        "x1": round(bbox[2], 6),
                        "y1": round(bbox[3], 6),
                    },
                    "coordinate_mapping": mapping,
                    "mapping_candidates": mapping_candidates,
                    "agreement_outcome": comparison["outcome"],
                    "effective_match_ratio": comparison["effective_match_ratio"],
                    "segment_metrics": comparison["segments"],
                    "intersection_metrics": comparison["intersections"],
                    "scene_materialization_authorized": comparison["outcome"] == "AGREE",
                    "objects": objects,
                    "unmatched_geometry_published": False,
                    "authority_state": "DERIVED_REVIEW_EVIDENCE",
                    "canonical_write_authorized": False,
                    "engineering_authority_effect": "NONE",
                }
            )

    payload: dict[str, Any] = {
        "schema_version": "1.1",
        "artifact_contract": "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1",
        "source_code": source["source_code"],
        "source_id": source["source_id"],
        "source_version_id": source["source_version_id"],
        "source_sha256": source["sha256"],
        "archive_commit": source["archive_commit"],
        "archive_path": source["archive_path"],
        "git_blob_sha": source["git_blob_sha"],
        "pdf_page_no": PDF_PAGE_NO,
        "page_size_pt": [py_width, py_height],
        "extractors": {"pymupdf": py_version, "docling_parse": dp_version},
        "tolerance_profile": tol,
        "page_diagnostic": {
            "role": "DIAGNOSTIC_ONLY_NOT_A_SCENE_MATERIALIZATION_GATE",
            "coordinate_mapping": page_mapping,
            "agreement_outcome": page_outcome,
            "segment_metrics": page_segments,
            "intersection_metrics": page_intersections,
        },
        "comparison_scope": "GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE",
        "regions": region_results,
        "governed_region_count": len(region_results),
        "agreed_region_count": sum(1 for region in region_results if region["agreement_outcome"] == "AGREE"),
        "region_object_count": sum(len(region["objects"]) for region in region_results),
        "unmatched_geometry_published": False,
        "authority_state": "DERIVED_REVIEW_EVIDENCE",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "guards": [
            "Page-level agreement is diagnostic only; scene publication is EvidenceRegion-scoped.",
            "Only an existing READY canonical EvidenceRegion can define claim-scoped comparison bounds.",
            "Agreement is corroboration of source geometry, not technical or structural identity.",
            "PARTIAL/DISAGREE/UNCOMPARABLE regions publish no scene geometry.",
            "Unmatched extractor geometry is never silently completed or promoted.",
            "Canonical engineering data cannot be mutated by this artifact.",
        ],
    }
    payload["artifact_content_sha256"] = digest_bytes(canonical_json(payload).encode("utf-8"))
    return payload


def _worker(pdf: Path, source_json: Path, out: Path) -> None:
    source = json.loads(source_json.read_text(encoding="utf-8"))
    actual = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if actual != source["sha256"]:
        raise AssertionError(
            f"immutable source digest mismatch for {source['source_code']}: expected={source['sha256']} actual={actual}"
        )
    payload = _artifact_payload(source, pdf)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _venv_python(root: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(root)
    if os.name == "nt":
        return root / "Scripts/python.exe"
    return root / "bin/python"


def _install_extractors(python: Path) -> None:
    subprocess.run(
        [
            str(python), "-m", "pip", "install", "--disable-pip-version-check",
            f"PyMuPDF=={PYMUPDF_BUILD_VERSION}",
            f"docling-parse=={DOCLING_PARSE_BUILD_VERSION}",
        ],
        cwd=ROOT,
        check=True,
    )


def _build_with_python(plan: dict[str, Any], python: Path, temp_root: Path) -> dict[str, Any]:
    managed_f3_builder._ensure_archive_commit(plan["archive_commit"])
    source_root = temp_root / "sources"
    source_root.mkdir(parents=True, exist_ok=True)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []

    for source in plan["sources"]:
        pdf = source_root / f"{source['source_code']}.pdf"
        managed_f3_builder._materialize_source(source, pdf)
        source_json = temp_root / f"{source['source_code']}.source.json"
        source_json.write_text(json.dumps(source), encoding="utf-8")
        out = ASSET_ROOT / f"{source['source_code']}_p001.document-geometry.json"
        subprocess.run(
            [str(python), str(Path(__file__).resolve()), "--worker", "--pdf", str(pdf), "--source-json", str(source_json), "--out", str(out)],
            cwd=ROOT,
            check=True,
        )
        artifact = json.loads(out.read_text(encoding="utf-8"))
        entries.append(
            {
                "source_code": source["source_code"],
                "source_id": source["source_id"],
                "source_version_id": source["source_version_id"],
                "source_sha256": source["sha256"],
                "pdf_page_no": PDF_PAGE_NO,
                "page_diagnostic_outcome": artifact["page_diagnostic"]["agreement_outcome"],
                "governed_region_count": artifact["governed_region_count"],
                "agreed_region_count": artifact["agreed_region_count"],
                "region_object_count": artifact["region_object_count"],
                "filename": out.name,
                "file_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "artifact_content_sha256": artifact["artifact_content_sha256"],
            }
        )
        pdf.unlink(missing_ok=True)

    manifest = {
        **plan,
        "entries": entries,
        "source_coverage": f"{len(entries)}/{len(REQUIRED_SOURCES)}",
        "agreed_region_count": sum(entry["agreed_region_count"] for entry in entries),
        "region_object_count": sum(entry["region_object_count"] for entry in entries),
        "build_state": "READY",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def build_assets(*, use_current_python: bool = False) -> dict[str, Any]:
    plan = build_plan()
    if ASSET_ROOT.exists():
        import shutil
        shutil.rmtree(ASSET_ROOT)

    with tempfile.TemporaryDirectory(prefix="cew-doc-geometry-") as temp_name:
        temp_root = Path(temp_name)
        if use_current_python:
            python = Path(sys.executable)
        else:
            env_root = temp_root / "extractor-venv"
            python = _venv_python(env_root)
            _install_extractors(python)
        manifest = _build_with_python(plan, python, temp_root)

    print("CEW_DOCUMENT_GEOMETRY_ARTIFACT_BUILD = PASS")
    print(f"BUILD_REVISION = {manifest['build_revision']}")
    print(f"SOURCE_COVERAGE = {manifest['source_coverage']}")
    print(f"GOVERNED_REGION_COUNT = {manifest['governed_region_count']}")
    print(f"AGREED_REGION_COUNT = {manifest['agreed_region_count']}")
    print(f"REGION_OBJECT_COUNT = {manifest['region_object_count']}")
    for entry in manifest["entries"]:
        print(
            f"{entry['source_code']} PAGE_DIAGNOSTIC={entry['page_diagnostic_outcome']} "
            f"regions={entry['governed_region_count']} agreed={entry['agreed_region_count']} objects={entry['region_object_count']}"
        )
        artifact = json.loads((ASSET_ROOT / entry["filename"]).read_text(encoding="utf-8"))
        for region in artifact["regions"]:
            print(
                f"REGION {region['evidence_region_id']} = {region['agreement_outcome']} "
                f"ratio={region['effective_match_ratio']:.6f} objects={len(region['objects'])} "
                f"mapping={region['coordinate_mapping']}"
            )
    print("PAGE_LEVEL_ROLE = DIAGNOSTIC_ONLY")
    print("EXTRACTOR_ENVIRONMENT = EPHEMERAL_BUILD_ONLY")
    print("RUNTIME_DOCLING_REQUIRED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-plan-only", action="store_true")
    parser.add_argument("--use-current-python", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--source-json", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.worker:
        if not args.pdf or not args.source_json or not args.out:
            raise SystemExit("--worker requires --pdf --source-json --out")
        _worker(args.pdf, args.source_json, args.out)
        return 0

    plan = build_plan()
    if args.validate_plan_only:
        print("CEW_DOCUMENT_GEOMETRY_BUILD_PLAN = PASS")
        print(f"BUILD_REVISION = {plan['build_revision']}")
        print(f"SOURCE_COVERAGE = {len(plan['sources'])}/{len(REQUIRED_SOURCES)}")
        print(f"GOVERNED_REGION_COUNT = {plan['governed_region_count']}")
        print(f"PYMUPDF_BUILD_VERSION = {PYMUPDF_BUILD_VERSION}")
        print(f"DOCLING_PARSE_BUILD_VERSION = {DOCLING_PARSE_BUILD_VERSION}")
        print("COMPARISON_SCOPE = GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE")
        print("PAGE_LEVEL_ROLE = DIAGNOSTIC_ONLY")
        print("EXTRACTOR_ENVIRONMENT = EPHEMERAL_BUILD_ONLY")
        print("RUNTIME_DOCLING_REQUIRED = false")
        print("CANONICAL_WRITE_AUTHORIZED = false")
        return 0

    build_assets(use_current_python=args.use_current_python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
