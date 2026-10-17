#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_SOURCE_IDENTITY_CONTRACT_v1.json"
REGISTRY = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
ARCH = ROOT / "docs" / "ARCHITECTURE" / "CEW_SOURCE_EVIDENCE_REPOSITORY_v1.md"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_READINESS = {
    "READY",
    "NEEDS_HASH",
    "NEEDS_LOCATOR",
    "NEEDS_HASH_AND_LOCATOR",
    "UNRESOLVED",
}
ALLOWED_AUTHORITY = {"PRIMARY", "SECONDARY", "DERIVED"}


def main() -> int:
    if not ARCH.exists():
        raise AssertionError("missing CEW source/evidence repository architecture")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-SOURCE-IDENTITY-v1":
        raise AssertionError("unexpected source identity contract id")
    invariants = contract.get("invariants", {})
    if invariants.get("filename_is_identity") is not False:
        raise AssertionError("filename must never be source identity")
    if invariants.get("source_version_overwrite_allowed") is not False:
        raise AssertionError("SourceVersion overwrite must remain prohibited")
    if invariants.get("derived_asset_may_be_primary_authority") is not False:
        raise AssertionError("derived asset may not become PRIMARY authority")

    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise AssertionError("source identity registry is empty")

    source_versions: set[str] = set()
    logical_codes: set[str] = set()
    for row in rows:
        sid = row["source_id"].strip()
        vid = row["source_version_id"].strip()
        code = row["logical_source_code"].strip()
        authority = row["authority"].strip()
        readiness = row["readiness_state"].strip()
        digest = row["sha256"].strip().lower()
        locator = row["storage_locator"].strip()
        reason = row["migration_reason"].strip()

        if not sid or not vid or not code:
            raise AssertionError("source_id, source_version_id and logical_source_code are required")
        if vid in source_versions:
            raise AssertionError(f"duplicate source_version_id: {vid}")
        source_versions.add(vid)
        logical_codes.add(code)

        if authority not in ALLOWED_AUTHORITY:
            raise AssertionError(f"invalid authority {authority} for {vid}")
        if readiness not in ALLOWED_READINESS:
            raise AssertionError(f"invalid readiness {readiness} for {vid}")

        if readiness == "READY":
            if not SHA256_RE.fullmatch(digest):
                raise AssertionError(f"READY source must have 64-hex SHA-256: {vid}")
            if not locator:
                raise AssertionError(f"READY source must have storage locator: {vid}")
        else:
            if not reason:
                raise AssertionError(f"unready source requires explicit migration reason: {vid}")
            if digest and not SHA256_RE.fullmatch(digest):
                raise AssertionError(f"invalid optional SHA-256: {vid}")

        if authority == "DERIVED" and row["document_role"].strip() == "primary_source":
            raise AssertionError(f"derived row cannot claim primary-source role: {vid}")

    required_reference = {"TAV-05A", "TAV-06A"}
    missing = required_reference - logical_codes
    if missing:
        raise AssertionError(f"reference source migration rows missing: {sorted(missing)}")

    ready_reference = {
        row["logical_source_code"].strip()
        for row in rows
        if row["logical_source_code"].strip() in required_reference
        and row["readiness_state"].strip() == "READY"
    }
    acceptance = "PASS" if ready_reference == required_reference else "HOLD"

    print("CEW SOURCE IDENTITY CONTRACT = PASS")
    print(f"Registry rows: {len(rows)}")
    print(f"Reference source acceptance = {acceptance}")
    if acceptance == "HOLD":
        unresolved = sorted(required_reference - ready_reference)
        print("CEW-F1 remains IN_PROGRESS; unresolved immutable source identity: " + ", ".join(unresolved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
