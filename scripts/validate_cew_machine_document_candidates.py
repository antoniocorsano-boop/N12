#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_machine_document_candidates as mc


def expect_error(payload: dict, reason: str, errors: list[str]):
    try:
        mc.normalize(payload)
    except ValueError as exc:
        if str(exc) != reason:
            errors.append(f"expected {reason}, got {exc}")
    else:
        errors.append(f"expected fail-closed {reason}")


def main() -> int:
    errors: list[str] = []

    base = {
        "source_version_id": "CEW-N12-SRC-TAV05A-V17DEC414",
        "page_id": "CEW-N12-PAGE-TAV05A-P001",
        "feature_type": "EXPLODED_REINFORCEMENT_VIEW",
        "state": "CANDIDATE",
        "detector_family": "MULTIMODAL_AI",
        "detector": "cew-doc-reader",
        "detector_version": "test-v1",
        "bbox_normalized_0_1": [0.05, 0.10, 0.90, 0.20],
        "value_text": "possible exploded reinforcement group",
        "confidence": 0.82,
        "source_basis": "synthetic validator fixture on registered Page identity",
        "detector_coordinate_space": "NORMALIZED_0_1"
    }
    candidate = mc.normalize(base)
    if candidate.get("state") != "CANDIDATE":
        errors.append("valid machine output must remain CANDIDATE")
    if candidate.get("human_review_required_for_validation") is not True:
        errors.append("machine candidate must require human review")
    for key in ["evidence_region_created", "structural_binding_created", "canonical_engineering_promotion"]:
        if candidate.get(key) is not False:
            errors.append(f"machine candidate illegally sets {key}")
    if not candidate.get("candidate_id", "").startswith("CEW-DOC-CAND-"):
        errors.append("deterministic candidate identity missing")

    supported = mc.normalize({**base, "detector_family":"INDEPENDENT_CONSENSUS", "detector":"lsd+hough", "state":"SUPPORTED"})
    if supported.get("state") != "SUPPORTED" or supported.get("canonical_engineering_promotion") is not False:
        errors.append("detector consensus may be SUPPORTED but never canonical")

    expect_error({**base, "state":"VALIDATED"}, "MACHINE_STATE_NOT_ALLOWED", errors)
    expect_error({**base, "source_version_id":"CEW-N12-SRC-WRONG"}, "SOURCEVERSION_PAGE_MISMATCH", errors)
    expect_error({**base, "page_id":"CEW-N12-PAGE-TAV06S-P001", "source_version_id":"UNKNOWN"}, "PAGE_NOT_REGISTERED", errors)
    expect_error({**base, "detector_coordinate_space":"PIXELS_300DPI", "projection_note":""}, "COORDINATE_PROJECTION_NOTE_REQUIRED", errors)
    expect_error({**base, "bbox_normalized_0_1":[0.9,0.9,0.2,0.2]}, "BBOX_OUTSIDE_NORMALIZED_PAGE", errors)
    expect_error({**base, "feature_type":"STRUCTURAL_BEAM"}, "UNKNOWN_FEATURE_TYPE", errors)

    if mc.existing_candidate_count() != 0:
        errors.append("B1.5 must not silently seed machine candidates into the current registry")

    contract = (ROOT / "docs/PRODUCT/CEW_MACHINE_DOCUMENT_CANDIDATES_V1_CONTRACT.md").read_text(encoding="utf-8").lower()
    for token in ["detector confidence is not epistemic state", "detected line is not a beam", "candidate bbox is not an evidenceregion", "pr #59"]:
        if token not in contract:
            errors.append(f"machine candidate contract missing boundary: {token}")

    if errors:
        print("CEW_MACHINE_DOCUMENT_CANDIDATES = FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CEW_MACHINE_DOCUMENT_CANDIDATES = PASS")
    print("TAV05A_READY_PAGE_CANDIDATE = PASS")
    print("TAV06S_WITHOUT_CURRENT_PAGE = FAIL_CLOSED_AS_REQUIRED")
    print("MACHINE_VALIDATED = FORBIDDEN")
    print("CONSENSUS_SUPPORTED_CANONICAL = false")
    print("CANDIDATE_TO_EVIDENCE_REGION = false")
    print("STRUCTURAL_BINDING_CREATED = false")
    print("CANONICAL_ENGINEERING_PROMOTION = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
