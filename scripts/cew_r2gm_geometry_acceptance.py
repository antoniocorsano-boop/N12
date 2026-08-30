#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import cew_professional_gap_review as gap_review

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation" / "CEW_PWB005_R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_CONTRACT_v1.json"
R2M_ROOT = ROOT / ".cew_raster_geometry_consolidation"
R2M_MANIFEST = R2M_ROOT / "manifest.json"
EXPECTED_REGIONS = set(gap_review.EXPECTED_REGIONS)
RECEIPT_TYPE = "CEW_PWB005_R2GM_HUMAN_GEOMETRY_ACCEPTANCE_v1"
AUDIT_ENVELOPE_TYPE = "CEW_PWB005_R2GM_RUNTIME_AUDIT_ENVELOPE_v1"
ALLOWED_DECISIONS = {
    "ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY",
    "REJECT_REGION_DOCUMENT_GEOMETRY",
    "DEFER_NEEDS_ADDITIONAL_SOURCE",
}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_value(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"R2GM_REQUIRED_ARTIFACT_MISSING:{path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"R2GM_JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def _contract() -> dict[str, Any]:
    payload = _load(CONTRACT_PATH)
    if payload.get("contract_id") != "CEW_PWB005_R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_CONTRACT_v1":
        raise ValueError("R2GM_CONTRACT_ID_MISMATCH")
    if payload.get("canonical_write_authorized") is not False:
        raise ValueError("R2GM_CONTRACT_CANONICAL_WRITE_DRIFT")
    if payload.get("engineering_authority_effect") != "NONE":
        raise ValueError("R2GM_CONTRACT_ENGINEERING_AUTHORITY_DRIFT")
    return payload


def _validate_r2gi_ready(report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise ValueError("R2GM_R2GI_REPORT_REQUIRED")
    if report.get("report_type") != "CEW_PWB005_R2GI_GOVERNED_REVIEW_INGEST_REPORT_v1":
        raise ValueError("R2GM_R2GI_REPORT_TYPE_MISMATCH")
    if report.get("state") != "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW":
        raise ValueError("R2GM_R2GI_NOT_READY")
    if report.get("next_gate") != "R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_REQUIRED":
        raise ValueError("R2GM_R2GI_NEXT_GATE_MISMATCH")
    if report.get("region_coverage") != "4/4" or report.get("missing_regions") or report.get("unresolved_regions"):
        raise ValueError("R2GM_R2GI_COVERAGE_NOT_READY")
    if report.get("review_findings_are_geometry") is not False:
        raise ValueError("R2GM_R2GI_FINDING_AUTHORITY_DRIFT")
    if report.get("geometry_materialization_authorized") is not False:
        raise ValueError("R2GM_R2GI_GEOMETRY_AUTHORITY_DRIFT")
    if report.get("canonical_write_authorized") is not False:
        raise ValueError("R2GM_R2GI_CANONICAL_WRITE_DRIFT")


def _r2m_region(report: dict[str, Any], region_id: str) -> dict[str, Any]:
    manifest = _load(R2M_MANIFEST)
    candidate = str(report.get("candidate_head_sha", ""))
    if manifest.get("build_revision") != candidate:
        raise ValueError("R2GM_R2M_CANDIDATE_REVISION_MISMATCH")
    if manifest.get("region_coverage") != "4/4":
        raise ValueError("R2GM_R2M_REGION_COVERAGE_MISMATCH")
    if manifest.get("r2c_scene_adapter_authorized") is not False:
        raise ValueError("R2GM_R2M_PREMATURE_SCENE_AUTHORITY")
    entries = {row["evidence_region_id"]: row for row in manifest.get("regions") or []}
    if set(entries) != EXPECTED_REGIONS or region_id not in entries:
        raise ValueError("R2GM_R2M_REGION_SET_MISMATCH")
    entry = entries[region_id]
    path = R2M_ROOT / entry["result_filename"]
    if _hash_file(path) != entry["result_sha256"]:
        raise ValueError(f"R2GM_R2M_RESULT_SHA_MISMATCH:{region_id}")
    payload = _load(path)
    if payload.get("evidence_region_id") != region_id:
        raise ValueError(f"R2GM_R2M_REGION_ID_MISMATCH:{region_id}")
    return payload


def _source_point(normalized: list[float], source_rect: list[float]) -> list[float]:
    x0, y0, x1, y1 = [float(value) for value in source_rect]
    return [
        round(x0 + float(normalized[0]) * (x1 - x0), 6),
        round(y0 + float(normalized[1]) * (y1 - y0), 6),
    ]


def _region_r2gi_row(report: dict[str, Any], region_id: str) -> dict[str, Any]:
    rows = [row for row in report.get("regions") or [] if row.get("evidence_region_id") == region_id]
    if len(rows) != 1:
        raise ValueError(f"R2GM_R2GI_REGION_ROW_MISMATCH:{region_id}")
    row = rows[0]
    if row.get("state") != "INGESTED_REVIEW_FINDINGS_ONLY" or row.get("receipt_ingested") is not True:
        raise ValueError(f"R2GM_R2GI_REGION_NOT_INGESTED:{region_id}")
    return row


def build_region_proposal(report: dict[str, Any], region_id: str) -> dict[str, Any]:
    _contract()
    _validate_r2gi_ready(report)
    if region_id not in EXPECTED_REGIONS:
        raise ValueError("R2GM_REGION_NOT_ALLOWED")
    r2gi_region = _region_r2gi_row(report, region_id)
    r2m = _r2m_region(report, region_id)

    for key in ("source_code", "source_version_id", "source_sha256", "page_id", "transform_id"):
        if r2gi_region.get(key) != r2m.get(key):
            raise ValueError(f"R2GM_UPSTREAM_PROVENANCE_MISMATCH:{region_id}:{key}")

    base_primitives: list[dict[str, Any]] = []
    for row in r2m.get("consolidated_candidates") or []:
        primitive = {
            "primitive_id": "R2GM-BASE-" + str(row["consolidated_candidate_id"]),
            "origin": "R2M_CONSOLIDATED_RASTER_CANDIDATE",
            "geometry_type": "LINE",
            "coordinate_space": "EVIDENCE_REGION_NORMALIZED_0_1",
            "geometry_normalized": row["geometry_normalized"],
            "geometry_source_page_pt": row["geometry_source_page_pt"],
            "support_candidate_ids": list(row["support_candidate_ids"]),
            "source_finding_id": None,
            "human_supported_continuity": False,
        }
        base_primitives.append(primitive)

    findings = [row for row in report.get("review_findings") or [] if row.get("evidence_region_id") == region_id]
    bridge_primitives: list[dict[str, Any]] = []
    for finding in sorted(findings, key=lambda row: row["finding_id"]):
        if finding.get("finding_is_geometry") is not False or finding.get("geometry_materialization_authorized") is not False:
            raise ValueError(f"R2GM_R2GI_FINDING_AUTHORITY_DRIFT:{finding.get('finding_id')}")
        if finding.get("human_decision") != "SUPPORTED_CONTINUITY_HYPOTHESIS":
            continue
        endpoints = finding["bridge_endpoints_normalized"]
        primitive = {
            "primitive_id": "R2GM-BRIDGE-" + str(finding["finding_id"]),
            "origin": "R2GI_HUMAN_SUPPORTED_CONTINUITY",
            "geometry_type": "LINE",
            "coordinate_space": "EVIDENCE_REGION_NORMALIZED_0_1",
            "geometry_normalized": {
                "a": endpoints["a"],
                "b": endpoints["b"],
            },
            "geometry_source_page_pt": {
                "a": _source_point(endpoints["a"], r2m["source_rect_pt"]),
                "b": _source_point(endpoints["b"], r2m["source_rect_pt"]),
            },
            "support_candidate_ids": list(finding["candidate_ids"]),
            "source_finding_id": finding["finding_id"],
            "human_supported_continuity": True,
        }
        bridge_primitives.append(primitive)

    primitives = sorted(base_primitives + bridge_primitives, key=lambda row: row["primitive_id"])
    proposal_core = {
        "proposal_contract": "CEW_PWB005_R2GM_REGION_GEOMETRY_PROPOSAL_v1",
        "candidate_head_sha": report["candidate_head_sha"],
        "r2gi_report_sha256": report["report_sha256"],
        "evidence_region_id": region_id,
        "source_code": r2m["source_code"],
        "source_version_id": r2m["source_version_id"],
        "source_sha256": r2m["source_sha256"],
        "page_id": r2m["page_id"],
        "transform_id": r2m["transform_id"],
        "source_rect_pt": r2m["source_rect_pt"],
        "coordinate_space": "EVIDENCE_REGION_NORMALIZED_0_1",
        "base_primitive_count": len(base_primitives),
        "human_supported_bridge_count": len(bridge_primitives),
        "primitive_count": len(primitives),
        "primitives": primitives,
        "proposal_is_document_geometry": False,
        "proposal_requires_explicit_human_acceptance": True,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    proposal_sha = _hash_value(proposal_core)
    return {
        **proposal_core,
        "proposal_id": "R2GM-PROP-" + proposal_sha[:20],
        "proposal_sha256": proposal_sha,
    }


def validate_receipt(receipt: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ValueError("R2GM_RECEIPT_OBJECT_REQUIRED")
    required = {
        "schema_version",
        "receipt_type",
        "candidate_head_sha",
        "r2gi_report_sha256",
        "proposal_id",
        "proposal_sha256",
        "evidence_region_id",
        "source_code",
        "source_version_id",
        "source_sha256",
        "page_id",
        "transform_id",
        "proposal_primitive_count",
        "reviewer_label",
        "reviewer_attestation",
        "reviewed_at",
        "decision",
        "rationale",
        "receipt_authority",
        "document_geometry_materialization_authorized",
        "r2c_scene_adapter_authorized",
        "technical_identity_authorized",
        "structural_identity_authorized",
        "canonical_write_authorized",
        "engineering_authority_effect",
    }
    if set(receipt) != required:
        raise ValueError("R2GM_RECEIPT_FIELD_SET_MISMATCH")
    if receipt.get("schema_version") != "1.0" or receipt.get("receipt_type") != RECEIPT_TYPE:
        raise ValueError("R2GM_RECEIPT_TYPE_MISMATCH")
    for key in (
        "candidate_head_sha",
        "r2gi_report_sha256",
        "proposal_id",
        "proposal_sha256",
        "evidence_region_id",
        "source_code",
        "source_version_id",
        "source_sha256",
        "page_id",
        "transform_id",
    ):
        if receipt.get(key) != proposal.get(key):
            raise ValueError(f"R2GM_RECEIPT_PROVENANCE_MISMATCH:{key}")
    if receipt.get("proposal_primitive_count") != proposal.get("primitive_count"):
        raise ValueError("R2GM_RECEIPT_PROPOSAL_COUNT_MISMATCH")
    label = receipt.get("reviewer_label")
    if not isinstance(label, str) or not label.strip() or len(label.strip()) > 200:
        raise ValueError("R2GM_REVIEWER_LABEL_INVALID")
    if receipt.get("reviewer_attestation") is not True:
        raise ValueError("R2GM_REVIEWER_ATTESTATION_REQUIRED")
    reviewed_at = receipt.get("reviewed_at")
    if not isinstance(reviewed_at, str):
        raise ValueError("R2GM_REVIEWED_AT_INVALID")
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("R2GM_REVIEWED_AT_INVALID") from exc
    decision = receipt.get("decision")
    if decision not in ALLOWED_DECISIONS:
        raise ValueError("R2GM_DECISION_INVALID")
    rationale = receipt.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip() or len(rationale.strip()) > 4000:
        raise ValueError("R2GM_RATIONALE_INVALID")
    if receipt.get("receipt_authority") != "HUMAN_DOCUMENT_GEOMETRY_ACCEPTANCE_ONLY":
        raise ValueError("R2GM_RECEIPT_AUTHORITY_INVALID")
    expected_materialization = decision == "ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY"
    if receipt.get("document_geometry_materialization_authorized") is not expected_materialization:
        raise ValueError("R2GM_DOCUMENT_GEOMETRY_AUTHORITY_MISMATCH")
    if receipt.get("r2c_scene_adapter_authorized") is not False:
        raise ValueError("R2GM_RECEIPT_PREMATURE_R2C_AUTHORITY")
    for key in ("technical_identity_authorized", "structural_identity_authorized", "canonical_write_authorized"):
        if receipt.get(key) is not False:
            raise ValueError(f"R2GM_RECEIPT_AUTHORITY_DRIFT:{key}")
    if receipt.get("engineering_authority_effect") != "NONE":
        raise ValueError("R2GM_ENGINEERING_AUTHORITY_FORBIDDEN")
    return receipt


def _accepted_geometry(proposal: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any] | None:
    if receipt["decision"] != "ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY":
        return None
    geometry = {
        "geometry_contract": "CEW_PWB005_R2GM_ACCEPTED_DOCUMENT_GEOMETRY_v1",
        "candidate_head_sha": proposal["candidate_head_sha"],
        "r2gi_report_sha256": proposal["r2gi_report_sha256"],
        "proposal_id": proposal["proposal_id"],
        "proposal_sha256": proposal["proposal_sha256"],
        "evidence_region_id": proposal["evidence_region_id"],
        "source_code": proposal["source_code"],
        "source_version_id": proposal["source_version_id"],
        "source_sha256": proposal["source_sha256"],
        "page_id": proposal["page_id"],
        "transform_id": proposal["transform_id"],
        "source_rect_pt": proposal["source_rect_pt"],
        "coordinate_space": proposal["coordinate_space"],
        "primitives": proposal["primitives"],
        "primitive_count": proposal["primitive_count"],
        "accepted_by": receipt["reviewer_label"],
        "accepted_at": receipt["reviewed_at"],
        "acceptance_rationale": receipt["rationale"],
        "authority": "HUMAN_ACCEPTED_DOCUMENT_GEOMETRY",
        "is_document_geometry": True,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    geometry["accepted_geometry_sha256"] = _hash_value(geometry)
    return geometry


def audit_envelope(task_id: str, receipt: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    validated = validate_receipt(receipt, proposal)
    accepted = _accepted_geometry(proposal, validated)
    digest = _hash_value(validated)
    region = validated["evidence_region_id"].replace("/", "-")
    decision_id = f"R2GM-{region}-{validated['candidate_head_sha'][:12]}-{digest[:16]}"
    decision = validated["decision"]
    if decision == "ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY":
        next_gate = "R2GM_ALL_REGION_ACCEPTANCE_AGGREGATION_REQUIRED"
    elif decision == "REJECT_REGION_DOCUMENT_GEOMETRY":
        next_gate = "R2_RASTER_GEOMETRY_REWORK_REQUIRED"
    else:
        next_gate = "R2GM_ADDITIONAL_SOURCE_REQUIRED"
    return {
        "decision_id": decision_id,
        "task_id": task_id,
        "residual_id": validated["evidence_region_id"],
        "timestamp": validated["reviewed_at"],
        "receipt_type": AUDIT_ENVELOPE_TYPE,
        "r2gm_receipt": validated,
        "accepted_document_geometry": accepted,
        "authority": "RUNTIME_AUDIT_ONLY",
        "canonical_write": False,
        "engineering_authority_effect": "NONE",
        "next_gate": next_gate,
    }


def _validate_envelope(envelope: dict[str, Any], report: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    required = {
        "decision_id",
        "task_id",
        "residual_id",
        "timestamp",
        "receipt_type",
        "r2gm_receipt",
        "accepted_document_geometry",
        "authority",
        "canonical_write",
        "engineering_authority_effect",
        "next_gate",
    }
    if not isinstance(envelope, dict) or set(envelope) != required:
        raise ValueError("R2GM_AUDIT_ENVELOPE_FIELD_SET_MISMATCH")
    if envelope.get("receipt_type") != AUDIT_ENVELOPE_TYPE:
        raise ValueError("R2GM_AUDIT_ENVELOPE_TYPE_MISMATCH")
    if envelope.get("authority") != "RUNTIME_AUDIT_ONLY" or envelope.get("canonical_write") is not False:
        raise ValueError("R2GM_AUDIT_AUTHORITY_DRIFT")
    if envelope.get("engineering_authority_effect") != "NONE":
        raise ValueError("R2GM_AUDIT_ENGINEERING_AUTHORITY_FORBIDDEN")
    receipt = envelope.get("r2gm_receipt")
    if not isinstance(receipt, dict):
        raise ValueError("R2GM_AUDIT_RECEIPT_REQUIRED")
    region_id = str(receipt.get("evidence_region_id", ""))
    if region_id not in EXPECTED_REGIONS or envelope.get("residual_id") != region_id:
        raise ValueError("R2GM_AUDIT_REGION_MISMATCH")
    proposal = build_region_proposal(report, region_id)
    validated = validate_receipt(receipt, proposal)
    expected = audit_envelope(str(envelope.get("task_id", "")), validated, proposal)
    if envelope.get("decision_id") != expected["decision_id"]:
        raise ValueError("R2GM_AUDIT_DECISION_ID_MISMATCH")
    if _canonical(envelope.get("accepted_document_geometry")) != _canonical(expected["accepted_document_geometry"]):
        raise ValueError("R2GM_ACCEPTED_GEOMETRY_TAMPERED")
    if envelope.get("next_gate") != expected["next_gate"]:
        raise ValueError("R2GM_AUDIT_NEXT_GATE_MISMATCH")
    return region_id, validated, expected["accepted_document_geometry"]


def aggregate(report: dict[str, Any], envelopes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    _contract()
    try:
        _validate_r2gi_ready(report)
    except ValueError as exc:
        if str(exc) in {"R2GM_R2GI_NOT_READY", "R2GM_R2GI_COVERAGE_NOT_READY"}:
            return {
                "schema_version": "1.0",
                "report_type": "CEW_PWB005_R2GM_GEOMETRY_ACCEPTANCE_REPORT_v1",
                "candidate_head_sha": report.get("candidate_head_sha"),
                "state": "BLOCKED_R2GI_NOT_READY",
                "reason": str(exc),
                "next_gate": "R2GI_GOVERNED_REVIEW_INGEST_REQUIRED",
                "region_coverage": "0/4",
                "accepted_document_geometry": [],
                "document_geometry_materialized_region_count": 0,
                "r2c_scene_adapter_authorized": False,
                "technical_identity_authorized": False,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
                "engineering_authority_effect": "NONE",
            }
        raise

    by_region: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]] = {}
    for envelope in envelopes:
        region_id, receipt, accepted = _validate_envelope(envelope, report)
        if region_id in by_region:
            raise ValueError(f"R2GM_DUPLICATE_REGION_RECEIPT:{region_id}")
        by_region[region_id] = (envelope, receipt, accepted)

    region_rows: list[dict[str, Any]] = []
    accepted_geometry: list[dict[str, Any]] = []
    rejected_regions: list[str] = []
    deferred_regions: list[str] = []
    missing_regions: list[str] = []
    for region_id in sorted(EXPECTED_REGIONS):
        proposal = build_region_proposal(report, region_id)
        if region_id not in by_region:
            missing_regions.append(region_id)
            region_rows.append({
                "evidence_region_id": region_id,
                "state": "GEOMETRY_ACCEPTANCE_REQUIRED",
                "proposal_id": proposal["proposal_id"],
                "proposal_sha256": proposal["proposal_sha256"],
                "primitive_count": proposal["primitive_count"],
                "receipt_ingested": False,
                "document_geometry_materialized": False,
            })
            continue
        envelope, receipt, accepted = by_region[region_id]
        decision = receipt["decision"]
        if decision == "REJECT_REGION_DOCUMENT_GEOMETRY":
            rejected_regions.append(region_id)
        elif decision == "DEFER_NEEDS_ADDITIONAL_SOURCE":
            deferred_regions.append(region_id)
        if accepted is not None:
            accepted_geometry.append(accepted)
        region_rows.append({
            "evidence_region_id": region_id,
            "state": decision,
            "proposal_id": proposal["proposal_id"],
            "proposal_sha256": proposal["proposal_sha256"],
            "primitive_count": proposal["primitive_count"],
            "receipt_ingested": True,
            "runtime_audit_decision_id": envelope["decision_id"],
            "document_geometry_materialized": accepted is not None,
            "accepted_geometry_sha256": accepted.get("accepted_geometry_sha256") if accepted else None,
        })

    if rejected_regions:
        state = "BLOCKED_GEOMETRY_REJECTED"
        next_gate = "R2_RASTER_GEOMETRY_REWORK_REQUIRED"
    elif deferred_regions:
        state = "BLOCKED_ADDITIONAL_SOURCE_REQUIRED"
        next_gate = "R2GM_ADDITIONAL_SOURCE_REQUIRED"
    elif missing_regions:
        state = "BLOCKED_GEOMETRY_ACCEPTANCE_REQUIRED"
        next_gate = "R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_REQUIRED"
    else:
        state = "READY_FOR_R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER"
        next_gate = "R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER_REQUIRED"

    result = {
        "schema_version": "1.0",
        "report_type": "CEW_PWB005_R2GM_GEOMETRY_ACCEPTANCE_REPORT_v1",
        "candidate_head_sha": report["candidate_head_sha"],
        "r2gi_report_sha256": report["report_sha256"],
        "state": state,
        "next_gate": next_gate,
        "region_coverage": f"{len(by_region)}/{len(EXPECTED_REGIONS)}",
        "missing_regions": missing_regions,
        "rejected_regions": rejected_regions,
        "deferred_regions": deferred_regions,
        "regions": region_rows,
        "accepted_document_geometry": accepted_geometry,
        "document_geometry_materialized_region_count": len(accepted_geometry),
        "document_geometry_is_technical_identity": False,
        "document_geometry_is_structural_identity": False,
        "r2c_scene_adapter_authorized": state == "READY_FOR_R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER",
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    result["report_sha256"] = _hash_value(result)
    return result


def build_review_page(task_id: str, report: dict[str, Any], region_id: str) -> str:
    proposal = build_region_proposal(report, region_id)
    lines = []
    for primitive in proposal["primitives"]:
        a = primitive["geometry_normalized"]["a"]
        b = primitive["geometry_normalized"]["b"]
        css = "bridge" if primitive["origin"] == "R2GI_HUMAN_SUPPORTED_CONTINUITY" else "base"
        lines.append(
            f'<line class="{css}" x1="{float(a[0]):.8f}" y1="{float(a[1]):.8f}" '
            f'x2="{float(b[0]):.8f}" y2="{float(b[1]):.8f}" />'
        )
    embedded = json.dumps(proposal, ensure_ascii=False).replace("</", "<\\/")
    task_json = json.dumps(task_id, ensure_ascii=False)
    region_attr = html.escape(region_id, quote=True)
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Accettazione geometria documentale</title><style>
:root{{--ink:#17202a;--muted:#61707c;--line:#cfd6dc;--accent:#173f5f;--warn:#8a4b08;--ok:#286044}}*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui;background:#eef2f5;color:var(--ink)}}header{{background:#fff;border-bottom:1px solid var(--line);padding:12px 18px;display:flex;gap:12px;align-items:center}}main{{max-width:1450px;margin:auto;padding:16px}}a{{color:var(--accent);font-weight:700}}.notice{{background:#fff7e8;border-left:5px solid var(--warn);padding:10px 12px;margin-bottom:12px}}.layout{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(360px,.75fr);gap:14px}}.viewport{{position:sticky;top:12px;background:#111;border:1px solid #555;max-height:82vh;overflow:auto}}.viewport img{{display:block;width:100%;height:auto}}.viewport svg{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}.viewport line{{fill:none;vector-effect:non-scaling-stroke}}.viewport .base{{stroke:#00b7ff;stroke-width:1.4px;opacity:.82}}.viewport .bridge{{stroke:#ff2d55;stroke-width:3px;stroke-dasharray:9 6}}.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px;margin-bottom:10px}}.metric{{display:grid;grid-template-columns:1fr auto;gap:8px;border-bottom:1px solid #e5eaee;padding:7px 0}}label{{display:block;font-weight:700;margin:10px 0}}select,textarea,input{{width:100%;font:inherit;padding:8px;border:1px solid #aeb9c2;border-radius:6px;margin-top:4px}}button{{font:inherit;background:var(--accent);color:#fff;border:0;border-radius:6px;padding:10px 14px;font-weight:800;cursor:pointer}}.receipt{{background:#edf8f1;border-left:4px solid var(--ok);padding:10px;margin-top:10px}}.error{{background:#fff0f0;border-left:4px solid #a12622;padding:10px;margin-top:10px}}@media(max-width:900px){{.layout{{grid-template-columns:1fr}}.viewport{{position:relative;top:auto}}}}
</style></head><body><header><a href="/workbench?task={html.escape(task_id, quote=True)}">← Ambiente grafico</a><strong>Accettazione esplicita della geometria documentale</strong></header><main><div class="notice"><b>Decisione distinta:</b> qui non stai confermando una semplice ipotesi di continuità. Stai decidendo se l'intera geometria sovrapposta alla sorgente, identificata da un'impronta immutabile, può essere trattata come <b>geometria documentale accettata</b>. Anche se accettata, non diventa identità tecnica/strutturale, non modifica il canonico e non produce autorità ingegneristica.</div><div class="layout"><section><div class="viewport"><img src="/workbench/gap-review/assets/{region_attr}/source_crop_300.png" alt="Ritaglio della fonte verificata"><svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-label="Geometria proposta"><g>{''.join(lines)}</g></svg></div></section><section><div class="card"><h1>Proposta geometrica della regione</h1><div class="metric"><span>Primitive consolidate</span><b>{proposal['base_primitive_count']}</b></div><div class="metric"><span>Continuità supportate incluse</span><b>{proposal['human_supported_bridge_count']}</b></div><div class="metric"><span>Primitive totali</span><b>{proposal['primitive_count']}</b></div><p style="color:var(--muted)">Azzurro: geometria raster consolidata. Magenta tratteggiato: sole continuità già supportate dalla precedente revisione umana. L'accettazione riguarda esattamente questa composizione.</p><label>Decisione<select id="decision"><option value="">— seleziona —</option><option value="ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY">Accetta questa geometria documentale esatta</option><option value="REJECT_REGION_DOCUMENT_GEOMETRY">Respingi questa geometria</option><option value="DEFER_NEEDS_ADDITIONAL_SOURCE">Rimanda: serve un'altra fonte o vista</option></select></label><label>Motivazione<textarea id="rationale" rows="5" maxlength="4000" placeholder="Motiva la decisione sulla geometria complessiva visibile."></textarea></label><label>Revisore<input id="reviewerLabel" maxlength="200" placeholder="Nome, sigla o identificativo professionale"></label><label><input id="attestation" type="checkbox" style="width:auto"> Attesto di aver confrontato la geometria proposta con la sorgente visualizzata e di comprendere che l'accettazione è limitata alla geometria documentale.</label><button id="submitBtn">Registra decisione geometrica in CEW</button><div id="result" aria-live="polite"></div></div></section></div></main><script id="proposal" type="application/json">{embedded}</script><script>
const TASK={task_json};const P=JSON.parse(document.getElementById('proposal').textContent);const out=document.getElementById('result');
function collect(){{const decision=document.getElementById('decision').value;const rationale=document.getElementById('rationale').value.trim();const label=document.getElementById('reviewerLabel').value.trim();if(!decision)throw new Error('Seleziona una decisione.');if(!rationale)throw new Error('Inserisci la motivazione.');if(!label)throw new Error('Inserisci il revisore.');if(!document.getElementById('attestation').checked)throw new Error('È richiesta l’attestazione del revisore.');return {{schema_version:'1.0',receipt_type:'{RECEIPT_TYPE}',candidate_head_sha:P.candidate_head_sha,r2gi_report_sha256:P.r2gi_report_sha256,proposal_id:P.proposal_id,proposal_sha256:P.proposal_sha256,evidence_region_id:P.evidence_region_id,source_code:P.source_code,source_version_id:P.source_version_id,source_sha256:P.source_sha256,page_id:P.page_id,transform_id:P.transform_id,proposal_primitive_count:P.primitive_count,reviewer_label:label,reviewer_attestation:true,reviewed_at:new Date().toISOString(),decision,rationale,receipt_authority:'HUMAN_DOCUMENT_GEOMETRY_ACCEPTANCE_ONLY',document_geometry_materialization_authorized:decision==='ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY',r2c_scene_adapter_authorized:false,technical_identity_authorized:false,structural_identity_authorized:false,canonical_write_authorized:false,engineering_authority_effect:'NONE'}}}}
document.getElementById('submitBtn').onclick=async()=>{{try{{const receipt=collect();const r=await fetch('/api/workbench/geometry-acceptance/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{task:TASK,receipt}})}});const body=await r.json();if(!r.ok)throw new Error(body.reason||body.state||'Decisione respinta');out.className='receipt';out.textContent='Decisione registrata. Stato complessivo R2GM: '+body.geometry_acceptance_state+'. Prossimo gate: '+body.next_gate+'. Nessuna scrittura canonica è stata eseguita.';document.getElementById('submitBtn').disabled=true}}catch(e){{out.className='error';out.textContent=e.message}}}};
</script></body></html>'''
