#!/usr/bin/env python3
"""Derive OAR revision heads from governed append-only history.

This module deliberately does not implement a second transition machine.
`binding.aggregate()` is the canonical anchored-transition replay.  Revision
heads are a runtime CAS projection of that governed replay and carry no
classification, structural, canonical-write or engineering authority.
"""
from __future__ import annotations

from typing import Any

import cew_oar_g4_region_binding as binding


def derive_revision_heads(
    receipts: list[dict[str, Any]],
    contract: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    contract = contract or binding.load_contract()
    report = binding.aggregate(receipts, contract)
    heads: dict[str, dict[str, Any]] = {}
    for row in report["objects"]:
        support_id = str(row["support_id"])
        state = str(row["state"])
        if state == "UNBOUND":
            current = binding.unbound_revision_anchor(support_id)
        else:
            current = row.get("geometry_proposal_receipt_id")
            if not isinstance(current, str) or not current:
                raise ValueError("OAR_REGION_DERIVED_HEAD_PROPOSAL_REQUIRED")
        heads[support_id] = {
            "binding_id": report["binding_id"],
            "support_id": support_id,
            "current_proposal_decision_id": current,
            "state": state,
            "authority": "RUNTIME_REVISION_PROJECTION_ONLY",
            "canonical_write_authorized": False,
            "structural_identity_authorized": False,
            "oar_human_confirmation": False,
            "engineering_authority_effect": "NONE",
        }
    return heads


def derive_revision_head(
    receipts: list[dict[str, Any]],
    support_id: str,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    support_id = str(support_id).strip()
    if not support_id:
        raise ValueError("OAR_REGION_SUPPORT_ID_REQUIRED")
    heads = derive_revision_heads(receipts, contract)
    try:
        return heads[support_id]
    except KeyError as exc:
        raise ValueError("OAR_REGION_SUPPORT_NOT_IN_PILOT") from exc
