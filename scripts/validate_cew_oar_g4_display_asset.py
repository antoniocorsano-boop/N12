#!/usr/bin/env python3
"""Fail-closed parity gate for the exact visual asset used by OAR G4 review."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-OAR-300DPI"
ASSET_SHA256 = "6344abae8d390ef799812c808427431e684a61cca6bb5792de331b2b9d2b6252"
SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    binding = json.loads(read("automation/CEW_OAR_G4_COLUMN_REGION_BINDING_v1.json"))
    doc = binding["document"]
    assert doc["source_version_id"] == SOURCE_VERSION_ID
    assert doc["page_id"] == PAGE_ID
    assert doc["derived_asset_id"] == ASSET_ID
    assert doc["render_sha256"] == ASSET_SHA256
    assert doc["render_width_px"] == 7016
    assert doc["render_height_px"] == 12530
    assert binding["workflow"]["canonical_write_authorized"] is False

    with (ROOT / "data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv").open(newline="", encoding="utf-8") as handle:
        assets = {row["derived_asset_id"]: row for row in csv.DictReader(handle)}
    asset = assets[ASSET_ID]
    assert asset["source_version_id"] == SOURCE_VERSION_ID
    assert asset["page_id"] == PAGE_ID
    assert asset["asset_role"] == "OAR_FULL_PAGE_INTERACTION_RENDER"
    assert asset["format"] == "JPEG"
    assert asset["dpi"] == "300"
    assert asset["width_px"] == "7016" and asset["height_px"] == "12530"
    assert asset["generator"] == "PyMuPDF" and asset["generator_version"] == "1.26.4"
    assert ASSET_SHA256 in asset["generation_basis"]
    assert asset["authority_state"] == "DERIVED_REVIEW_AID_ONLY"
    assert asset["reproducibility_state"] == "REPRODUCIBLE_FROM_IMMUTABLE_SOURCE"

    resolver = read("scripts/cew_oar_g4_source_resolver.py")
    assert f'REGISTERED_DERIVED_ASSET_ID = "{ASSET_ID}"' in resolver
    assert f'REGISTERED_RENDER_SHA256 = "{ASSET_SHA256}"' in resolver
    assert "RUNTIME_DPI = 300" in resolver
    assert "JPEG_QUALITY = 92" in resolver
    assert "pixmap.save(RUNTIME_RASTER, jpg_quality=JPEG_QUALITY)" in resolver
    assert "_verify_registered_raster(RUNTIME_RASTER)" in resolver

    netlify_replay = read("netlify/functions/cew-oar-replay.mjs")
    assert f'derived_asset_id: "{ASSET_ID}"' in netlify_replay
    assert "validateOarReceiptGovernance" in netlify_replay

    sql_patch = read("sql/CEW_OAR_G4_DISPLAY_ASSET_BINDING_v1.sql")
    assert "create or replace function public.cew_oar_validate_g4_receipt_v1" in sql_patch.lower()
    assert f"is distinct from '{ASSET_ID}'" in sql_patch
    assert "v_action is null or v_action not in" in sql_patch.lower()
    assert "canonical_write_authorized" in sql_patch
    assert "engineering_authority_effect" in sql_patch

    provisioning = json.loads(read("automation/CEW_OAR_G4_SUPABASE_PROVISIONING_v1.json"))
    assert provisioning["ordered_sql"] == [
        "automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql",
        "sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql",
        "sql/CEW_OAR_G4_DISPLAY_ASSET_BINDING_v1.sql",
    ]
    runtime = provisioning["required_runtime_contract"]
    assert runtime["derived_asset_id"] == ASSET_ID
    assert runtime["render_sha256"] == ASSET_SHA256
    assert provisioning["authority"]["canonical_write_authorized"] is False
    assert provisioning["authority"]["structural_identity_authorized"] is False
    assert provisioning["authority"]["oar_human_confirmation"] is False
    assert provisioning["authority"]["engineering_authority_effect"] == "NONE"

    with (ROOT / "knowledge/ARTIFACT_REGISTRY_CEW_PROMOTION_ENGINE_PATCH_v1.csv").open(newline="", encoding="utf-8") as handle:
        registered = {row["artifact_id"]: row for row in csv.DictReader(handle)}
    patch = registered["SCHEMA-CEW-OAR-DISPLAY-ASSET-001"]
    procedure = registered["PROCEDURE-CEW-OAR-SUPABASE-001"]
    assert patch["path"] == "sql/CEW_OAR_G4_DISPLAY_ASSET_BINDING_v1.sql"
    assert patch["authority"] == "PROCEDURE" and patch["status"] == "CURRENT"
    assert procedure["path"] == "automation/CEW_OAR_G4_SUPABASE_PROVISIONING_v1.json"
    assert procedure["authority"] == "PROCEDURE" and procedure["status"] == "CURRENT"

    print("CEW_OAR_G4_DISPLAY_ASSET_PASS")
    print(f"derived_asset_id={ASSET_ID}")
    print(f"render_sha256={ASSET_SHA256} dimensions=7016x12530 dpi=300 generator=PyMuPDF-1.26.4")
    print("python=BOUND netlify=BOUND supabase_patch=BOUND provisioning=ORDERED")
    print("source_authority=IMMUTABLE_PDF display_authority=DERIVED_REVIEW_AID_ONLY canonical_write_authorized=false")


if __name__ == "__main__":
    main()
