from __future__ import annotations

from copy import deepcopy
from typing import Any


PREDECESSOR_COL03C_SHA = "a9daa18ddfb56eaf1834ad17f329e2f2db0af72e"
OUTPUT_NAMES = (
    "historical-package-recovery-manifest.json",
    "historical-member-manifest.json",
    "historical-derived-data-quality.json",
    "historical-recovery-reconciliation.json",
    "historical-recovery-closure.json",
)

_AUTHORITY_FLAGS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "vertical_chain_assignment_authorized",
    "structural_identity_authorized",
    "canonical_node_assignment_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def _sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((deepcopy(row) for row in rows), key=lambda row: str(row.get("artifact_name") or ""))


def _assert_evidence_only(
    package_witness: dict[str, Any],
    member_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    csv_evidence: list[dict[str, Any]],
    dxf_evidence: list[dict[str, Any]],
    historical_quality: dict[str, Any],
) -> None:
    if package_witness.get("authority") != "HISTORICAL_DERIVED_EVIDENCE":
        raise ValueError("HISTORICAL_RECOVERY_AUTHORITY_DRIFT:package")
    if package_witness.get("identity_promotion_authorized") is not False:
        raise ValueError("HISTORICAL_RECOVERY_AUTHORITY_DRIFT:package")

    for collection_name, rows in (
        ("members", member_rows),
        ("inventory", inventory_rows),
        ("csv", csv_evidence),
        ("dxf", dxf_evidence),
    ):
        for row in rows:
            if row.get("authority") != "HISTORICAL_DERIVED_EVIDENCE":
                raise ValueError(f"HISTORICAL_RECOVERY_AUTHORITY_DRIFT:{collection_name}")
            if row.get("promotion_authorized") is not False:
                raise ValueError(f"HISTORICAL_RECOVERY_AUTHORITY_DRIFT:{collection_name}")
            if row.get("structural_identity_authorized") not in (None, False):
                raise ValueError(f"HISTORICAL_RECOVERY_AUTHORITY_DRIFT:{collection_name}")
            if row.get("canonical_geometry_authorized") not in (None, False):
                raise ValueError(f"HISTORICAL_RECOVERY_AUTHORITY_DRIFT:{collection_name}")

    for key in (
        "identity_promotion_authorized",
        "structural_identity_authorized",
        "section_assignment_authorized",
        "vertical_chain_assignment_authorized",
        "fixed_line_assignment_authorized",
        "canonical_geometry_authorized",
        "canonical_write_authorized",
    ):
        if historical_quality.get(key) not in (None, False):
            raise ValueError(f"HISTORICAL_RECOVERY_AUTHORITY_DRIFT:quality:{key}")


