#!/usr/bin/env python3
"""Deterministic validation of the real G4 / TAV-05S OAR pilot projection."""
from collections import Counter
import csv
from pathlib import Path

from cew_object_acquisition import CandidateState, evaluate_cad_promotion
from cew_oar_g4_column_pilot import load_g4_column_candidates, build_g4_column_pilot_workbench

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical"

EXPECTED_FAMILIES = {
    "COL-G4-40X40": 21,
    "COL-G4-45X30": 5,
    "COL-G4-30X45": 5,
    "COL-G4-30X110": 2,
    "COL-G4-110X30": 1,
}
SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"
ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-300DPI"
TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001"
SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
RENDER_SHA256 = "32dfa5976b3d6a6482f73159da1778de6483e5d90c671ae771793374781f58b7"


def _rows(name: str) -> list[dict[str, str]]:
    with (CANONICAL / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _one(name: str, key: str, value: str) -> dict[str, str]:
    matches = [row for row in _rows(name) if row[key] == value]
    assert len(matches) == 1, (name, key, value, len(matches))
    return matches[0]


def validate_source_page_chain() -> None:
    source = _one("CEW_SOURCE_IDENTITY_REGISTRY_v1.csv", "source_version_id", SOURCE_VERSION_ID)
    assert source["logical_source_code"] == "TAV-05S"
    assert source["readiness_state"] == "READY"
    assert source["sha256"] == SOURCE_SHA256
    assert source["git_blob_sha"] == "ec32cd621877e9037cb26ebc083164140a8e3e68"

    page = _one("CEW_PAGE_REGISTRY_v1.csv", "page_id", PAGE_ID)
    assert page["source_version_id"] == SOURCE_VERSION_ID
    assert page["logical_source_code"] == "TAV-05S"
    assert page["page_index"] == "0"
    assert float(page["source_width"]) == 1683.72
    assert float(page["source_height"]) == 3007.08
    assert page["readiness_state"] == "READY"
    assert "32561084360" in page["verification_basis"]
    assert RENDER_SHA256 in page["verification_basis"]

    asset = _one("CEW_DERIVED_ASSET_REGISTRY_v1.csv", "derived_asset_id", ASSET_ID)
    assert asset["source_version_id"] == SOURCE_VERSION_ID
    assert asset["page_id"] == PAGE_ID
    assert asset["format"] == "JPEG"
    assert asset["dpi"] == "300"
    assert asset["width_px"] == "7016"
    assert asset["height_px"] == "12530"
    assert asset["authority_state"] == "DERIVED_REVIEW_AID_ONLY"
    assert asset["reproducibility_state"] == "REPRODUCIBLE_FROM_IMMUTABLE_SOURCE"
    assert RENDER_SHA256 in asset["generation_basis"]

    transform = _one("CEW_PAGE_TRANSFORM_REGISTRY_v1.csv", "transform_id", TRANSFORM_ID)
    assert transform["page_id"] == PAGE_ID
    assert transform["derived_asset_id"] == ASSET_ID
    assert transform["readiness_state"] == "READY"
    assert transform["rounding_policy"] == "NO_CANONICAL_ROUNDING__DISPLAY_ONLY"
    assert transform["normalized_to_source_formula"] == "x_s=x_n*1683.720000;y_s=y_n*3007.080000"
    assert transform["source_to_normalized_formula"] == "x_n=x_s/1683.720000;y_n=y_s/3007.080000"
    assert transform["normalized_to_derived_formula"] == "x_px=x_n*7016;y_px=y_n*12530"
    assert transform["derived_to_normalized_formula"] == "x_n=x_px/7016;y_n=y_px/12530"


def main() -> None:
    validate_source_page_chain()

    candidates = load_g4_column_candidates()
    assert len(candidates) == 34
    assert len({item.evidence_object_id for item in candidates}) == 34
    assert all(item.object_type.value == "COLUMN" for item in candidates)
    assert all(item.state == CandidateState.CANDIDATE for item in candidates)
    assert all(item.review is None for item in candidates)

    counts = Counter(item.family_id for item in candidates)
    assert dict(counts) == EXPECTED_FAMILIES

    # DIRECT_REGISTERED is retained only as source-registration evidence.
    # It must not become OAR human confirmation.
    assert all(
        item.signature.context["source_validation_state"] == "DIRECT_REGISTERED"
        for item in candidates
    )
    assert not any(item.state == CandidateState.HUMAN_CONFIRMED for item in candidates)

    # SourceVersion and Page are now real canonical bindings. The remaining
    # provenance blocker is deliberately the missing per-object EvidenceRegion.
    assert all(item.provenance.source_version_id == SOURCE_VERSION_ID for item in candidates)
    assert all(item.provenance.page_id == PAGE_ID for item in candidates)
    assert all(not item.provenance.evidence_region_id for item in candidates)
    assert all(not item.provenance.complete() for item in candidates)

    # Even if runtime write authority were hypothetically true, these real
    # pilot candidates cannot promote because region provenance + human review are absent.
    for item in candidates:
        result = evaluate_cad_promotion(
            item,
            runtime_canonical_write_authorized=True,
            cad_object_id=f"CAD-{item.evidence_object_id}",
        )
        assert not result.eligible
        assert not result.canonical_write_authorized
        assert "INCOMPLETE_PROVENANCE" in result.reasons
        assert "HUMAN_CONFIRMATION_REQUIRED" in result.reasons

    view = build_g4_column_pilot_workbench()
    assert view["summary"]["total"] == 34
    assert view["summary"]["families"] == 5
    assert view["summary"]["states"] == {"proposal": 34}
    assert view["summary"]["provenance_blocking_count"] == 34
    assert view["summary"]["review_blocking_count"] == 0
    assert view["summary"]["promotion_ready_count"] == 0
    assert all(obj["reviewable"] for obj in view["objects"])
    assert not any(obj["promotion_ready"] for obj in view["objects"])
    assert view["pilot"]["source_page_binding"] == "READY"
    assert view["pilot"]["source_version_id"] == SOURCE_VERSION_ID
    assert view["pilot"]["page_id"] == PAGE_ID
    assert view["pilot"]["derived_asset_id"] == ASSET_ID
    assert view["pilot"]["page_transform_id"] == TRANSFORM_ID
    assert view["pilot"]["evidence_region_binding"] == "MISSING_PER_OBJECT"
    assert view["pilot"]["next_gate"] == "BIND_PER_OBJECT_EVIDENCE_REGIONS"
    assert view["pilot"]["oar_human_confirmation"] == "NOT_ASSERTED"
    assert view["canonical_write_authorized"] is False

    print("CEW_OAR_G4_COLUMN_PILOT_PASS")
    print("objects=34 families=5 source_page_binding=READY evidence_regions=0 provenance_blockers=34")
    print("human_confirmed=0 promotion_ready=0 canonical_write_authorized=false")


if __name__ == "__main__":
    main()
