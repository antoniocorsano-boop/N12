#!/usr/bin/env python3
"""Free, deterministic CEW reviewer for governance-critical repository invariants."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "automation/CEW_OAR_G4_COLUMN_REGION_BINDING_v1.json"
ASSET_REGISTRY = ROOT / "data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv"
TRANSFORM_REGISTRY = ROOT / "data/canonical/CEW_PAGE_TRANSFORM_REGISTRY_v1.csv"
NETLIFY_AUDIT = ROOT / "netlify/functions/cew-audit.mjs"
NETLIFY_REPLAY = ROOT / "netlify/functions/cew-oar-replay.mjs"
SQL_DIR = ROOT / "sql"

failures: list[str] = []


def fail(path: Path, message: str) -> None:
    rel = path.relative_to(ROOT) if path.is_absolute() else path
    failures.append(f"{rel}: {message}")
    print(f"::error file={rel}::{message}")


def require(condition: bool, path: Path, message: str) -> None:
    if not condition:
        fail(path, message)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def first_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    return next((row for row in rows if row.get(key) == value), None)


def review_authority_boundaries() -> None:
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    workflow = binding.get("workflow", {})
    require(workflow.get("canonical_write_authorized") is False, BINDING, "OAR binding must keep canonical writes unauthorized")
    require(workflow.get("geometry_confirmation_authority") == "HUMAN_EVIDENCE_LOCALIZATION_ONLY", BINDING, "geometry confirmation authority drift")
    require(workflow.get("oar_classification_authority") == "SEPARATE_REVIEW_REQUIRED", BINDING, "OAR classification must remain a separate review")
    require(len(binding.get("objects", [])) == 34, BINDING, "bounded G4 pilot must remain exactly 34 supports")

    # Scan only effective runtime/governance surfaces; validator fixtures are
    # intentionally excluded because they contain positive escalation examples
    # to prove fail-closed behavior.
    critical_files: list[Path] = []
    for root in (ROOT / "automation", ROOT / "netlify/functions", ROOT / "sql"):
        if root.exists():
            critical_files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".js", ".mjs", ".sql"})
    forbidden = {
        "canonical_write_authorized=true": re.compile(r"(?i)canonical_write_authorized[^\n]{0,24}\btrue\b"),
        "structural_identity_authorized=true": re.compile(r"(?i)structural_identity_authorized[^\n]{0,24}\btrue\b"),
        "oar_human_confirmation=true": re.compile(r"(?i)oar_human_confirmation[^\n]{0,24}\btrue\b"),
    }
    for path in critical_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in forbidden.items():
            if pattern.search(text):
                fail(path, f"forbidden authority escalation detected: {label}")


def review_provenance_chain() -> None:
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    document = binding.get("document", {})
    asset_id = str(document.get("derived_asset_id") or "")
    transform_id = str(document.get("page_transform_id") or "")
    render_sha = str(document.get("render_sha256") or "")

    require(bool(asset_id), BINDING, "missing governed derived_asset_id")
    require(bool(transform_id), BINDING, "missing governed page_transform_id")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", render_sha)), BINDING, "render_sha256 must be a lowercase SHA-256")

    assets = load_csv(ASSET_REGISTRY)
    asset = first_row(assets, "derived_asset_id", asset_id)
    require(asset is not None, ASSET_REGISTRY, f"binding asset is not registered: {asset_id}")
    if asset:
        hash_candidates = [value for key, value in asset.items() if "sha" in key.lower() and value]
        require(render_sha in hash_candidates or render_sha in " ".join(asset.values()), ASSET_REGISTRY, "registered asset hash does not match binding render_sha256")

    transforms = load_csv(TRANSFORM_REGISTRY)
    transform = first_row(transforms, "transform_id", transform_id)
    require(transform is not None, TRANSFORM_REGISTRY, f"binding transform is not registered: {transform_id}")
    if transform:
        require(transform.get("derived_asset_id") == asset_id, TRANSFORM_REGISTRY, "PageTransform is not bound to the displayed DerivedAsset")
        require(transform.get("page_id") == document.get("page_id"), TRANSFORM_REGISTRY, "PageTransform page_id differs from binding page")

    replay = NETLIFY_REPLAY.read_text(encoding="utf-8")
    require(asset_id in replay, NETLIFY_REPLAY, "Netlify replay predicate does not bind the displayed asset")
    require(transform_id in replay, NETLIFY_REPLAY, "Netlify replay predicate does not bind the displayed transform")

    sql_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in SQL_DIR.glob("*.sql"))
    require(asset_id in sql_text, SQL_DIR, "Supabase provisioning does not bind the displayed asset")
    require(transform_id in sql_text, SQL_DIR, "Supabase provisioning does not bind the displayed transform")


def review_atomic_oar_boundaries() -> None:
    text = NETLIFY_AUDIT.read_text(encoding="utf-8")
    atomic_start = text.find("async function atomicOarAppend")
    generic_start = text.find("async function appendReceipt")
    require(atomic_start >= 0 and generic_start > atomic_start, NETLIFY_AUDIT, "Netlify atomic/generic append functions not found")
    if atomic_start < 0 or generic_start <= atomic_start:
        return
    atomic = text[atomic_start:generic_start]
    generic = text[generic_start:]

    for marker in (
        "anchored_proposal AS (",
        "confirmation_guard AS (",
        "OAR_REGION_CONFIRMATION_BBOX_MISMATCH",
        "OAR_REGION_ANCHORED_PROPOSAL_NOT_FOUND",
        "p.receipt_json->'bbox' = ${receiptBboxJson}::jsonb",
    ):
        require(marker in atomic, NETLIFY_AUDIT, f"missing Netlify atomic confirmation guard marker: {marker}")

    if "confirmation_guard AS (" in atomic:
        guard_at = atomic.index("confirmation_guard AS (")
        for marker in ("updated_existing AS (", "seeded_transition AS (", "INSERT INTO cew_human_receipt_audit"):
            require(marker in atomic and guard_at < atomic.index(marker), NETLIFY_AUDIT, f"confirmation guard must precede {marker}")
    require(atomic.count("(SELECT reason FROM confirmation_guard) = 'OK'") >= 2, NETLIFY_AUDIT, "both existing-head and legacy-seed confirmation paths must be bbox-gated")

    generic_guard = "payload.receipt_json?.receipt_type === OAR_RECEIPT_TYPE"
    require(generic_guard in generic, NETLIFY_AUDIT, "generic append does not reject OAR receipts")
    require("OAR_ATOMIC_TRANSITION_REQUIRED" in generic, NETLIFY_AUDIT, "generic OAR append must fail closed")
    if generic_guard in generic and "INSERT INTO cew_human_receipt_audit" in generic:
        require(generic.index(generic_guard) < generic.index("INSERT INTO cew_human_receipt_audit"), NETLIFY_AUDIT, "generic OAR rejection occurs after audit insert")

    sql_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in SQL_DIR.glob("*.sql"))
    require("OAR_REGION_CONFIRMATION_BBOX_MISMATCH" in sql_text, SQL_DIR, "Supabase atomic path lacks confirmation bbox mismatch guard")
    require("cew_oar_validate_g4_receipt_v1" in sql_text, SQL_DIR, "Supabase governed OAR receipt validator missing")


def main() -> None:
    review_authority_boundaries()
    review_provenance_chain()
    review_atomic_oar_boundaries()

    if failures:
        print("CEW_FREE_REVIEW_GATE_FAIL")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)

    print("CEW_FREE_REVIEW_GATE_PASS")
    print("reviewer=DETERMINISTIC_REPOSITORY_INVARIANTS")
    print("g4_supports=34")
    print("provenance_chain=SOURCE_PAGE_DERIVED_ASSET_PAGE_TRANSFORM_BOUND")
    print("netlify_confirmation_bbox_cas=FAIL_CLOSED")
    print("supabase_confirmation_bbox_cas=FAIL_CLOSED")
    print("generic_oar_append=FAIL_CLOSED")
    print("canonical_write_authorized=false structural_identity_authorized=false oar_human_confirmation=false")


if __name__ == "__main__":
    main()