def build_recovery_artifacts(
    *,
    predecessor_sha: str,
    package_witness: dict[str, Any],
    member_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    csv_evidence: list[dict[str, Any]],
    dxf_evidence: list[dict[str, Any]],
    historical_quality: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if predecessor_sha != PREDECESSOR_COL03C_SHA:
        raise ValueError("COL03D_PREDECESSOR_SHA_DRIFT")

    _assert_evidence_only(
        package_witness,
        member_rows,
        inventory_rows,
        csv_evidence,
        dxf_evidence,
        historical_quality,
    )

    members = _sorted_rows(member_rows)
    inventory = _sorted_rows(inventory_rows)
    csv_rows = _sorted_rows(csv_evidence)
    dxf_rows = _sorted_rows(dxf_evidence)
    quality = deepcopy(historical_quality)
    quality["row_counts"] = dict(sorted(dict(quality.get("row_counts") or {}).items()))
    quality["historical_state_counts"] = dict(
        sorted(dict(quality.get("historical_state_counts") or {}).items())
    )
    quality["blocking_findings"] = sorted(set(quality.get("blocking_findings") or []))

    package_source_verified = package_witness.get("verification_state") in {
        "EXTERNALLY_VERIFIED_IMMUTABLE_WITNESS",
        "MATERIALIZED_VERIFIED",
    }
    package_repository_materialized = package_witness.get("repository_materialized") is True
    package_exact_source_replayable = package_witness.get("exact_source_replayable") is True
    members_materialized = (
        len(members) == 8
        and all(row.get("materialization_state") == "MATERIALIZED_VERIFIED" for row in members)
    )
    row_level_recovered = (
        bool(csv_rows)
        and all(isinstance(row.get("row_count"), int) and row["row_count"] >= 0 for row in csv_rows)
        and quality.get("status") == "EVIDENCE_ONLY"
    )

    qualification_blockers: list[str] = []
    if not package_source_verified:
        qualification_blockers.append("HISTORICAL_PACKAGE_SOURCE_NOT_VERIFIED")
    if not package_exact_source_replayable:
        qualification_blockers.append("HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE")
    if not members_materialized:
        qualification_blockers.append("REQUIRED_HISTORICAL_MEMBERS_NOT_MATERIALIZED")
    if not row_level_recovered:
        qualification_blockers.append("HISTORICAL_ROW_LEVEL_EVIDENCE_NOT_RECOVERED")
    if any(row.get("materialization_state") != "PACKAGE_MEMBER_DISCOVERED" for row in inventory):
        qualification_blockers.append("GOVERNED_INVENTORY_RECONCILIATION_INCOMPLETE")

    package_manifest = {
        "schema": "CEW_COL03D_HISTORICAL_PACKAGE_RECOVERY_MANIFEST",
        "predecessor_sha": predecessor_sha,
        "logical_name": str(package_witness.get("logical_name") or ""),
        "sha256": str(package_witness.get("sha256") or ""),
        "size_bytes": int(package_witness.get("size_bytes") or 0),
        "member_count": int(package_witness.get("member_count") or 0),
        "verification_state": str(package_witness.get("verification_state") or "NOT_VERIFIED"),
        "historical_package_source_verified": package_source_verified,
        "historical_package_repository_materialized": package_repository_materialized,
        "historical_package_exact_source_replayable": package_exact_source_replayable,
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }

    member_manifest = {
        "schema": "CEW_COL03D_HISTORICAL_MEMBER_MANIFEST",
        "predecessor_sha": predecessor_sha,
        "required_member_count": 8,
        "materialized_verified_count": sum(
            row.get("materialization_state") == "MATERIALIZED_VERIFIED" for row in members
        ),
        "members": members,
        "required_historical_members_materialized": members_materialized,
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }

    data_quality = {
        "schema": "CEW_COL03D_HISTORICAL_DERIVED_DATA_QUALITY",
        "predecessor_sha": predecessor_sha,
        "status": quality.get("status"),
        "row_counts": quality["row_counts"],
        "historical_state_counts": quality["historical_state_counts"],
        "blocking_findings": quality["blocking_findings"],
        "csv_evidence": csv_rows,
        "dxf_evidence": dxf_rows,
        "historical_row_level_evidence_recovered": row_level_recovered,
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
        "structural_identity_authorized": False,
        "section_assignment_authorized": False,
        "vertical_chain_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }

    reconciliation = {
        "schema": "CEW_COL03D_HISTORICAL_RECOVERY_RECONCILIATION",
        "predecessor_sha": predecessor_sha,
        "inventory_rows": inventory,
        "recovered_member_names": [row["artifact_name"] for row in members],
        "inventory_reconciliation_complete": not any(
            row.get("materialization_state") != "PACKAGE_MEMBER_DISCOVERED" for row in inventory
        ),
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }

    closure: dict[str, Any] = {
        "schema": "CEW_COL03D_HISTORICAL_RECOVERY_CLOSURE",
        "predecessor_sha": predecessor_sha,
        "historical_package_source_verified": package_source_verified,
        "historical_package_recovery_complete": package_source_verified and members_materialized,
        "historical_package_repository_materialized": package_repository_materialized,
        "historical_package_exact_source_replayable": package_exact_source_replayable,
        "required_historical_members_materialized": members_materialized,
        "historical_row_level_evidence_recovered": row_level_recovered,
        "historical_evidence_identity_promoted": False,
        "recovery_evidence_complete": package_source_verified and members_materialized and row_level_recovered,
        "col03d_exact_source_qualification_complete": not qualification_blockers,
        "qualification_blockers": sorted(set(qualification_blockers)),
    }
    closure.update({key: False for key in _AUTHORITY_FLAGS})

    return {
        "historical-package-recovery-manifest.json": package_manifest,
        "historical-member-manifest.json": member_manifest,
        "historical-derived-data-quality.json": data_quality,
        "historical-recovery-reconciliation.json": reconciliation,
        "historical-recovery-closure.json": closure,
    }
