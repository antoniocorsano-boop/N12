#!/usr/bin/env python3
from __future__ import annotations

import build_cew_evidence_region_mapping_root_cause as root_cause
import run_cew_pwb005_r1_frozen_scope as frozen_scope


def main() -> int:
    root_cause.r1.geometry_builder.build_plan = frozen_scope._frozen_geometry_plan
    return root_cause.main()


if __name__ == "__main__":
    raise SystemExit(main())
