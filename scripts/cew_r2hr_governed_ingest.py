#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import cew_professional_gap_review as gap_review

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "data" / "review" / "cew_r2hr_governed_ingest"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "cew_r2gi_ingest"
CONTRACT_PATH = ROOT / "automation" / "CEW_PWB005_R2GI_GOVERNED_REVIEW_INGEST_CONTRACT_v1.json"
EXPECTED_REGIONS = set(gap_review.EXPECTED_REGIONS)
ALLOWED_AUDIT_RECEIPT_TYPE = "CEW_PWB005_R2HR_RUNTIME_AUDIT_ENVELOPE_v1"
OUTPUT_SCHEMA_VERSION = "1.2"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"R2GI_JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def _contract() -> dict[str, Any]:
    if not CONTRACT_PATH.is_file():
        raise ValueError("R2GI_CONTRACT_MISSING")
    payload = _load(CONTRACT_PATH)
    if payload.get("contract_id") != "CEW_PWB005_R2GI_GOVERNED_REVIEW_INGEST_CONTRACT_v1":
        raise ValueError("R2GI_CONTRACT_ID_MISMATCH")
    if payload.get("canonical_write_authorized") is not False:
        raise ValueError("R2GI_CONTRACT_CANONICAL_WRITE_DRIFT")
    if payload.get("geometry_materialization_authorized") is not False:
        raise ValueError("R2GI_CONTRACT_GEOMETRY_AUTHORITY_DRIFT")
    return payload


