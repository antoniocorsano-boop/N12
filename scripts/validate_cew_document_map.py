#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_document_map as dm
import cew_document_map_page as dm_page

MODEL = ROOT / "automation/CEW_DOCUMENT_MAP_MODEL_v1.json"
REGISTRY = ROOT / "data/canonical/CEW_DOCUMENT_MAP_REGISTRY_v1.json"
CANDIDATES = ROOT / "automation/CEW_DOCUMENT_FEATURE_CANDIDATES_v1.json"
ADOPTION = ROOT / "docs/MIGRATION/CEW_DOCINTEL_V0_ADOPTION_v1.md"
APP = ROOT / "app.py"


def fail(errors: list[str]) -> int:
    print("CEW_DOCUMENT_MAP = FAIL")
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def main() -> int:
    errors: list[str] = []
    for path in [MODEL, REGISTRY, CANDIDATES, ADOPTION, APP]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return fail(errors)

    model = json.loads(MODEL.read_text(encoding="utf-8"))
    maps = dm.maps()
    candidates_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))

    if model.get("validation_policy", {}).get("canonical_engineering_promotion") is not False:
        errors.append("DocumentMap model must prohibit canonical engineering promotion")
    if model.get("evidence_boundary", {}).get("document_feature_candidate_is_evidence_region") is not False:
        errors.append("candidate must not be an EvidenceRegion")
    if model.get("evidence_boundary", {}).get("validated_document_feature_is_evidence_region") is not False:
        errors.append("validated document feature must not automatically be an EvidenceRegion")

    if candidates_payload.get("candidates") != []:
        errors.append("initial B1.3 candidate registry must remain empty until actual candidates are produced")

    expected = {
        "TAV-05A": {
            "source_version_id": "CEW-N12-SRC-TAV05A-V17DEC414",
            "page_id": "CEW-N12-PAGE-TAV05A-P001",
            "evidence_regions": {"CEW-N12-REG-G01-R06", "CEW-N12-REG-G07-R07", "CEW-N12-REG-G05-R04"},
            "source_class": "armature_travi",
            "project_level": "G4",
        },
        "TAV-06A": {
            "source_version_id": "CEW-N12-SRC-TAV06A-V3F2D557F",
            "page_id": "CEW-N12-PAGE-TAV06A-P001",
            "evidence_regions": {"CEW-N12-REG-T6A-G03"},
            "source_class": "armature_copertura",
            "project_level": "G5_copertura",
        },
    }

    for source_id, exp in expected.items():
        row = maps.get(source_id)
        if not row:
            errors.append(f"missing DocumentMap {source_id}")
            continue
        if row.get("state") != "PARTIAL":
            errors.append(f"{source_id}: initial map must be PARTIAL")
        if row.get("source_version_id") != exp["source_version_id"] or row.get("page_id") != exp["page_id"]:
            errors.append(f"{source_id}: F1/F2 identity drift")
        if set(row.get("evidence_region_ids", [])) != exp["evidence_regions"]:
            errors.append(f"{source_id}: EvidenceRegion link drift")
        meta = row.get("registered_metadata", {})
        if meta.get("source_class") != exp["source_class"] or meta.get("project_level") != exp["project_level"]:
            errors.append(f"{source_id}: registered metadata drift")
        if meta.get("metadata_is_drawing_internal_reading") is not False:
            errors.append(f"{source_id}: registered metadata must not masquerade as drawing-internal reading")
        if row.get("validated_feature_ids") or row.get("candidate_feature_ids"):
            errors.append(f"{source_id}: initial map must not contain invented validated/candidate features")
        for required_unknown in ["DRAWING_TITLE", "DRAWING_SCALE", "READING_ORIENTATION", "EXPLODED_REINFORCEMENT_VIEW"]:
            if required_unknown not in row.get("unknown_fields", []):
                errors.append(f"{source_id}: {required_unknown} must remain UNKNOWN initially")

    invalid_direct_validation = {
        "candidate_id": "TEST-1",
        "source_version_id": "CEW-N12-SRC-TAV05A-V17DEC414",
        "page_id": "CEW-N12-PAGE-TAV05A-P001",
        "feature_type": "DRAWING_SCALE",
        "state": "VALIDATED",
        "detector_or_author": "machine-test",
        "created_at": "2026-08-28T00:00:00Z",
        "value_text": "1:50"
    }
    if "VALIDATED_REQUIRES_HUMAN_REVIEWER" not in dm.validate_candidate(invalid_direct_validation):
        errors.append("machine/direct VALIDATED candidate must fail without human reviewer")

    valid_candidate = {
        "candidate_id": "TEST-2",
        "source_version_id": "CEW-N12-SRC-TAV05A-V17DEC414",
        "page_id": "CEW-N12-PAGE-TAV05A-P001",
        "feature_type": "EXPLODED_REINFORCEMENT_VIEW",
        "state": "CANDIDATE",
        "detector_or_author": "docintel-test",
        "created_at": "2026-08-28T00:00:00Z",
        "bbox_normalized_0_1": [0.1, 0.2, 0.3, 0.4],
        "confidence": 0.8
    }
    if dm.validate_candidate(valid_candidate):
        errors.append(f"valid candidate rejected: {dm.validate_candidate(valid_candidate)}")

    bad_bbox = {**valid_candidate, "candidate_id": "TEST-3", "bbox_normalized_0_1": [0.9, 0.9, 0.2, 0.2]}
    if "BBOX_OUTSIDE_NORMALIZED_PAGE" not in dm.validate_candidate(bad_bbox):
        errors.append("out-of-page candidate bbox must fail closed")

    page = dm_page.build_page("TAV-05A")
    for marker in ["Document Map", "PARTIAL", "Nessun candidato OCR/vector/AI registrato", "Titolo della tavola", "Armature esplose", "non equivale a DOC"]:
        if marker.lower() not in page.lower():
            errors.append(f"DocumentMap UI missing marker: {marker}")

    app_text = APP.read_text(encoding="utf-8")
    for marker in [
        "import cew_document_map_page as document_map_page",
        '@app.get("/drawings/{source_id}/map"',
        '"document_map": "B13_PREP_AVAILABLE_NOT_PROMOTED"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime integration missing: {marker}")

    adoption_text = ADOPTION.read_text(encoding="utf-8")
    for marker in ["exp/cew-document-intelligence-foundation-v0", "SQLite", "does not become", "VALIDATED"]:
        if marker.lower() not in adoption_text.lower():
            errors.append(f"adoption contract missing: {marker}")

    if errors:
        return fail(errors)

    print("CEW_DOCUMENT_MAP = PASS")
    print("INITIAL_DOCUMENT_MAPS = TAV-05A,TAV-06A")
    print("INITIAL_MACHINE_CANDIDATES = 0")
    print("VALIDATED_REQUIRES_HUMAN_REVIEW = true")
    print("CANDIDATE_TO_EVIDENCE_REGION_AUTOMATIC = false")
    print("CANONICAL_ENGINEERING_PROMOTION = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
