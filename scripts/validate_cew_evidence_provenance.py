#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_EVIDENCE_PROVENANCE_CONTRACT_v1.json"
SOURCES = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
PAGES = ROOT / "data" / "canonical" / "CEW_PAGE_REGISTRY_v1.csv"
ASSETS = ROOT / "data" / "canonical" / "CEW_DERIVED_ASSET_REGISTRY_v1.csv"
TRANSFORMS = ROOT / "data" / "canonical" / "CEW_PAGE_TRANSFORM_REGISTRY_v1.csv"
REGIONS = ROOT / "data" / "canonical" / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data" / "canonical" / "CEW_OBSERVATION_REGISTRY_v1.csv"
ARCH = ROOT / "docs" / "ARCHITECTURE" / "CEW_EVIDENCE_PROVENANCE_MODEL_v1.md"

# Frozen F2 closure reference subset. Additional governed chains may be appended,
# but these four historical chains must never disappear or regress.
REFERENCE = {"T5A-G01/G01-R06", "T5A-G07/G07-R07", "T5A-G05/G05-R04", "T6A-G03"}
FINAL_READING_STATES = {"READABLE", "PARTIAL", "UNREADABLE", "GRAPHICALLY_DIRECT_PARTIAL"}
TOL = 1e-9


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=TOL)


