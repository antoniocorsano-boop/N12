#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_ews3_spatial_candidate_review_runtime as runtime

CONTRACT = ROOT / "automation/CEW_EWS31_VIEWER_FRAME_ALIGNMENT_CONTRACT_v1.json"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["contract"] == "CEW_EWS31_VIEWER_FRAME_ALIGNMENT", "contract id drift")
    require(contract["status"] in {"IMPLEMENTED_PENDING_VALIDATION", "EWS31_COMPLETE_PASS"}, "invalid state")
    require(contract["authority_effect"] == "NONE", "authority drift")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")

    locators, meta = runtime._load_locators()
    require(meta["source_frame"] == "ROT90_CCW_300DPI", "registration frame drift")
    require(meta["frame_width_px"] == 12530 and meta["frame_height_px"] == 7016, "registration dimensions drift")
    require(meta["expected_native_dzi_width_px"] == 7016 and meta["expected_native_dzi_height_px"] == 12530, "native DZI dimensions drift")
    require(meta["viewer_frame_adapter"] == "ROT90_CCW_REGISTRATION_TO_NATIVE_DZI", "frame adapter drift")
    require(len(locators) == 34, "locator coverage drift")

    nw, nh = 7016.0, 12530.0
    mapped = {}
    for sid, loc in locators.items():
        x, y = runtime._registration_to_native_viewer(float(loc["u_px"]), float(loc["v_px"]), native_width=nw, native_height=nh)
        require(math.isfinite(x) and math.isfinite(y), f"non-finite mapped locator {sid}")
        require(0 <= x <= nw and 0 <= y <= nh, f"mapped locator outside native frame {sid}")
        mapped[sid] = (x, y)

    x11, y11 = mapped["11"]
    require(4900 < x11 < 5050, f"support 11 native x unexpected: {x11}")
    require(5850 < y11 < 6050, f"support 11 native y unexpected: {y11}")

    source = (ROOT / "scripts/cew_ews3_spatial_candidate_review_runtime.py").read_text(encoding="utf-8")
    for marker in [
        "ROT90_CCW_REGISTRATION_TO_NATIVE_DZI",
        "const x=nw-v,y=u",
        "getContentSize",
        "locator fonte registrato · navigazione",
        "registrationState",
        "Frame registrazione",
        "Adapter viewer",
        "focusLocator(locator,true)",
    ]:
        require(marker in source, f"runtime invariant missing: {marker}")
    require("syncStatus" not in source, "EWS-3.1 must not claim technical spatial synchronization")

    print("CEW_EWS31_VIEWER_FRAME_ALIGNMENT = PASS")
    print("REGISTRATION_FRAME = 12530x7016 ROT90_CCW_300DPI")
    print("NATIVE_DZI_FRAME = 7016x12530")
    print(f"SUPPORT_11_NATIVE = {x11:.3f},{y11:.3f}")
    print("LOCATOR_COVERAGE_NATIVE_FRAME = 34/34")
    print("AUTHORITY_EFFECT = NONE")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
