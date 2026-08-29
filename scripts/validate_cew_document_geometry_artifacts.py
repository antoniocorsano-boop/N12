#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import cew_professional_workbench_document_geometry as geometry


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_artifact(
    root: Path,
    source_code: str,
    source_version_id: str,
    source_sha256: str,
    *,
    region_outcome: str,
) -> dict:
    region_id = f"REG-{source_code}"
    objects = []
    if region_outcome == "AGREE":
        objects = [
            {
                "object_id": f"DGP-{source_code}",
                "object_family": "DocumentGraphicPrimitive",
                "coordinate_space": "SOURCE_PAGE_PT",
                "authority_state": "DERIVED_DUAL_VECTOR_CORROBORATION",
                "selection_authorized": True,
                "technical_identity_authorized": False,
                "geometry": {"type": "LINE", "a": [10.0, 20.0], "b": [30.0, 20.0]},
                "properties": {
                    "source_kind": "line",
                    "length_pt": 20.0,
                    "angle_deg": 0.0,
                    "agreement": {
                        "endpoint_error_pt": 0.1,
                        "angle_error_deg": 0.0,
                        "relative_length_error": 0.0,
                    },
                },
                "provenance": {
                    "source_id": f"SRC-{source_code}",
                    "source_version_id": source_version_id,
                    "source_sha256": source_sha256,
                    "pdf_page_no": 1,
                    "page_id": f"PAGE-{source_code}",
                    "evidence_region_id": region_id,
                    "transform_id": f"XFORM-{source_code}",
                    "coordinate_mapping": "DIRECT",
                    "extractor_pair": ["PyMuPDF", "DoclingParse"],
                    "artifact_role": "CORROBORATED_CLAIM_SCOPED_DOCUMENT_GEOMETRY",
                },
                "canonical_write_authorized": False,
            }
        ]
    region = {
        "evidence_region_id": region_id,
        "reference_item": f"REF-{source_code}",
        "page_id": f"PAGE-{source_code}",
        "transform_id": f"XFORM-{source_code}",
        "coordinate_space": "NORMALIZED_0_1",
        "bbox_normalized": {"x": 0.0, "y": 0.1, "width": 1.0, "height": 0.2},
        "bbox_source_pt": {"x0": 0.0, "y0": 20.0, "x1": 100.0, "y1": 60.0},
        "coordinate_mapping": "DIRECT",
        "mapping_candidates": {
            "DIRECT": {"outcome": region_outcome, "effective_match_ratio": 1.0 if region_outcome == "AGREE" else 0.85},
            "DOCLING_VERTICAL_FLIP": {"outcome": "DISAGREE", "effective_match_ratio": 0.0},
        },
        "agreement_outcome": region_outcome,
        "effective_match_ratio": 1.0 if region_outcome == "AGREE" else 0.85,
        "segment_metrics": {},
        "intersection_metrics": {},
        "scene_materialization_authorized": region_outcome == "AGREE",
        "objects": objects,
        "unmatched_geometry_published": False,
        "authority_state": "DERIVED_REVIEW_EVIDENCE",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    artifact = {
        "schema_version": "1.1",
        "artifact_contract": "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1",
        "source_code": source_code,
        "source_id": f"SRC-{source_code}",
        "source_version_id": source_version_id,
        "source_sha256": source_sha256,
        "archive_commit": "a" * 40,
        "archive_path": f"sources/{source_code}.pdf",
        "git_blob_sha": "b" * 40,
        "pdf_page_no": 1,
        "page_size_pt": [100.0, 200.0],
        "extractors": {"pymupdf": "1.28.2", "docling_parse": "7.16.0"},
        "tolerance_profile": {},
        "page_diagnostic": {
            "role": "DIAGNOSTIC_ONLY_NOT_A_SCENE_MATERIALIZATION_GATE",
            "coordinate_mapping": "DIRECT",
            "agreement_outcome": "DISAGREE",
            "segment_metrics": {},
            "intersection_metrics": {},
        },
        "comparison_scope": "GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE",
        "regions": [region],
        "governed_region_count": 1,
        "agreed_region_count": 1 if region_outcome == "AGREE" else 0,
        "region_object_count": len(objects),
        "unmatched_geometry_published": False,
        "authority_state": "DERIVED_REVIEW_EVIDENCE",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "guards": [],
    }
    artifact["artifact_content_sha256"] = hashlib.sha256(canonical_json(artifact).encode("utf-8")).hexdigest()
    path = root / f"{source_code}_p001.document-geometry.json"
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return {
        "source_code": source_code,
        "source_id": f"SRC-{source_code}",
        "source_version_id": source_version_id,
        "source_sha256": source_sha256,
        "pdf_page_no": 1,
        "page_diagnostic_outcome": "DISAGREE",
        "governed_region_count": 1,
        "agreed_region_count": artifact["agreed_region_count"],
        "region_object_count": len(objects),
        "filename": path.name,
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "artifact_content_sha256": artifact["artifact_content_sha256"],
    }


def build_fixture(root: Path, revision: str, partial_source: str | None = None) -> dict:
    entries = []
    for code in geometry.REQUIRED_SOURCES:
        version = f"SV-{code}"
        source_sha = hashlib.sha256(code.encode("utf-8")).hexdigest()
        outcome = "PARTIAL" if code == partial_source else "AGREE"
        entries.append(write_artifact(root, code, version, source_sha, region_outcome=outcome))
    manifest = {
        "schema_version": "1.1",
        "artifact_contract": "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1",
        "build_revision": revision,
        "archive_commit": "a" * 40,
        "pdf_page_no": 1,
        "comparison_scope": "GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE",
        "page_level_role": "DIAGNOSTIC_ONLY",
        "extractor_environment": "EPHEMERAL_BUILD_ONLY",
        "extractor_pins": {"pymupdf": "1.28.2", "docling_parse": "7.16.0"},
        "sources": [],
        "governed_region_count": 4,
        "runtime_docling_required": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "entries": entries,
        "source_coverage": "4/4",
        "agreed_region_count": sum(entry["agreed_region_count"] for entry in entries),
        "region_object_count": sum(entry["region_object_count"] for entry in entries),
        "build_state": "READY",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def rewrite_artifact_and_entry(root: Path, source_code: str, mutator) -> None:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(item for item in manifest["entries"] if item["source_code"] == source_code)
    artifact_path = root / entry["filename"]
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    mutator(data)
    data["artifact_content_sha256"] = hashlib.sha256(
        canonical_json({k: v for k, v in data.items() if k != "artifact_content_sha256"}).encode("utf-8")
    ).hexdigest()
    artifact_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    entry["file_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    entry["artifact_content_sha256"] = data["artifact_content_sha256"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    original_root = geometry.ASSET_ROOT
    original_manifest = geometry.MANIFEST
    original_revision = os.environ.get("RENDER_GIT_COMMIT")
    revision = "0123456789abcdef0123456789abcdef01234567"

    try:
        with tempfile.TemporaryDirectory(prefix="cew-doc-geometry-validator-") as tmp:
            root = Path(tmp)
            geometry.ASSET_ROOT = root
            geometry.MANIFEST = root / "manifest.json"
            os.environ["RENDER_GIT_COMMIT"] = revision

            manifest = build_fixture(root, revision)
            validated = geometry.validate_manifest()
            assert validated["source_coverage"] == "4/4"
            assert validated["governed_region_count"] == 4
            first = manifest["entries"][0]
            result = geometry.scene_objects(
                source_version_id=first["source_version_id"],
                source_sha256=first["source_sha256"],
                page=1,
                evidence_region_id=f"REG-{first['source_code']}",
            )
            assert result["state"] == "READY_AGREED_DOCUMENT_GEOMETRY"
            assert result["object_count"] == 1
            assert result["objects"][0]["technical_identity_authorized"] is False
            assert result["canonical_write_authorized"] is False
            print("PAGE_DISAGREE_REGION_AGREE_MATERIALIZATION = PASS")

            manifest = build_fixture(root, revision, partial_source="TAV-05A")
            first = next(entry for entry in manifest["entries"] if entry["source_code"] == "TAV-05A")
            result = geometry.scene_objects(
                source_version_id=first["source_version_id"],
                source_sha256=first["source_sha256"],
                page=1,
                evidence_region_id="REG-TAV-05A",
            )
            assert result["state"] == "NOT_MATERIALIZED_FAIL_CLOSED"
            assert result["objects"] == []
            print("PARTIAL_REGION_GEOMETRY_PUBLICATION = FORBIDDEN")

            build_fixture(root, revision)
            os.environ["RENDER_GIT_COMMIT"] = "f" * 40
            try:
                geometry.validate_manifest()
            except ValueError as exc:
                assert str(exc) == "DOCUMENT_GEOMETRY_RUNTIME_REVISION_MISMATCH"
            else:
                raise AssertionError("stale document geometry revision was accepted")
            print("STALE_DOCUMENT_GEOMETRY_REVISION = REJECTED")

            os.environ["RENDER_GIT_COMMIT"] = revision
            build_fixture(root, revision)
            rewrite_artifact_and_entry(
                root,
                "TAV-05A",
                lambda data: data["regions"][0]["objects"][0].__setitem__("technical_identity_authorized", True),
            )
            try:
                geometry.validate_manifest()
            except ValueError as exc:
                assert str(exc) == "DOCUMENT_GEOMETRY_TECHNICAL_IDENTITY_FORBIDDEN"
            else:
                raise AssertionError("document geometry was allowed to claim technical identity")
            print("DOCUMENT_GEOMETRY_TECHNICAL_IDENTITY = FORBIDDEN")

            build_fixture(root, revision)
            rewrite_artifact_and_entry(
                root,
                "TAV-05A",
                lambda data: data["regions"][0].__setitem__("unmatched_geometry_published", True),
            )
            try:
                geometry.validate_manifest()
            except ValueError as exc:
                assert str(exc) == "DOCUMENT_GEOMETRY_UNMATCHED_PUBLICATION_FORBIDDEN"
            else:
                raise AssertionError("unmatched extractor geometry was allowed into artifact")
            print("UNMATCHED_GEOMETRY_PUBLICATION = FORBIDDEN")

        module_text = Path(geometry.__file__).read_text(encoding="utf-8")
        assert "import docling" not in module_text.lower()
        print("RUNTIME_DOCLING_IMPORT = NONE")
        print("SOURCE_COVERAGE = 4/4")
        print("COMPARISON_SCOPE = GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE")
        print("PAGE_LEVEL_ROLE = DIAGNOSTIC_ONLY")
        print("CANONICAL_WRITE_AUTHORIZED = false")
        print("CEW_DOCUMENT_GEOMETRY_RUNTIME_GUARDS = PASS")
    finally:
        geometry.ASSET_ROOT = original_root
        geometry.MANIFEST = original_manifest
        if original_revision is None:
            os.environ.pop("RENDER_GIT_COMMIT", None)
        else:
            os.environ["RENDER_GIT_COMMIT"] = original_revision


if __name__ == "__main__":
    main()
