#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_EVIDENCE_PROVENANCE_CONTRACT_v1.json"
SOURCES = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
PAGES = ROOT / "data" / "canonical" / "CEW_PAGE_REGISTRY_v1.csv"
ASSETS = ROOT / "data" / "canonical" / "CEW_DERIVED_ASSET_REGISTRY_v1.csv"
REGIONS = ROOT / "data" / "canonical" / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data" / "canonical" / "CEW_OBSERVATION_REGISTRY_v1.csv"
ARCH = ROOT / "docs" / "ARCHITECTURE" / "CEW_EVIDENCE_PROVENANCE_MODEL_v1.md"

REFERENCE = {
    "T5A-G01/G01-R06",
    "T5A-G07/G07-R07",
    "T5A-G05/G05-R04",
    "T6A-G03",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    if not ARCH.exists():
        raise AssertionError("missing evidence provenance architecture")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-EVIDENCE-PROVENANCE-v1":
        raise AssertionError("unexpected evidence provenance contract id")

    policy = contract.get("technical_reading_policy", {})
    min_dpi = int(policy.get("minimum_render_dpi", 0))
    if min_dpi != 300:
        raise AssertionError("CEW technical-reading minimum must be exactly 300 dpi")
    if policy.get("render_authority") != "DERIVED_REVIEW_AID_ONLY":
        raise AssertionError("technical renders must remain non-authoritative derived assets")

    inv = contract.get("invariants", {})
    if inv.get("observation_may_assert_structural_binding") is not False:
        raise AssertionError("Observation must not carry structural binding authority")
    if inv.get("crop_is_authority_region") is not False:
        raise AssertionError("crop must not define authority region")
    if inv.get("technical_reading_below_300dpi_allowed") is not False:
        raise AssertionError("technical reading below 300 dpi must be forbidden")
    if inv.get("unreadable_fields_may_be_filled_by_context") is not False:
        raise AssertionError("unreadable fields may not be filled by context")

    sources = {r["source_version_id"].strip(): r for r in read_csv(SOURCES)}
    pages = {r["page_id"].strip(): r for r in read_csv(PAGES)}
    assets = read_csv(ASSETS)
    regions = read_csv(REGIONS)
    observations = read_csv(OBS)

    if set(r["reference_item"].strip() for r in regions) != REFERENCE:
        raise AssertionError("reference region migration set changed")
    if set(r["reference_item"].strip() for r in observations) != REFERENCE:
        raise AssertionError("reference observation migration set changed")

    technical_assets_by_page: dict[str, list[dict[str, str]]] = {}
    for asset in assets:
        src = asset["source_version_id"].strip()
        page_id = asset["page_id"].strip()
        if src not in sources:
            raise AssertionError(f"derived asset references unknown SourceVersion: {asset['derived_asset_id']}")
        if page_id not in pages:
            raise AssertionError(f"derived asset references unknown Page: {asset['derived_asset_id']}")
        if asset["authority_state"].strip() != "DERIVED_REVIEW_AID_ONLY":
            raise AssertionError(f"derived render authority violation: {asset['derived_asset_id']}")
        if asset["asset_role"].strip() == "TECHNICAL_READING_RENDER":
            dpi = int(asset["dpi"])
            if dpi < min_dpi:
                raise AssertionError(f"technical-reading asset below {min_dpi} dpi: {asset['derived_asset_id']}")
            if asset["reproducibility_state"].strip() != "REPRODUCIBLE_FROM_IMMUTABLE_SOURCE":
                raise AssertionError(f"technical-reading asset not reproducible: {asset['derived_asset_id']}")
            technical_assets_by_page.setdefault(page_id, []).append(asset)

    ready_regions: set[str] = set()
    for row in regions:
        src = row["source_version_id"].strip()
        page_id = row["page_id"].strip()
        state = row["readiness_state"].strip()
        if src not in sources:
            raise AssertionError(f"region references unknown SourceVersion: {src}")
        if page_id not in pages:
            raise AssertionError(f"region references unknown Page: {page_id}")
        if sources[src]["readiness_state"].strip() != "READY":
            raise AssertionError(f"reference region parent source is not READY: {src}")
        if pages[page_id]["readiness_state"].strip() == "READY" and page_id not in technical_assets_by_page:
            raise AssertionError(f"READY reference page lacks >=300 dpi technical-reading asset: {page_id}")

        if state == "READY":
            if pages[page_id]["readiness_state"].strip() != "READY":
                raise AssertionError(f"READY region requires READY page: {row['evidence_region_id']}")
            if row["coordinate_space"].strip() != "NORMALIZED_0_1":
                raise AssertionError("reference READY regions must use NORMALIZED_0_1")
            if row["geometry_type"].strip() != "BBOX":
                raise AssertionError("reference READY regions must currently use BBOX")
            vals = [float(row[k]) for k in ("x", "y", "width", "height")]
            x, y, w, h = vals
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                raise AssertionError(f"invalid normalized bbox: {row['evidence_region_id']}")
            if x + w > 1.0000001 or y + h > 1.0000001:
                raise AssertionError(f"normalized bbox exceeds page: {row['evidence_region_id']}")
            ready_regions.add(row["evidence_region_id"].strip())
        else:
            if not row["migration_note"].strip():
                raise AssertionError(f"unready region requires migration note: {row['evidence_region_id']}")

    region_ids = {r["evidence_region_id"].strip() for r in regions}
    for row in observations:
        if row["source_version_id"].strip() not in sources:
            raise AssertionError(f"observation references unknown SourceVersion: {row['observation_id']}")
        if row["evidence_region_id"].strip() not in region_ids:
            raise AssertionError(f"observation references unknown region: {row['observation_id']}")
        if row["structural_binding"].strip():
            raise AssertionError(f"Observation may not assert structural binding: {row['observation_id']}")

    ready_reference = {
        r["reference_item"].strip() for r in regions
        if r["evidence_region_id"].strip() in ready_regions
    }
    acceptance = "PASS" if ready_reference == REFERENCE else "HOLD"

    print("CEW EVIDENCE PROVENANCE CONTRACT = PASS")
    print(f"Technical reading minimum dpi = {min_dpi}")
    print(f"Registered technical-reading assets = {sum(len(v) for v in technical_assets_by_page.values())}")
    print(f"Reference evidence acceptance = {acceptance}")
    if acceptance == "HOLD":
        missing = sorted(REFERENCE - ready_reference)
        print("CEW-F2 remains IN_PROGRESS; exact region localization required: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
