#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_EWS21_EWS32_PROFESSIONAL_USABILITY_CONTRACT_v1.json"
EWS21 = ROOT / "scripts/cew_ews21_compact_context_rail_runtime.py"
EWS32 = ROOT / "scripts/cew_ews32_persistent_source_locator_runtime.py"
RESUME = ROOT / "scripts/cew_enterprise_governed_resume_runtime.py"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["authority"]["authority_effect"] == "NONE"
    assert contract["authority"]["canonical_write_authorized"] is False
    assert contract["authority"]["structural_identity_authorized"] is False
    assert contract["authority"]["canonical_geometry_authorized"] is False
    assert contract["authority"]["locator_navigation_only"] is True

    rail = EWS21.read_text(encoding="utf-8")
    locator = EWS32.read_text(encoding="utf-8")
    resume = RESUME.read_text(encoding="utf-8")

    require(rail, "CEW_EWS21_COMPACT_PROFESSIONAL_RAIL", "EWS-2.1 marker")
    require(rail, "ews21-prototype-governed", "governed prototype compact state")
    require(rail, "ews21-edit-example", "explicit edit example state")
    require(rail, "#oaTeach>label", "default form compaction")
    require(rail, "grid-template-rows:auto minmax(120px,.42fr) minmax(220px,.58fr)", "bounded review layout")
    require(rail, "secondary_details_collapsed:true", "secondary disclosure contract")

    require(locator, "CEW_EWS32_PERSISTENT_SOURCE_LOCATOR", "EWS-3.2 marker")
    require(locator, "anchor_object_id", "prototype anchor binding")
    require(locator, "mode==='REVIEW_SET'", "review mode active candidate routing")
    require(locator, "const x=nw-v,y=u", "ROT90_CCW native viewer adapter")
    require(locator, "locator fonte registrato · navigazione", "status strip consistency")
    require(locator, "Prototipo governato", "prototype locator badge")
    require(locator, "canonical_write_authorized:false", "no canonical write")
    require(locator, "structural_identity_authorized:false", "no identity authority")
    if "method:'POST'" in locator or 'method:"POST"' in locator:
        raise AssertionError("EWS-3.2 must not perform writes")

    order = [
        "ews2_runtime.augment",
        "ews2_guard_runtime.augment",
        "ews3_runtime.augment",
        "ews21_runtime.augment",
        "ews32_runtime.augment",
    ]
    positions = [resume.find(token) for token in order]
    if any(p < 0 for p in positions):
        raise AssertionError("presentation composition token missing")
    # ews2 is nested inside the guard call, so only require downstream stages after it.
    if not (resume.find("ews3_runtime.augment") < resume.find("ews21_runtime.augment") < resume.find("ews32_runtime.augment")):
        raise AssertionError("EWS-3 -> EWS-2.1 -> EWS-3.2 composition order invalid")

    print("CEW_EWS21_COMPACT_PROFESSIONAL_RAIL = PASS")
    print("CEW_EWS32_PERSISTENT_SOURCE_LOCATOR = PASS")
    print("CEW_EWS21_EWS32_AUTHORITY_BOUNDARY = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
