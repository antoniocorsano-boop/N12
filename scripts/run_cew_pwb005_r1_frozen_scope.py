#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

import build_cew_evidence_region_content_diagnostic as diagnostic

FROZEN_PWB005_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-T6A-G03",
}

_original_build_plan = diagnostic.geometry_builder.build_plan


def _frozen_geometry_plan():
    plan = deepcopy(_original_build_plan())
    found: set[str] = set()
    for source in plan.get("sources", []):
        scoped = []
        for region in source.get("evidence_regions", []):
            region_id = str(region.get("evidence_region_id", "")).strip()
            if region_id in FROZEN_PWB005_REGIONS:
                scoped.append(region)
                found.add(region_id)
        source["evidence_regions"] = scoped
    missing = FROZEN_PWB005_REGIONS - found
    if missing:
        raise AssertionError(f"PWB005 frozen EvidenceRegion missing: {sorted(missing)}")
    plan["governed_region_count"] = len(found)
    plan["diagnostic_scope"] = "PWB005_FROZEN_REFERENCE_REGIONS_ONLY"
    plan["excluded_extension_regions_are_regressions"] = False
    return plan


def main() -> int:
    diagnostic.geometry_builder.build_plan = _frozen_geometry_plan
    return diagnostic.main()


if __name__ == "__main__":
    raise SystemExit(main())
