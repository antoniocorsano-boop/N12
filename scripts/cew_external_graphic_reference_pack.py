#!/usr/bin/env python3
"""Build a fingerprinted EXTERNAL_REFERENCE graphic-library pack from human review.

Acquisition, review and library-pack creation are deliberately separate gates.
This builder accepts only explicit human ACCEPT_REFERENCE_EVIDENCE decisions
bound to exact acquired source/page fingerprints. DEFER is non-terminal: it may
appear in append-only history before one final ACCEPT or REJECT, but a non-empty
pack cannot be built until every queue item has a terminal human decision.
Discovery queries never supply semantic meaning.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ACQUISITION_SCHEMA = "CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1"
QUEUE_SCHEMA = "CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1"
DECISIONS_SCHEMA = "CEW_EXTERNAL_REFERENCE_REVIEW_DECISIONS_v1"
LIBRARY_SCHEMA = "CEW_GRAPHIC_REFERENCE_LIBRARY_INDEX_v1"
PACK_BUILDER_VERSION = "CEW_EXTERNAL_REFERENCE_PACK_BUILDER_v1"

ALLOWED_STATES = {
    "ACCEPT_REFERENCE_EVIDENCE",
    "REJECT_REFERENCE_EVIDENCE",
    "DEFER",
}
TERMINAL_STATES = {
    "ACCEPT_REFERENCE_EVIDENCE",
    "REJECT_REFERENCE_EVIDENCE",
}
NONTERMINAL_STATES = {"DEFER"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"REFERENCE_REVIEW_{field.upper()}_REQUIRED")
    return text


def _reviewed_at_key(decision: dict[str, Any]) -> tuple[datetime, str]:
    value = _require_text(decision.get("reviewed_at"), "reviewed_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("REFERENCE_REVIEW_REVIEWED_AT_INVALID") from exc
    if parsed.tzinfo is None:
        raise ValueError("REFERENCE_REVIEW_REVIEWED_AT_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc), _require_text(decision.get("decision_id"), "decision_id")


def _load_acquired_page_index(acquisition: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    if acquisition.get("schema") != ACQUISITION_SCHEMA:
        raise ValueError("REFERENCE_ACQUISITION_SCHEMA_INVALID")
    if acquisition.get("library_promotion_authorized") is not False:
        raise ValueError("REFERENCE_ACQUISITION_AUTHORITY_DRIFT")
    index: dict[tuple[str, int], dict[str, Any]] = {}
    for source in acquisition.get("acquired_sources") or []:
        source_id = str(source["source_id"])
        source_sha = str(source["source_sha256"])
        for evidence in source.get("selected_reference_evidence") or []:
            key = (source_id, int(evidence["page_index"]))
            row = {
                "source_id": source_id,
                "source_sha256": source_sha,
                "source_url": source.get("source_url"),
                "page_index": int(evidence["page_index"]),
                "page_number_1_based": int(evidence["page_number_1_based"]),
                "page_text_sha256": str(evidence["page_text_sha256"]),
                "page_feature_sha256": str(evidence["page_feature_sha256"]),
            }
            previous = index.get(key)
            if previous and previous != row:
                raise ValueError("REFERENCE_ACQUISITION_PAGE_FINGERPRINT_CONFLICT")
            index[key] = row
    return index


def _queue_index(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if queue.get("schema") != QUEUE_SCHEMA:
        raise ValueError("REFERENCE_REVIEW_QUEUE_SCHEMA_INVALID")
    if queue.get("automatic_library_pack_build_authorized") is not False:
        raise ValueError("REFERENCE_REVIEW_QUEUE_AUTHORITY_DRIFT")
    rows: dict[str, dict[str, Any]] = {}
    for item in queue.get("review_items") or []:
        item_id = str(item.get("review_item_id") or "")
        if not item_id or item_id in rows:
            raise ValueError("REFERENCE_REVIEW_ITEM_ID_INVALID_OR_DUPLICATE")
        if item.get("meaning") is not None:
            raise ValueError("REFERENCE_REVIEW_QUEUE_MUST_NOT_PREFILL_MEANING")
        rows[item_id] = item
    return rows


def _validate_decision_anchor(
    decision: dict[str, Any],
    queue_item: dict[str, Any],
    acquired_page: dict[str, Any],
) -> tuple[str, str, str]:
    state = str(decision.get("state") or "")
    if state not in ALLOWED_STATES:
        raise ValueError("REFERENCE_REVIEW_DECISION_STATE_INVALID")
    reviewer = _require_text(decision.get("reviewer"), "reviewer")
    rationale = _require_text(decision.get("rationale"), "rationale")
    _reviewed_at_key(decision)

    for field in ("source_id", "source_sha256", "page_index", "page_text_sha256", "page_feature_sha256"):
        expected = acquired_page[field]
        actual = decision.get(field)
        if field == "page_index":
            try:
                actual = int(actual)
            except (TypeError, ValueError) as exc:
                raise ValueError("REFERENCE_REVIEW_PAGE_INDEX_INVALID") from exc
        if actual != expected:
            raise ValueError(f"REFERENCE_REVIEW_{field.upper()}_MISMATCH")
    if str(queue_item["source_id"]) != acquired_page["source_id"] or int(queue_item["page_index"]) != acquired_page["page_index"]:
        raise ValueError("REFERENCE_REVIEW_QUEUE_ACQUISITION_MISMATCH")
    if str(queue_item["page_feature_sha256"]) != acquired_page["page_feature_sha256"]:
        raise ValueError("REFERENCE_REVIEW_QUEUE_PAGE_FEATURE_MISMATCH")
    return state, reviewer, rationale


def _entry_from_terminal_accept(
    decision: dict[str, Any],
    queue_item: dict[str, Any],
    acquired_page: dict[str, Any],
    reviewer: str,
    rationale: str,
) -> dict[str, Any]:
    meaning = _require_text(decision.get("meaning"), "meaning")
    scope = decision.get("scope")
    if not isinstance(scope, dict) or not scope:
        raise ValueError("REFERENCE_REVIEW_SCOPE_REQUIRED")
    primitive_families = decision.get("primitive_families")
    if not isinstance(primitive_families, list) or not primitive_families or not all(str(x).strip() for x in primitive_families):
        raise ValueError("REFERENCE_REVIEW_PRIMITIVE_FAMILIES_REQUIRED")
    aspect_buckets = decision.get("aspect_buckets") or []
    area_buckets = decision.get("area_buckets") or []
    if not isinstance(aspect_buckets, list) or not isinstance(area_buckets, list):
        raise ValueError("REFERENCE_REVIEW_PATTERN_BUCKETS_INVALID")
    filled = decision.get("filled")
    if filled is not None and not isinstance(filled, bool):
        raise ValueError("REFERENCE_REVIEW_FILLED_INVALID")
    counterexample_refs = decision.get("counterexample_refs") or []
    if not isinstance(counterexample_refs, list):
        raise ValueError("REFERENCE_REVIEW_COUNTEREXAMPLE_REFS_INVALID")

    entry_identity = {
        "meaning": meaning,
        "scope": scope,
        "source_id": acquired_page["source_id"],
        "source_sha256": acquired_page["source_sha256"],
        "page_index": acquired_page["page_index"],
        "page_feature_sha256": acquired_page["page_feature_sha256"],
        "primitive_families": sorted(str(x).strip() for x in primitive_families),
        "aspect_buckets": sorted(str(x).strip() for x in aspect_buckets),
        "area_buckets": sorted(str(x).strip() for x in area_buckets),
        "filled": filled,
    }
    entry_id = "GREF-" + _sha256(_canonical(entry_identity).encode("utf-8"))[:20]
    source_ref = {
        "source_id": acquired_page["source_id"],
        "source_sha256": acquired_page["source_sha256"],
        "source_url": acquired_page.get("source_url"),
        "page_index": acquired_page["page_index"],
        "page_number_1_based": acquired_page["page_number_1_based"],
        "page_text_sha256": acquired_page["page_text_sha256"],
        "page_feature_sha256": acquired_page["page_feature_sha256"],
        "review_item_id": queue_item["review_item_id"],
    }
    return {
        "entry_id": entry_id,
        "meaning": meaning,
        "tier": "EXTERNAL_REFERENCE",
        "scope": scope,
        "primitive_families": sorted(str(x).strip() for x in primitive_families),
        "aspect_buckets": sorted(str(x).strip() for x in aspect_buckets),
        "area_buckets": sorted(str(x).strip() for x in area_buckets),
        "filled": filled,
        "source_refs": [source_ref],
        "counterexample_refs": counterexample_refs,
        "review": {
            "reviewer": reviewer,
            "rationale": rationale,
            "decision_id": _require_text(decision.get("decision_id"), "decision_id"),
            "reviewed_at": _require_text(decision.get("reviewed_at"), "reviewed_at"),
        },
        "project_semantic_authority": "NONE",
        "canonical_write_authorized": False,
    }


def _resolve_terminal_decisions(
    decisions_rows: list[dict[str, Any]],
    queued: dict[str, dict[str, Any]],
    acquired_pages: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, str]]:
    seen_decision_ids: set[str] = set()
    by_item: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions_rows:
        decision_id = _require_text(decision.get("decision_id"), "decision_id")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", decision_id) or decision_id in seen_decision_ids:
            raise ValueError("REFERENCE_REVIEW_DECISION_ID_INVALID_OR_DUPLICATE")
        seen_decision_ids.add(decision_id)
        review_item_id = _require_text(decision.get("review_item_id"), "review_item_id")
        if review_item_id not in queued:
            raise ValueError("REFERENCE_REVIEW_ITEM_UNKNOWN")
        by_item.setdefault(review_item_id, []).append(decision)

    resolved: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, str]] = {}
    for review_item_id, history in by_item.items():
        queue_item = queued[review_item_id]
        key = (str(queue_item["source_id"]), int(queue_item["page_index"]))
        acquired_page = acquired_pages.get(key)
        if acquired_page is None:
            raise ValueError("REFERENCE_REVIEW_ITEM_NOT_ACQUIRED")
        history = sorted(history, key=_reviewed_at_key)
        terminal_seen = False
        for decision in history:
            state, reviewer, rationale = _validate_decision_anchor(decision, queue_item, acquired_page)
            if terminal_seen:
                raise ValueError("REFERENCE_REVIEW_DECISION_AFTER_TERMINAL")
            if state in NONTERMINAL_STATES:
                continue
            terminal_seen = True
            resolved[review_item_id] = (decision, queue_item, acquired_page, reviewer, rationale)
    return resolved


def _empty_pack(build_state: str) -> dict[str, Any]:
    return {
        "schema": LIBRARY_SCHEMA,
        "status": "LIBRARY_EMPTY",
        "generation_id": None,
        "content_sha256": None,
        "entry_count": 0,
        "tiers_present": [],
        "source_count": 0,
        "sources": [],
        "entries": [],
        "build_state": build_state,
        "project_semantic_authority": "NONE",
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def build_pack(
    acquisition: dict[str, Any],
    queue: dict[str, Any],
    decisions: dict[str, Any],
) -> dict[str, Any]:
    if decisions.get("schema") != DECISIONS_SCHEMA:
        raise ValueError("REFERENCE_REVIEW_DECISIONS_SCHEMA_INVALID")
    expected_receipt = str(queue.get("acquisition_receipt_fingerprint") or "")
    if str(decisions.get("acquisition_receipt_fingerprint") or "") != expected_receipt:
        raise ValueError("REFERENCE_REVIEW_DECISIONS_ACQUISITION_FINGERPRINT_MISMATCH")
    acquired_pages = _load_acquired_page_index(acquisition)
    queued = _queue_index(queue)
    decisions_rows = decisions.get("decisions")
    if not isinstance(decisions_rows, list):
        raise ValueError("REFERENCE_REVIEW_DECISIONS_LIST_REQUIRED")
    if not decisions_rows:
        return _empty_pack("HUMAN_REVIEW_NOT_STARTED")

    resolved = _resolve_terminal_decisions(decisions_rows, queued, acquired_pages)
    if set(resolved) != set(queued):
        raise ValueError("REFERENCE_REVIEW_INCOMPLETE")

    entries: list[dict[str, Any]] = []
    for review_item_id in sorted(resolved):
        decision, queue_item, acquired_page, reviewer, rationale = resolved[review_item_id]
        state = str(decision["state"])
        if state == "ACCEPT_REFERENCE_EVIDENCE":
            entries.append(_entry_from_terminal_accept(decision, queue_item, acquired_page, reviewer, rationale))
        elif state != "REJECT_REFERENCE_EVIDENCE":
            raise ValueError("REFERENCE_REVIEW_TERMINAL_STATE_INVALID")

    entries.sort(key=lambda x: x["entry_id"])
    if not entries:
        return _empty_pack("HUMAN_REVIEW_COMPLETE_NO_ACCEPTED_REFERENCE_EVIDENCE")

    content_sha = _sha256(_canonical(entries).encode("utf-8"))
    generation_id = "GREF-GEN-" + content_sha[:16]
    sources = sorted({ref["source_id"] for entry in entries for ref in entry["source_refs"]})
    return {
        "schema": LIBRARY_SCHEMA,
        "status": "LIBRARY_AVAILABLE_UNVERIFIED_FOR_CONTEXT",
        "generation_id": generation_id,
        "content_sha256": content_sha,
        "entry_count": len(entries),
        "tiers_present": ["EXTERNAL_REFERENCE"],
        "source_count": len(sources),
        "sources": sources,
        "entries": entries,
        "builder_version": PACK_BUILDER_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "acquisition_receipt_fingerprint": expected_receipt,
        "project_human_validation_required_for_match": True,
        "project_semantic_authority": "NONE",
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build reviewed external graphic-reference library pack")
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    acquisition = json.loads(args.acquisition.read_text(encoding="utf-8"))
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    pack = build_pack(acquisition, queue, decisions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"CEW_EXTERNAL_REFERENCE_PACK status={pack['status']} entries={pack['entry_count']} generation={pack.get('generation_id')}")


if __name__ == "__main__":
    main()
