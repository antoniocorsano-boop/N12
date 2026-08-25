#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_EVIDENCE_PROVENANCE_CONTRACT_v1.json"
SOURCES = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
PAGES = ROOT / "data" / "canonical" / "CEW_PAGE_REGISTRY_v1.csv"
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
    inv = contract.get("invariants", {})
    if inv.get("observation_may_assert_structural_binding") is not False:
        raise AssertionError("Observation must not carry structural binding authority")
    if inv.get("crop_is_authority_region") is not False:
        raise AssertionError("crop must not define authority region")
    if inv.get("unreadable_fields_may_be_filled_by_context") is not False:
        raise AssertionError("unreadable fields may not be filled by context")

    sources = {r["source_version_id"].strip(): r for r in read_csv(SOURCES)}
    pages = {r["page_id"].strip(): r for r in read_csv(PAGES)}
    regions = read_csv(REGIONS)
    observations = read_csv(OBS)

    if set(r["reference_item"].strip() for r in regions) != REFERENCE:
        raise AssertionError("reference region migration set changed")
    if set(r["reference_item"].strip() for r in observations) != REFERENCE:
        raise AssertionError("reference observation migration set changed")

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

    for row in observations:
        if row["source_version_id"].strip() not in sources:
            raise AssertionError(f"observation references unknown SourceVersion: {row['observation_id']}")
        if row["evidence_region_id"].strip() not in {r["evidence_region_id"].strip() for r in regions}:
            raise AssertionError(f"observation references unknown region: {row['observation_id']}")
        if row["structural_binding"].strip():
            raise AssertionError(f"Observation may not assert structural binding: {row['observation_id']}")

    ready_reference = {
        r["reference_item"].strip() for r in regions
        if r["evidence_region_id"].strip() in ready_regions
    }
    acceptance = "PASS" if ready_reference == REFERENCE else "HOLD"

    print("CEW EVIDENCE PROVENANCE CONTRACT = PASS")
    print(f"Reference evidence acceptance = {acceptance}")
    if acceptance == "HOLD":
        missing = sorted(REFERENCE - ready_reference)
        print("CEW-F2 remains IN_PROGRESS; exact region localization required: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
