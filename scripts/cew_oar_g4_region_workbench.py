#!/usr/bin/env python3
"""Composizione del Workbench OAR G4 con risoluzione governata di TAV-05S."""
from __future__ import annotations

from cew_oar_g4_region_workbench_base import *  # noqa: F401,F403
import cew_oar_g4_audit_history as _history
import cew_oar_g4_atomic_store as _atomic_store
import cew_oar_g4_region_binding as _binding
import cew_oar_g4_region_workbench_base as _base
import cew_oar_g4_source_resolver as _resolver

verify_source = _resolver.verify_source
ensure_runtime_raster = _resolver.ensure_runtime_raster
EXPECTED_SOURCE_SHA256 = _resolver.EXPECTED_SOURCE_SHA256
EXPECTED_PAGE_WIDTH_PT = _resolver.EXPECTED_PAGE_WIDTH_PT
EXPECTED_PAGE_HEIGHT_PT = _resolver.EXPECTED_PAGE_HEIGHT_PT
RUNTIME_DPI = _resolver.RUNTIME_DPI
RUNTIME_RASTER = _resolver.RUNTIME_RASTER

_base.verify_source = verify_source
_base.ensure_runtime_raster = ensure_runtime_raster
_base.EXPECTED_SOURCE_SHA256 = EXPECTED_SOURCE_SHA256
_base.EXPECTED_PAGE_WIDTH_PT = EXPECTED_PAGE_WIDTH_PT
_base.EXPECTED_PAGE_HEIGHT_PT = EXPECTED_PAGE_HEIGHT_PT
_base.RUNTIME_DPI = RUNTIME_DPI
_base.RUNTIME_RASTER = RUNTIME_RASTER

_original_runtime_loader = _base.audit_store.load_runtime_receipts


def _governed_runtime_loader(receipt_type, store, *, max_receipts=_history.MAX_PAGE_SIZE):
    if receipt_type == _binding.RECEIPT_TYPE:
        return _history.load_runtime_receipts(receipt_type, store, max_receipts=max_receipts)
    return _original_runtime_loader(receipt_type, store, max_receipts=max_receipts)


_base.audit_store.load_runtime_receipts = _governed_runtime_loader


def _post_commit_summary(current: dict, row: dict, action: str) -> tuple[dict, str]:
    """Project the committed support transition onto the pre-commit snapshot.

    This summary is intentionally identified as a projection. It never performs a
    second remote read, so a temporary read/source outage cannot turn a committed
    append into an apparent rejection. The UI performs its normal status refresh
    independently after receiving this success response.
    """
    summary = dict(current["summary"])
    previous = str(row["state"])
    if action == _binding.PROPOSAL_ACTION and previous == "UNBOUND":
        summary["UNBOUND"] -= 1
        summary["PROPOSED"] += 1
    elif action == _binding.CONFIRM_ACTION and previous == "PROPOSED":
        summary["PROPOSED"] -= 1
        summary["GEOMETRY_CONFIRMED"] += 1
    next_gate = "LOCALIZE_REMAINING_OBJECTS" if summary["UNBOUND"] else "GOVERNED_EVIDENCE_REGION_MATERIALIZATION_REVIEW"
    return summary, next_gate


