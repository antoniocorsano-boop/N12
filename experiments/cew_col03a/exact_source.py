from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.cew_col03a.governed_inputs import collect_governed_positive_evidence
from experiments.cew_col03a.occurrence_ledger import (
    QUALIFIED_BASE_SHA,
    attach_exact_source_geometry,
    build_ledger_closure,
    build_occurrence_ledger,
    build_proposal_geometry_index,
    build_reconciliation_report,
    canonical_bytes,
    collapse_strong_lineage,
)


EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_SEARCH_REPLAY_SHA256 = "11dc8a03789628c6167a8c7cc10fe41d318c5fa22535065598e1c36aa56fd1ac"
EXPECTED_RECONCILIATION_REPLAY_SHA256 = "b68526f71e77a072b0849d2d3cd2fcab886b03c86a99681717d7aee5cd13bf3c"
EXPECTED_REPAIR_MANIFEST_SHA256 = "e688c22753d8804edfdded8e9f89651c60b7a864a016b400a027d708329b1228"

COL02_ROOT = Path("evidence/cew-col02/footprint-text-binding")
OUTPUT_ROOT = Path("evidence/cew-col03a")

PROTOTYPE_RECEIPT_PATH = Path("governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json")
PROTOTYPE_GUIDED_RECEIPT_PATH = Path("governance/cew-col02/COL02_PROTOTYPE_GUIDED_HUMAN_REVIEW_v1.json")
MOBILE_RECEIPT_PATH = Path("governance/cew-col02/COL02_RESIDUAL_MOBILE_HUMAN_REVIEW_v1.json")
RECONCILIATION_RECEIPT_PATH = Path("governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json")
REPAIR_REVIEW_RECEIPT_PATH = Path("governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v2.json")

AUDIT_PATH = COL02_ROOT / "col02-audit.json"
PROTOTYPE_SEARCH_PATH = COL02_ROOT / "col02-prototype-guided-search.json"
RECONCILIATION_MANIFEST_PATH = COL02_ROOT / "col02-residual-occurrence-reconciliation.json"
REPAIR_MANIFEST_PATH = COL02_ROOT / "col02-axis-aware-whole-symbol-repair.json"
COVERAGE_CLOSURE_PATH = COL02_ROOT / "col02-occurrence-coverage-closure.json"

LEDGER_NAME = "column-occurrence-ledger.json"
RECONCILIATION_NAME = "column-occurrence-reconciliation.json"
CLOSURE_NAME = "column-occurrence-ledger-closure.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _pretty_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_source(source: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ValueError("COL-03A source must be an object")
    return {
        "source_version_id": source.get("source_version_id"),
        "source_path": source.get("source_path") or source.get("path"),
        "sha256": source.get("sha256") or source.get("source_sha256"),
        "page_id": source.get("page_id"),
        "page_index": source.get("page_index"),
        "page_transform_id": source.get("page_transform_id"),
    }


