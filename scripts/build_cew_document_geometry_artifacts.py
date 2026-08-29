#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
REQUIRED_SOURCES = ("TAV-05A", "TAV-06A", "TAV-05S", "TAV-06S")
PYMUPDF_BUILD_VERSION = "1.28.2"
DOCLING_PARSE_BUILD_VERSION = "7.16.0"
PAGE_NO = 1


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def build_revision() -> str:
    env = os.getenv("RENDER_GIT_COMMIT") or os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA")
    if env:
        return env.strip()
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def build_plan() -> dict[str, Any]:
    f3_plan = managed_f3_builder.build_plan()
    sources = [dict(source) for source in f3_plan["sources"] if source["source_code"] in REQUIRED_SOURCES]
    if {source["source_code"] for source in sources} != set(REQUIRED_SOURCES):
        raise AssertionError("document-geometry source coverage must be exactly 4/4")
    return {
        "schema_version": "1.0",
        "artifact_contract": "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1",
        "build_revision": build_revision(),
        "archive_commit": f3_plan["archive_commit"],
        "page": PAGE_NO,
        "extractor_environment": "EPHEMERAL_BUILD_ONLY",
        "extractor_pins": {
            "pymupdf": PYMUPDF_BUILD_VERSION,
            "docling_parse": DOCLING_PARSE_BUILD_VERSION,
        },
        "sources": sources,
        "runtime_docling_required": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _artifact_payload(source: dict[str, str], pdf: Path) -> dict[str, Any]:
    import cew_dual_vector_agreement as dual

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tol = contract["tolerance_profile"]
    py, py_width, py_height, py_version = dual.extract_pymupdf(pdf, PAGE_NO, tol["minimum_line_length_pt"])
    dp, dp_width, dp_height, dp_version = dual.extract_docling(pdf, PAGE_NO, tol["minimum_line_length_pt"])

    if abs(py_width - dp_width) > tol["endpoint_distance_pt"] or abs(py_height - dp_height) > tol["endpoint_distance_pt"]:
        outcome = "UNCOMPARABLE"
        mapping = None
        segment_result = {
            "matches": [],
            "match_ratio": 0.0,
            "reference_count": len(py),
            "candidate_count": len(dp),
            "unmatched_reference": len(py),
            "unmatched_candidate": len(dp),
            "median_endpoint_error_pt": None,
            "max_endpoint_error_pt": None,
        }
        intersection_result = {
            "reference_count": 0,
            "candidate_count": 0,
            "matches": 0,
            "match_ratio": 0.0,
            "median_error_pt": None,
            "max_error_pt": None,
        }
    else:
        mapping, dp_mapped, segment_result = dual.choose_coordinate_mapping(py, dp, py_height, tol)
        py_intersections = dual.unique_intersections(py, tol["intersection_distance_pt"])
        dp_intersections = dual.unique_intersections(dp_mapped, tol["intersection_distance_pt"])
        intersection_result = dual.match_points(py_intersections, dp_intersections, tol["intersection_distance_pt"])
        outcome = dual.classify_outcome(
            segment_result["match_ratio"], intersection_result["match_ratio"], tol
        )

    objects: list[dict[str, Any]] = []
    if outcome == "AGREE":
        for match in segment_result["matches"]:
            ref = py[match["reference_index"]]
            candidate_index = int(match["candidate_index"])
            object_id = stable_id(
                "DGP",
                source["source_version_id"],
                PAGE_NO,
                match["reference_index"],
                candidate_index,
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
                            "reference_index": int(match["reference_index"]),
                            "candidate_index": candidate_index,
                            "endpoint_error_pt": match["endpoint_error_pt"],
                            "angle_error_deg": match["angle_error_deg"],
                            "relative_length_error": match["relative_length_error"],
                        },
                    },
                    "provenance": {
                        "source_id": source["source_id"],
                        "source_version_id": source["source_version_id"],
                        "source_sha256": source["sha256"],
                        "page": PAGE_NO,
                        "coordinate_mapping": mapping,
                        "extractor_pair": ["PyMuPDF", "DoclingParse"],
                        "artifact_role": "CORROBORATED_DOCUMENT_GEOMETRY",
                    },
                    "canonical_write_authorized": False,
                }
            )

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_contract": "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1",
        "source_code": source["source_code"],
        "source_id": source["source_id"],
        "source_version_id": source["source_version_id"],
        "source_sha256": source["sha256"],
        "archive_commit": source["archive_commit"],
        "archive_path": source["archive_path"],
        "git_blob_sha": source["git_blob_sha"],
        "page": PAGE_NO,
        "page_size_pt": [py_width, py_height],
        "coordinate_mapping": mapping,
        "extractors": {
            "pymupdf": py_version,
            "docling_parse": dp_version,
        },
        "tolerance_profile": tol,
        "agreement_outcome": outcome,
        "segment_metrics": segment_result,
        "intersection_metrics": intersection_result,
        "scene_materialization_authorized": outcome == "AGREE",
        "objects": objects,
        "unmatched_geometry_published": False,
        "authority_state": "DERIVED_REVIEW_EVIDENCE",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "guards": [
            "Agreement is corroboration of source geometry, not structural identity.",
            "PARTIAL/DISAGREE/UNCOMPARABLE artifacts publish no scene geometry.",
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
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
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
        out = ASSET_ROOT / f"{source['source_code']}_p001.agreed-geometry.json"
        subprocess.run(
            [
                str(python),
                str(Path(__file__).resolve()),
                "--worker",
                "--pdf",
                str(pdf),
                "--source-json",
                str(source_json),
                "--out",
                str(out),
            ],
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
                "page": PAGE_NO,
                "agreement_outcome": artifact["agreement_outcome"],
                "scene_materialization_authorized": artifact["scene_materialization_authorized"],
                "object_count": len(artifact["objects"]),
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
    for entry in manifest["entries"]:
        print(
            f"{entry['source_code']} = {entry['agreement_outcome']} "
            f"objects={entry['object_count']} materialize={str(entry['scene_materialization_authorized']).lower()}"
        )
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
        print(f"PYMUPDF_BUILD_VERSION = {PYMUPDF_BUILD_VERSION}")
        print(f"DOCLING_PARSE_BUILD_VERSION = {DOCLING_PARSE_BUILD_VERSION}")
        print("EXTRACTOR_ENVIRONMENT = EPHEMERAL_BUILD_ONLY")
        print("RUNTIME_DOCLING_REQUIRED = false")
        print("CANONICAL_WRITE_AUTHORIZED = false")
        return 0

    build_assets(use_current_python=args.use_current_python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