def _validate_audit_envelope(envelope: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    required = {
        "decision_id",
        "task_id",
        "residual_id",
        "timestamp",
        "receipt_type",
        "r2hr_receipt",
        "authority",
        "canonical_write",
        "engineering_authority_effect",
        "next_gate",
    }
    if set(envelope) != required:
        raise ValueError("R2GI_AUDIT_ENVELOPE_FIELD_SET_MISMATCH")
    if envelope.get("receipt_type") != ALLOWED_AUDIT_RECEIPT_TYPE:
        raise ValueError("R2GI_AUDIT_ENVELOPE_TYPE_MISMATCH")
    if envelope.get("authority") != "RUNTIME_AUDIT_ONLY":
        raise ValueError("R2GI_AUDIT_AUTHORITY_MISMATCH")
    if envelope.get("canonical_write") is not False:
        raise ValueError("R2GI_AUDIT_CANONICAL_WRITE_FORBIDDEN")
    if envelope.get("engineering_authority_effect") != "NONE":
        raise ValueError("R2GI_AUDIT_ENGINEERING_AUTHORITY_FORBIDDEN")
    if envelope.get("next_gate") != "R2HR_GOVERNED_REVIEW_INGEST_REQUIRED":
        raise ValueError("R2GI_AUDIT_NEXT_GATE_MISMATCH")

    receipt = envelope.get("r2hr_receipt")
    if not isinstance(receipt, dict):
        raise ValueError("R2GI_R2HR_RECEIPT_REQUIRED")
    region_id = str(receipt.get("evidence_region_id", ""))
    if region_id not in EXPECTED_REGIONS:
        raise ValueError("R2GI_REGION_NOT_ALLOWED")
    if envelope.get("residual_id") != region_id:
        raise ValueError("R2GI_ENVELOPE_REGION_MISMATCH")

    expected = gap_review.template(region_id)
    validated = gap_review.validate_receipt(receipt, expected)
    expected_envelope = gap_review.audit_envelope(str(envelope.get("task_id", "")), validated)
    if envelope.get("decision_id") != expected_envelope["decision_id"]:
        raise ValueError("R2GI_AUDIT_DECISION_ID_MISMATCH")
    return region_id, validated


def _decision_finding(region_id: str, receipt: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    decision_value = decision["decision"]
    if decision_value == "SUPPORTED_CONTINUITY_HYPOTHESIS":
        disposition = "ELIGIBLE_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW"
    elif decision_value == "REJECTED_CONTINUITY_HYPOTHESIS":
        disposition = "EXCLUDED_FROM_GEOMETRY_MATERIALIZATION"
    else:
        disposition = "BLOCKS_REGION_GEOMETRY_MATERIALIZATION"
    finding = {
        "finding_id": "R2GI-" + hashlib.sha256(
            f"{receipt['candidate_head_sha']}|{region_id}|{decision['gap_hypothesis_id']}|{decision_value}".encode("utf-8")
        ).hexdigest()[:20],
        "candidate_head_sha": receipt["candidate_head_sha"],
        "build_revision": receipt["build_revision"],
        "source_code": receipt["source_code"],
        "source_version_id": receipt["source_version_id"],
        "source_sha256": receipt["source_sha256"],
        "page_id": receipt["page_id"],
        "transform_id": receipt["transform_id"],
        "evidence_region_id": region_id,
        "gap_hypothesis_id": decision["gap_hypothesis_id"],
        "human_decision": decision_value,
        "human_rationale": decision["rationale"],
        "reviewer_label": receipt["reviewer_label"],
        "reviewed_at": receipt["reviewed_at"],
        "candidate_ids": list(decision["candidate_ids"]),
        "bridge_endpoints_normalized": decision["bridge_endpoints_normalized"],
        "metric_snapshot": decision["metric_snapshot"],
        "disposition": disposition,
        "finding_authority": "GOVERNED_HUMAN_REVIEW_FINDING_ONLY",
        "finding_is_geometry": False,
        "geometry_materialization_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    finding["finding_sha256"] = _sha256(finding)
    return finding


def ingest_envelopes(envelopes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    _contract()
    review_status = gap_review.status()
    if review_status.get("state") != "READY":
        raise ValueError(review_status.get("reason", "R2HR_PACKAGE_NOT_READY"))

    by_region: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for envelope in envelopes:
        region_id, receipt = _validate_audit_envelope(envelope)
        if region_id in by_region:
            raise ValueError(f"R2GI_DUPLICATE_REGION_RECEIPT:{region_id}")
        by_region[region_id] = (envelope, receipt)

    candidate_head_sha = str(review_status["candidate_head_sha"])
    build_revisions = {str(receipt["build_revision"]) for _, receipt in by_region.values()}
    if len(build_revisions) > 1:
        raise ValueError("R2GI_BUILD_REVISION_CONFLICT")
    build_revision = next(iter(build_revisions), None)
    missing_regions = sorted(EXPECTED_REGIONS - set(by_region))
    findings: list[dict[str, Any]] = []
    region_rows: list[dict[str, Any]] = []
    unresolved_regions: list[str] = []

    for region_id in sorted(EXPECTED_REGIONS):
        if region_id not in by_region:
            region_rows.append(
                {
                    "evidence_region_id": region_id,
                    "state": "HUMAN_RECEIPT_REQUIRED",
                    "receipt_ingested": False,
                    "geometry_materialization_authorized": False,
                }
            )
            continue
        envelope, receipt = by_region[region_id]
        if receipt["candidate_head_sha"] != candidate_head_sha:
            raise ValueError(f"R2GI_CANDIDATE_REVISION_MISMATCH:{region_id}")
        if receipt["build_revision"] != build_revision:
            raise ValueError(f"R2GI_BUILD_REVISION_MISMATCH:{region_id}")
        region_findings = [_decision_finding(region_id, receipt, decision) for decision in receipt["decisions"]]
        findings.extend(region_findings)
        has_unresolved = any(
            finding["human_decision"] == "UNRESOLVED_FROM_CURRENT_VIEW" for finding in region_findings
        )
        if has_unresolved:
            unresolved_regions.append(region_id)
        region_rows.append(
            {
                "evidence_region_id": region_id,
                "candidate_head_sha": receipt["candidate_head_sha"],
                "build_revision": receipt["build_revision"],
                "source_code": receipt["source_code"],
                "source_version_id": receipt["source_version_id"],
                "source_sha256": receipt["source_sha256"],
                "page_id": receipt["page_id"],
                "transform_id": receipt["transform_id"],
                "state": "INGESTED_REVIEW_FINDINGS_ONLY",
                "receipt_ingested": True,
                "runtime_audit_decision_id": envelope["decision_id"],
                "receipt_sha256": _sha256(receipt),
                "finding_count": len(region_findings),
                "unresolved_gap_count": sum(
                    1 for finding in region_findings if finding["human_decision"] == "UNRESOLVED_FROM_CURRENT_VIEW"
                ),
                "geometry_materialization_authorized": False,
            }
        )

    if missing_regions:
        state = "BLOCKED_HUMAN_RECEIPT_REQUIRED"
        next_gate = "R2HR_HUMAN_REVIEW_REQUIRED"
    elif unresolved_regions:
        state = "BLOCKED_UNRESOLVED_HUMAN_REVIEW"
        next_gate = "R2HR_ADDITIONAL_SOURCE_OR_REVIEW_REQUIRED"
    else:
        state = "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW"
        next_gate = "R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_REQUIRED"

    report = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "report_type": "CEW_PWB005_R2GI_GOVERNED_REVIEW_INGEST_REPORT_v1",
        "candidate_head_sha": candidate_head_sha,
        "build_revision": build_revision,
        "state": state,
        "next_gate": next_gate,
        "region_coverage": f"{len(by_region)}/{len(EXPECTED_REGIONS)}",
        "missing_regions": missing_regions,
        "unresolved_regions": sorted(unresolved_regions),
        "regions": region_rows,
        "review_findings": findings,
        "review_findings_are_geometry": False,
        "geometry_materialization_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    report["report_sha256"] = _sha256(report)
    return report


def load_envelopes(input_dir: Path) -> list[dict[str, Any]]:
    if not input_dir.exists():
        return []
    if not input_dir.is_dir():
        raise ValueError("R2GI_INPUT_PATH_NOT_DIRECTORY")
    return [_load(path) for path in sorted(input_dir.glob("*.json"))]


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "ingest_report.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed ingest for CEW PWB-005 R2HR human review receipts")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    envelopes = load_envelopes(args.input_dir)
    report = ingest_envelopes(envelopes)
    target = write_report(report, args.output_dir)
    print(f"R2GI_STATE = {report['state']}")
    print(f"R2GI_REGION_COVERAGE = {report['region_coverage']}")
    print(f"R2GI_BUILD_REVISION = {report['build_revision']}")
    print(f"R2GI_NEXT_GATE = {report['next_gate']}")
    print("R2GI_GEOMETRY_MATERIALIZATION_AUTHORIZED = false")
    print("R2GI_CANONICAL_WRITE_AUTHORIZED = false")
    print(f"R2GI_REPORT = {target.relative_to(ROOT)}")
    if args.require_complete and report["state"] != "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
