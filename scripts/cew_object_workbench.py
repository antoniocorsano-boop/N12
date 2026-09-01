#!/usr/bin/env python3
"""OA-1 read-only Human Object Workbench projection.

Produces a CAD-oriented review model. Source imagery is secondary evidence and
canonical writes remain outside this module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
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
        if item.state in (CandidateState.AMBIGUOUS, CandidateState.BLOCKED):
            blockers.append(
                {
                    "evidence_object_id": item.evidence_object_id,
                    "state": item.state.value,
                    "family_id": item.family_id,
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
                "source_evidence": {
                    "source_version_id": item.provenance.source_version_id,
                    "page_id": item.provenance.page_id,
                    "evidence_region_id": item.provenance.evidence_region_id,
                    "registration_id": item.provenance.registration_id,
                    "role": "SECONDARY_AUDIT_EVIDENCE",
                },
                "actions": [
                    "TEACH_THIS_IS",
                    "FIND_SIMILAR",
                    "CONFIRM",
                    "REJECT",
                    "MOVE_FAMILY",
                    "CREATE_FAMILY",
                    "COMPARE",
                    "VIEW_SOURCE",
                    "MARK_AMBIGUOUS",
                ],
            }
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
        },
        "families": [
            {"family_id": key, "count": len(value), "object_ids": sorted(value)}
            for key, value in sorted(families.items())
        ],
        "blockers": blockers,
        "objects": objects,
    }