def main() -> int:
    if not ARCH.exists():
        raise AssertionError("missing evidence provenance architecture")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-EVIDENCE-PROVENANCE-v1":
        raise AssertionError("unexpected evidence provenance contract id")
    if contract.get("required_chain") != ["SourceVersion", "Page", "PageTransform", "EvidenceRegion", "Observation"]:
        raise AssertionError("F2 closure chain must include PageTransform")
    if contract.get("canonical_region_space") != "NORMALIZED_0_1":
        raise AssertionError("canonical region space must be NORMALIZED_0_1")
    if contract.get("viewer_consumption_space") != "NORMALIZED_0_1":
        raise AssertionError("viewer must consume certified normalized geometry")

    inv = contract.get("invariants", {})
    required_true = {
        "ready_page_requires_ready_source_version",
        "ready_region_requires_ready_page",
        "ready_region_requires_transform",
        "ready_region_requires_reproducible_derived_asset_when_used_for_inspection",
        "ready_observation_requires_ready_region",
        "normalized_region_must_roundtrip_to_source_native",
        "normalized_region_must_roundtrip_to_derived_pixels",
        "viewer_must_consume_certified_transform_without_geometry_correction",
    }
    for key in required_true:
        if inv.get(key) is not True:
            raise AssertionError(f"required F2 invariant not enabled: {key}")
    required_false = {
        "observation_may_assert_structural_binding",
        "crop_is_authority_region",
        "derived_asset_is_primary_authority",
        "derived_pixel_coordinates_are_source_native",
        "unreadable_fields_may_be_filled_by_context",
        "unreadable_fields_may_be_filled_by_ai_confidence",
    }
    for key in required_false:
        if inv.get(key) is not False:
            raise AssertionError(f"required F2 invariant not disabled: {key}")

    sources = {r["source_version_id"].strip(): r for r in read_csv(SOURCES)}
    pages = {r["page_id"].strip(): r for r in read_csv(PAGES)}
    assets = {r["derived_asset_id"].strip(): r for r in read_csv(ASSETS)}
    transforms = {r["transform_id"].strip(): r for r in read_csv(TRANSFORMS)}
    regions = read_csv(REGIONS)
    observations = read_csv(OBS)

    region_reference_items = {r["reference_item"].strip() for r in regions}
    observation_reference_items = {r["reference_item"].strip() for r in observations}
    if not REFERENCE.issubset(region_reference_items):
        raise AssertionError("frozen reference region subset changed")
    if not REFERENCE.issubset(observation_reference_items):
        raise AssertionError("frozen reference observation subset changed")

    region_source_ids = {r["source_version_id"].strip() for r in regions}
    for src_id, src in sources.items():
        if src_id in region_source_ids:
            if src["readiness_state"].strip() != "READY":
                raise AssertionError(f"reference SourceVersion not READY: {src_id}")
            if len(src["sha256"].strip()) != 64:
                raise AssertionError(f"reference SourceVersion lacks SHA-256: {src_id}")
            locator = src["storage_locator"].strip()
            if "@78c20a52db4f391ce0d13b9705b9f04737e218c9/" not in locator:
                raise AssertionError(f"reference SourceVersion locator is not pinned to immutable archive commit: {src_id}")

    ready_reference: set[str] = set()
    ready_regions: set[str] = set()
    for row in regions:
        region_id = row["evidence_region_id"].strip()
        ref = row["reference_item"].strip()
        src_id = row["source_version_id"].strip()
        page_id = row["page_id"].strip()
        asset_id = row["derived_asset_id"].strip()
        transform_id = row["transform_id"].strip()

        if row["readiness_state"].strip() != "READY":
            raise AssertionError(f"reference EvidenceRegion not READY: {region_id}")
        if src_id not in sources or page_id not in pages or asset_id not in assets or transform_id not in transforms:
            raise AssertionError(f"incomplete provenance parent chain: {region_id}")

        page = pages[page_id]
        asset = assets[asset_id]
        transform = transforms[transform_id]
        if page["readiness_state"].strip() != "READY":
            raise AssertionError(f"READY region requires READY page: {region_id}")
        if page["source_version_id"].strip() != src_id:
            raise AssertionError(f"Page/SourceVersion mismatch: {region_id}")
        if asset["source_version_id"].strip() != src_id or asset["page_id"].strip() != page_id:
            raise AssertionError(f"DerivedAsset parent mismatch: {region_id}")
        if asset["authority_state"].strip() != "DERIVED_REVIEW_AID_ONLY":
            raise AssertionError(f"DerivedAsset authority violation: {region_id}")
        if asset["reproducibility_state"].strip() != "REPRODUCIBLE_FROM_IMMUTABLE_SOURCE":
            raise AssertionError(f"DerivedAsset is not reproducible: {region_id}")
        if transform["page_id"].strip() != page_id or transform["derived_asset_id"].strip() != asset_id:
            raise AssertionError(f"PageTransform parent mismatch: {region_id}")
        if transform["readiness_state"].strip() != "READY":
            raise AssertionError(f"PageTransform not READY: {region_id}")
        if "viewer_x=x_n" not in transform["viewer_consumption_formula"]:
            raise AssertionError(f"Viewer transform may not alter canonical geometry: {region_id}")

        if row["coordinate_space"].strip() != "NORMALIZED_0_1" or row["geometry_type"].strip() != "BBOX":
            raise AssertionError(f"unexpected READY region geometry: {region_id}")
        x, y, w, h = [float(row[k]) for k in ("x", "y", "width", "height")]
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1 and x + w <= 1.0000001 and y + h <= 1.0000001):
            raise AssertionError(f"invalid normalized bbox: {region_id}")

        sw, sh = float(page["source_width"]), float(page["source_height"])
        pw, ph = float(asset["width_px"]), float(asset["height_px"])
        for value in (sw, sh, pw, ph):
            if value <= 0:
                raise AssertionError(f"non-positive page/asset dimension: {region_id}")

        src_bbox = (x * sw, y * sh, w * sw, h * sh)
        src_roundtrip = (src_bbox[0] / sw, src_bbox[1] / sh, src_bbox[2] / sw, src_bbox[3] / sh)
        px_bbox = (x * pw, y * ph, w * pw, h * ph)
        px_roundtrip = (px_bbox[0] / pw, px_bbox[1] / ph, px_bbox[2] / pw, px_bbox[3] / ph)
        canonical = (x, y, w, h)
        if not all(close(a, b) for a, b in zip(canonical, src_roundtrip)):
            raise AssertionError(f"source-native roundtrip failed: {region_id}")
        if not all(close(a, b) for a, b in zip(canonical, px_roundtrip)):
            raise AssertionError(f"derived-pixel roundtrip failed: {region_id}")

        basis = row["localization_basis"].strip()
        note = row["migration_note"].strip().lower()
        if "immutable pdf page" not in basis.lower() and "primary-source" not in basis.lower():
            raise AssertionError(f"region localization lacks primary-source provenance: {region_id}")
        if "crop is not authority" not in note:
            raise AssertionError(f"region must explicitly reject crop authority: {region_id}")

        ready_regions.add(region_id)
        ready_reference.add(ref)

    finalized_reference: set[str] = set()
    region_ids = {r["evidence_region_id"].strip() for r in regions}
    for row in observations:
        obs_id = row["observation_id"].strip()
        region_id = row["evidence_region_id"].strip()
        if region_id not in ready_regions or region_id not in region_ids:
            raise AssertionError(f"Observation lacks READY EvidenceRegion: {obs_id}")
        if row["reading_state"].strip() not in FINAL_READING_STATES:
            raise AssertionError(f"Observation not finalized: {obs_id}")
        if row["structural_binding"].strip():
            raise AssertionError(f"Observation may not assert structural binding: {obs_id}")
        if row["reference_item"].strip() == "T6A-G03":
            joined = (row["canonical_evidence_basis"] + " " + row["migration_note"]).upper()
            if "UNBOUND" not in joined:
                raise AssertionError("T6A-G03 must explicitly remain structurally UNBOUND")
        finalized_reference.add(row["reference_item"].strip())

    if not REFERENCE.issubset(ready_reference) or not REFERENCE.issubset(finalized_reference):
        raise AssertionError("not all four frozen reference chains satisfy reproducible closure")

    print("CEW EVIDENCE PROVENANCE CONTRACT = PASS")
    print("Frozen reproducible reference chains = 4/4")
    print(f"Total governed READY EvidenceRegions = {len(ready_regions)}")
    print(f"Total finalized Observations = {len(finalized_reference)}")
    print("Coordinate roundtrip NORMALIZED_0_1 <-> SOURCE_NATIVE = PASS")
    print("Coordinate roundtrip NORMALIZED_0_1 <-> DERIVED_ASSET_PIXELS = PASS")
    print("T6A-G03 structural binding = UNBOUND")
    print("EVIDENCE_PROVENANCE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