# Arena-style optimistic concurrency: the client prepares an intent bound to the
# exact revision it observed, while the persistence boundary performs the final
# compare-and-set and assigns the governed timestamp inside the serialized commit.
def persist_action(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("OAR_REGION_REQUEST_OBJECT_REQUIRED")
    allowed = {"decision_id", "support_id", "action", "bbox"}
    if not set(payload).issubset(allowed) or not {"decision_id", "support_id", "action"}.issubset(payload):
        raise ValueError("OAR_REGION_REQUEST_FIELD_SET_INVALID")

    action = str(payload["action"])
    support_id = str(payload["support_id"])
    current = _base.load_report()
    row = next((item for item in current["objects"] if str(item["support_id"]) == support_id), None)
    if row is None:
        raise ValueError("OAR_REGION_SUPPORT_NOT_IN_PILOT")

    if action == _binding.PROPOSAL_ACTION:
        if row["state"] == "GEOMETRY_CONFIRMED":
            raise ValueError("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED")
        bbox = payload.get("bbox")
        base_proposal_decision_id = (
            row.get("geometry_proposal_receipt_id")
            if row["state"] == "PROPOSED"
            else _binding.unbound_revision_anchor(support_id)
        )
    elif action == _binding.CONFIRM_ACTION:
        if row["state"] != "PROPOSED" or not isinstance(row.get("bbox"), dict):
            raise ValueError("OAR_REGION_CONFIRMATION_REQUIRES_CURRENT_PROPOSAL")
        bbox = row["bbox"]
        base_proposal_decision_id = row.get("geometry_proposal_receipt_id")
        if not base_proposal_decision_id:
            raise ValueError("OAR_REGION_CONFIRMATION_REQUIRES_PROPOSAL_REVISION")
        if "bbox" in payload and payload["bbox"] is not None and _binding.normalize_bbox(payload["bbox"]) != bbox:
            raise ValueError("OAR_REGION_CONFIRMATION_BBOX_MISMATCH")
    else:
        raise ValueError("OAR_REGION_ACTION_INVALID")

    receipt = _binding.build_receipt(
        decision_id=str(payload["decision_id"]),
        support_id=support_id,
        bbox=bbox,
        action=action,
        base_proposal_decision_id=base_proposal_decision_id,
    )

    # Pre-validation gives the operator an immediate domain error, but it is not
    # the concurrency authority. The atomic store repeats revision validation
    # inside its persistence boundary and may reject this intent as stale.
    loaded = _base.audit_store.load_runtime_receipts(_binding.RECEIPT_TYPE, _base.RUNTIME_STORE)
    _binding.aggregate([*loaded["receipts"], receipt])
    persisted = _atomic_store.persist_region_receipt(receipt, _base.RUNTIME_STORE)

    # Persistence is the commit boundary. Do not perform a second governed read
    # before acknowledging success: that read could fail after an irreversible
    # append and incorrectly tell the operator that the receipt was rejected.
    committed = persisted.get("committed_receipt")
    if not isinstance(committed, dict) or committed.get("decision_id") != persisted.get("runtime_receipt_id"):
        raise RuntimeError("OAR_REGION_COMMITTED_RECEIPT_MISSING")
    object_state = "PROPOSED" if action == _binding.PROPOSAL_ACTION else "GEOMETRY_CONFIRMED"
    committed_bbox = _binding.normalize_bbox(committed.get("bbox"))
    summary, next_gate = _post_commit_summary(current, row, action)
    return {
        "state": "OAR_REGION_RECEIPT_COMMITTED_AUDIT_ONLY",
        "runtime_receipt_id": persisted["runtime_receipt_id"],
        "sha256": persisted["sha256"],
        "audit_backend": persisted["audit_backend"],
        "atomic_revision": persisted.get("atomic_revision") is True,
        "commit_acknowledged": True,
        "status_refresh_required": True,
        "summary_basis": "PRE_COMMIT_SNAPSHOT_PLUS_COMMITTED_TRANSITION",
        "support_id": support_id,
        "object_state": object_state,
        "bbox": committed_bbox,
        "summary": summary,
        "next_gate": next_gate,
        "oar_human_confirmation": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


_base.persist_action = persist_action

# Harden the already validated base UI. A displayed bbox that has been edited is
# explicitly dirty: confirmation is disabled until PROPOSE_GEOMETRY persists it.
# Confirmation also sends the displayed bbox so the server mismatch guard remains
# a second, independent fail-closed boundary.
_base_build_page = _base.build_page


def build_page() -> str:
    page = _base_build_page()
    replacements = (
        (
            "let report=null, selected=null, draft=null, dragStart=null;",
            "let report=null, selected=null, draft=null, dragStart=null, draftDirty=false;",
        ),
        (
            "setBox(r?.bbox??null);propose.disabled=!selected;confirmBtn.disabled=!(r&&r.state==='PROPOSED');",
            "setBox(r?.bbox??null);draftDirty=false;propose.disabled=!selected;confirmBtn.disabled=!(r&&r.state==='PROPOSED');",
        ),
        (
            "setBox({x,y,w:Math.abs(p.x-dragStart.x),h:Math.abs(p.y-dragStart.y)});propose.disabled=!(draft&&draft.w>0&&draft.h>0)",
            "setBox({x,y,w:Math.abs(p.x-dragStart.x),h:Math.abs(p.y-dragStart.y)});draftDirty=true;confirmBtn.disabled=true;propose.disabled=!(draft&&draft.w>0&&draft.h>0)",
        ),
        (
            "if(action==='PROPOSE_GEOMETRY')payload.bbox=draft;message.textContent='Registrazione…';",
            "if(action==='PROPOSE_GEOMETRY'||action==='CONFIRM_GEOMETRY')payload.bbox=draft;if(action==='CONFIRM_GEOMETRY'&&draftDirty){message.textContent='Registra prima la geometria modificata.';return};message.textContent='Registrazione…';",
        ),
    )
    for old, new in replacements:
        if old not in page:
            raise RuntimeError("OAR_G4_UI_STALE_GEOMETRY_PATCH_MARKER_MISSING")
        page = page.replace(old, new, 1)
    return page


_base.build_page = build_page


def build_router():
    return _base.build_router()
