#!/usr/bin/env python3
"""OA-1 read-only Human Object Workbench projection.

Produces a CAD-oriented review model. Source imagery is secondary evidence and
canonical writes remain outside this module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from cew_object_acquisition import CandidateState, ObjectCandidate


VISIBLE_STATE = {
    CandidateState.HUMAN_CONFIRMED: "verified",
    CandidateState.CANDIDATE: "proposal",
    CandidateState.DETECTED: "proposal",
    CandidateState.AMBIGUOUS: "ambiguous",
    CandidateState.BLOCKED: "blocked",
    CandidateState.REJECTED: "rejected",
}


def _provenance_gaps(item: ObjectCandidate) -> list[str]:
    gaps = []
    if not item.provenance.source_version_id.strip():
        gaps.append("SOURCE_VERSION_BINDING_MISSING")
    if not item.provenance.page_id.strip():
        gaps.append("PAGE_BINDING_MISSING")
    if not item.provenance.evidence_region_id.strip():
        gaps.append("EVIDENCE_REGION_BINDING_MISSING")
    if not item.provenance.evidence_fingerprint.strip():
        gaps.append("EVIDENCE_FINGERPRINT_MISSING")
    return gaps


def build_object_workbench_view(candidates: Iterable[ObjectCandidate]) -> dict:
    items = list(candidates)
    state_counts = Counter(VISIBLE_STATE[item.state] for item in items)
    families: dict[str, list[str]] = defaultdict(list)
    blockers = []

    objects = []
    for item in items:
        family = item.family_id or "UNASSIGNED"
        families[family].append(item.evidence_object_id)
        status = VISIBLE_STATE[item.state]
        provenance_gaps = _provenance_gaps(item)

        if item.state in (CandidateState.AMBIGUOUS, CandidateState.BLOCKED):
            blockers.append(
                {
                    "evidence_object_id": item.evidence_object_id,
                    "blocker_type": "REVIEW_STATE",
                    "state": item.state.value,
                    "family_id": item.family_id,
                    "source_action": "VIEW_SOURCE",
                }
            )
        if provenance_gaps:
            blockers.append(
                {
                    "evidence_object_id": item.evidence_object_id,
                    "blocker_type": "PROVENANCE_BINDING",
                    "state": item.state.value,
                    "family_id": item.family_id,
                    "reasons": provenance_gaps,
                    "effect": "CAD_PROMOTION_INELIGIBLE",
                    "reviewable": True,
                    "source_action": "VIEW_SOURCE",
                }
            )

        objects.append(
            {
                "evidence_object_id": item.evidence_object_id,
                "object_type": item.object_type.value,
                "family_id": item.family_id,
                "visual_state": status,
                "cad_signature": item.signature.fingerprint(),
                "reviewable": item.state not in (CandidateState.REJECTED,),
                "promotion_ready": item.provenance.complete() and item.state == CandidateState.HUMAN_CONFIRMED,
                "provenance_gaps": provenance_gaps,
                "source_evidence": {
                    "source_version_id": item.provenance.source_version_id or None,
                    "page_id": item.provenance.page_id or None,
                    "evidence_region_id": item.provenance.evidence_region_id or None,
                    "registration_id": item.provenance.registration_id,
                    "evidence_fingerprint": item.provenance.evidence_fingerprint,
                    "role": "SECONDARY_AUDIT_EVIDENCE",
                },
                "actions": [
                    "TEACH_THIS_IS",
                    "FIND_SIMILAR",
                    "CONFIRM",
                    "CONFIRM_GROUP",
                    "REJECT",
                    "MOVE_FAMILY",
                    "CREATE_FAMILY",
                    "COMPARE",
                    "VIEW_SOURCE",
                    "MARK_AMBIGUOUS",
                ],
            }
        )

    provenance_blocking_count = sum(
        1 for blocker in blockers if blocker["blocker_type"] == "PROVENANCE_BINDING"
    )
    review_blocking_count = sum(
        1 for blocker in blockers if blocker["blocker_type"] == "REVIEW_STATE"
    )

    return {
        "surface": "CEW_OBJECT_EVIDENCE_WORKBENCH",
        "mode": "CAD_ORIENTED_PRIMARY_SOURCE_SECONDARY",
        "authority": "WORKING_OBJECT_EVIDENCE_ONLY",
        "canonical_write_authorized": False,
        "summary": {
            "total": len(items),
            "states": dict(sorted(state_counts.items())),
            "families": len(families),
            "blocking_count": len(blockers),
            "provenance_blocking_count": provenance_blocking_count,
            "review_blocking_count": review_blocking_count,
            "promotion_ready_count": sum(
                1 for item in items
                if item.provenance.complete() and item.state == CandidateState.HUMAN_CONFIRMED
            ),
        },
        "families": [
            {"family_id": key, "count": len(value), "object_ids": sorted(value)}
            for key, value in sorted(families.items())
        ],
        "blockers": blockers,
        "objects": objects,
    }