def build_col03a_from_payloads(
    *,
    evidence_items: list[dict[str, Any]],
    proposals: dict[str, Any],
    repair_manifest: dict[str, Any],
    col02_closure: dict[str, Any],
    source: dict[str, Any],
    qualified_base_sha: str = QUALIFIED_BASE_SHA,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build the three COL-03A payloads from already-governed evidence only."""
    normalized_source = _normalized_source(source)
    proposal_index = build_proposal_geometry_index(proposals)
    attached = attach_exact_source_geometry(
        evidence_items=list(evidence_items),
        proposal_index=proposal_index,
        repair_manifest=repair_manifest,
        source=normalized_source,
    )
    groups = collapse_strong_lineage(attached)
    ledger_source = {
        "source_version_id": normalized_source["source_version_id"],
        "source_path": normalized_source["source_path"],
        "source_sha256": normalized_source["sha256"],
        "page_id": normalized_source["page_id"],
        "page_index": normalized_source["page_index"],
        "page_transform_id": normalized_source["page_transform_id"],
    }
    ledger = build_occurrence_ledger(records=groups, source=ledger_source)
    reconciliation = build_reconciliation_report(
        evidence_items=list(evidence_items),
        occurrences=ledger["occurrences"],
        conflicts=ledger["conflicts"],
    )
    closure = build_ledger_closure(
        ledger=ledger,
        reconciliation=reconciliation,
        col02_closure=col02_closure,
        qualified_base_sha=qualified_base_sha,
    )
    return ledger, reconciliation, closure


def _require_deterministic_build(
    *,
    evidence_items: list[dict[str, Any]],
    proposals: dict[str, Any],
    repair_manifest: dict[str, Any],
    col02_closure: dict[str, Any],
    source: dict[str, Any],
    qualified_base_sha: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    first = build_col03a_from_payloads(
        evidence_items=evidence_items,
        proposals=proposals,
        repair_manifest=repair_manifest,
        col02_closure=col02_closure,
        source=source,
        qualified_base_sha=qualified_base_sha,
    )
    second = build_col03a_from_payloads(
        evidence_items=list(reversed(evidence_items)),
        proposals=proposals,
        repair_manifest=repair_manifest,
        col02_closure=col02_closure,
        source=source,
        qualified_base_sha=qualified_base_sha,
    )
    if any(canonical_bytes(a) != canonical_bytes(b) for a, b in zip(first, second, strict=True)):
        raise ValueError("COL-03A build is not deterministic under evidence ordering")
    return first


def write_col03a_artifacts(
    *,
    evidence_items_path: Path,
    proposals_path: Path,
    repair_manifest_path: Path,
    col02_closure_path: Path,
    source_path: Path,
    output_root: Path,
    qualified_base_sha: str = QUALIFIED_BASE_SHA,
) -> dict[str, Any]:
    evidence_items = _load_json(evidence_items_path)
    proposals = _load_json(proposals_path)
    repair_manifest = _load_json(repair_manifest_path)
    col02_closure = _load_json(col02_closure_path)
    source = _load_json(source_path)
    if not isinstance(evidence_items, list):
        raise ValueError("normalized governed evidence must be a list")

    ledger, reconciliation, closure = _require_deterministic_build(
        evidence_items=evidence_items,
        proposals=proposals,
        repair_manifest=repair_manifest,
        col02_closure=col02_closure,
        source=source,
        qualified_base_sha=qualified_base_sha,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "ledger": output_root / LEDGER_NAME,
        "reconciliation": output_root / RECONCILIATION_NAME,
        "closure": output_root / CLOSURE_NAME,
    }
    output_paths["ledger"].write_bytes(_pretty_bytes(ledger))
    output_paths["reconciliation"].write_bytes(_pretty_bytes(reconciliation))
    output_paths["closure"].write_bytes(_pretty_bytes(closure))

    return {
        "occurrence_count": ledger["occurrence_count"],
        "conflict_count": ledger["conflict_count"],
        "occurrence_ledger_complete": closure["occurrence_ledger_complete"],
        "ledger_sha256": _file_sha256(output_paths["ledger"]),
        "reconciliation_sha256": _file_sha256(output_paths["reconciliation"]),
        "closure_sha256": _file_sha256(output_paths["closure"]),
    }


def _validate_fresh_col02_lineage(
    *,
    audit: dict[str, Any],
    prototype_search: dict[str, Any],
    reconciliation_manifest: dict[str, Any],
    repair_manifest_bytes: bytes,
    repair_manifest: dict[str, Any],
    coverage_closure: dict[str, Any],
) -> dict[str, Any]:
    source = audit.get("source")
    if not isinstance(source, dict):
        raise ValueError("fresh COL-02 audit source missing")
    if source.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("fresh COL-02 source SHA drift")
    if audit.get("candidate_generation", {}).get("proposal_count") != 611:
        raise ValueError("fresh COL-02 proposal count drift")
    if prototype_search.get("replay_sha256") != EXPECTED_SEARCH_REPLAY_SHA256:
        raise ValueError("fresh prototype-guided search replay drift")
    if prototype_search.get("source", {}).get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("prototype-guided search source drift")
    if reconciliation_manifest.get("replay_sha256") != EXPECTED_RECONCILIATION_REPLAY_SHA256:
        raise ValueError("fresh residual reconciliation replay drift")
    if reconciliation_manifest.get("residual_candidate_review_complete") is not True:
        raise ValueError("fresh residual reconciliation is incomplete")
    repair_digest = hashlib.sha256(repair_manifest_bytes).hexdigest()
    if repair_digest != EXPECTED_REPAIR_MANIFEST_SHA256:
        raise ValueError("fresh repair manifest digest drift")
    if repair_manifest.get("proposal_count") != 611:
        raise ValueError("fresh repair manifest proposal count drift")
    if coverage_closure.get("occurrence_coverage_complete") is not True:
        raise ValueError("fresh COL-02 occurrence coverage is incomplete")
    if coverage_closure.get("reconciliation_replay_sha256") != EXPECTED_RECONCILIATION_REPLAY_SHA256:
        raise ValueError("coverage closure reconciliation replay drift")
    if coverage_closure.get("reviewed_repair_manifest_sha256") != EXPECTED_REPAIR_MANIFEST_SHA256:
        raise ValueError("coverage closure repair digest drift")
    return _normalized_source(source)


def _load_real_governed_evidence(
    *,
    reconciliation_manifest: dict[str, Any],
    repair_manifest: dict[str, Any],
    coverage_closure: dict[str, Any],
) -> list[dict[str, Any]]:
    return collect_governed_positive_evidence(
        prototype_receipt=_load_json(PROTOTYPE_RECEIPT_PATH),
        prototype_guided_receipt=_load_json(PROTOTYPE_GUIDED_RECEIPT_PATH),
        mobile_receipt=_load_json(MOBILE_RECEIPT_PATH),
        reconciliation_manifest=reconciliation_manifest,
        reconciliation_receipt=_load_json(RECONCILIATION_RECEIPT_PATH),
        repair_manifest=repair_manifest,
        repair_review_receipt=_load_json(REPAIR_REVIEW_RECEIPT_PATH),
        coverage_closure=coverage_closure,
    )


def main() -> None:
    from experiments.cew_col02.axis_aware_whole_symbol_exact_source import (
        _regenerate_source_analysis_and_proposals,
    )

    audit = _load_json(AUDIT_PATH)
    prototype_search = _load_json(PROTOTYPE_SEARCH_PATH)
    reconciliation_manifest = _load_json(RECONCILIATION_MANIFEST_PATH)
    repair_manifest_bytes = REPAIR_MANIFEST_PATH.read_bytes()
    repair_manifest = json.loads(repair_manifest_bytes.decode("utf-8"))
    coverage_closure = _load_json(COVERAGE_CLOSURE_PATH)
    source = _validate_fresh_col02_lineage(
        audit=audit,
        prototype_search=prototype_search,
        reconciliation_manifest=reconciliation_manifest,
        repair_manifest_bytes=repair_manifest_bytes,
        repair_manifest=repair_manifest,
        coverage_closure=coverage_closure,
    )
    evidence_items = _load_real_governed_evidence(
        reconciliation_manifest=reconciliation_manifest,
        repair_manifest=repair_manifest,
        coverage_closure=coverage_closure,
    )

    _image, _analysis, proposals = _regenerate_source_analysis_and_proposals()
    ledger, reconciliation, closure = _require_deterministic_build(
        evidence_items=evidence_items,
        proposals=proposals,
        repair_manifest=repair_manifest,
        col02_closure=coverage_closure,
        source=source,
        qualified_base_sha=QUALIFIED_BASE_SHA,
    )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    ledger_path = OUTPUT_ROOT / LEDGER_NAME
    reconciliation_path = OUTPUT_ROOT / RECONCILIATION_NAME
    closure_path = OUTPUT_ROOT / CLOSURE_NAME
    ledger_path.write_bytes(_pretty_bytes(ledger))
    reconciliation_path.write_bytes(_pretty_bytes(reconciliation))
    closure_path.write_bytes(_pretty_bytes(closure))

    summary = {
        "status": "COMPLETE" if closure["occurrence_ledger_complete"] else "BLOCKED",
        "occurrence_count": ledger["occurrence_count"],
        "conflict_count": ledger["conflict_count"],
        "occurrence_ledger_complete": closure["occurrence_ledger_complete"],
        "ledger_sha256": _file_sha256(ledger_path),
        "reconciliation_sha256": _file_sha256(reconciliation_path),
        "closure_sha256": _file_sha256(closure_path),
    }
    print("CEW_COL03A_OCCURRENCE_LEDGER=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
