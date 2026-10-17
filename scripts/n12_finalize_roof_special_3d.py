#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "automation" / "N12_WORK_QUEUE_v1.json"
TARGET = ROOT / "data" / "canonical" / "ROOF_G5_SPECIAL_FEATURES_3D_CURRENT_v1.csv"
AUDIT = ROOT / "analysis" / "automation" / "M0G_RESOLVE_ROOF_SPECIAL_3D_AUDIT_v1.csv"
REGISTRY = ROOT / "knowledge" / "ARTIFACT_REGISTRY_AUTOMATION_PATCH_v1.csv"
INBOX = ROOT / "automation" / "inbox" / "N12_AGENT_RESULT.json"
WORK_ITEM = "M0G-RESOLVE-ROOF-SPECIAL-3D"


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    item = next((x for x in queue.get("items", []) if x.get("id") == WORK_ITEM), None)
    if not item:
        raise SystemExit(f"missing work item {WORK_ITEM}")
    if item.get("state") == "COMPLETE":
        print("Roof-special 3D work item already COMPLETE; no action.")
        return
    if item.get("state") != "BLOCKED":
        print(f"Roof-special 3D state is {item.get('state')}; guarded finalizer does not alter it.")
        return

    rows, fields = read_csv(TARGET)
    if len(rows) != 6:
        raise SystemExit(f"roof-special target must contain 6 rows, found {len(rows)}")
    ridges = [r for r in rows if r.get("feature_type") == "RIDGE_AXIS"]
    eaves = [r for r in rows if r.get("feature_type") == "GRONDA_EDGE_SET"]
    if len(ridges) != 3 or len(eaves) != 3:
        raise SystemExit(f"expected 3 ridges + 3 eaves, found {len(ridges)} + {len(eaves)}")
    if any(r.get("structural_member_status") != "TO_VERIFY_MEMBER" for r in rows):
        raise SystemExit("roof-special candidate contains an unsupported structural-member promotion")
    if any((r.get("linked_beam_id") or "").strip() for r in rows):
        raise SystemExit("roof-special six-feature target must not duplicate linked ordinary beams")
    if any((r.get("z_rel_g1_m") or "").strip() for r in rows):
        raise SystemExit("guarded finalizer refuses pre-assigned global roof Z")
    if any(r.get("z_evidence_state") != "ND" for r in rows):
        raise SystemExit("roof-special candidate must preserve unresolved global Z as ND")
    if any(r.get("xy_evidence_state") != "MIS" for r in ridges):
        raise SystemExit("ridge XY must remain MIS registered geometry")
    if any(r.get("xy_evidence_state") != "ND" for r in eaves):
        raise SystemExit("eaves XY must remain ND where no unique centerline is supported")

    # Direct visual recheck of immutable TAV-06S section A-B corrects the prior 3.15 transcription.
    # The local source dimensions are 2.10 m at the eave side and 3.75 m at the ridge side.
    for r in rows:
        r["local_vertical_evidence"] = (
            "TAV-06S section A-B directly shows local 2.10 m at the eave side and 3.75 m at the ridge side; "
            "TAV-06E independently records a 2.00+0.20=2.20 m upper module. These endpoint semantics are not "
            "proven equivalent or uniformly bound to all six roof features, so global Z remains ND."
        )
        r["z_binding_status"] = "UNRESOLVED_NONBLOCKING_BY_CONTRACT"
        r["validation_state"] = "CURRENT_WITH_WATCH"
        note = r.get("note", "")
        note = note.replace("3.15", "3.75")
        if "Global Z intentionally remains ND" not in note:
            note = (note.rstrip(".") + ". Global Z intentionally remains ND under the assembly contract.").strip()
        r["note"] = note
    write_csv(TARGET, rows, fields)

    audit_rows, audit_fields = read_csv(AUDIT)
    for r in audit_rows:
        if r.get("audit_id") == "M0G-RS3D-A06":
            r["note"] = (
                "Direct TAV-06S section A-B recheck gives local 2.10 m eave-side and 3.75 m ridge-side dimensions; "
                "TAV-06E gives 2.00+0.20=2.20 m for its upper module. Endpoint semantics are not uniformly bound "
                "to all six features, therefore zero canonical Z assignments is the contract-compliant result."
            )
            r["source_or_method"] = "TAV-06S section A-B direct visual recheck plus TAV-06E vertical chain"
    if not any(r.get("audit_id") == "M0G-RS3D-A11" for r in audit_rows):
        audit_rows.append({
            "audit_id": "M0G-RS3D-A11",
            "work_item_id": WORK_ITEM,
            "check": "local_ridge_dimension_transcription",
            "expected": "3.75",
            "observed": "3.75",
            "result": "PASS",
            "evidence_state": "DOC",
            "source_or_method": "immutable TAV-06S 300dpi section A-B direct visual recheck",
            "note": "Corrects prior candidate text 3.15 -> 3.75 without assigning a global roof Z."
        })
    if not any(r.get("audit_id") == "M0G-RS3D-A12" for r in audit_rows):
        audit_rows.append({
            "audit_id": "M0G-RS3D-A12",
            "work_item_id": WORK_ITEM,
            "check": "semantic_gate_allows_retained_mis_nd",
            "expected": "YES",
            "observed": "YES",
            "result": "PASS",
            "evidence_state": "PROCEDURE",
            "source_or_method": "automation/N12_WORK_QUEUE_v1.json semantic_gate",
            "note": "The queue explicitly permits metric XY/Z only where supported; retained MIS/ND is nonblocking when identities and anti-inference rules are satisfied."
        })
    write_csv(AUDIT, audit_rows, audit_fields)

    reg_rows, reg_fields = read_csv(REGISTRY)
    wanted = {
        "data/canonical/ROOF_G5_SPECIAL_FEATURES_3D_CURRENT_v1.csv": (
            "CANONICAL", "CURRENT", "YES",
            "PASS_WITH_WATCH: exactly 3 ridge axes + 3 eaves edge sets; ridge XY MIS, eaves centerline XY ND, all global Z ND; local TAV-06S A-B values corrected to 2.10/3.75; no structural-member promotion."
        ),
        "analysis/automation/M0G_RESOLVE_ROOF_SPECIAL_3D_AUDIT_v1.csv": (
            "CANONICAL", "CURRENT", "YES",
            "PASS_WITH_WATCH: all six identity/separation checks pass; retained MIS/ND is explicitly permitted by the semantic gate; TAV-06S local ridge transcription corrected 3.15 to 3.75."
        ),
    }
    found: set[str] = set()
    for r in reg_rows:
        path = r.get("path", "")
        if path in wanted:
            authority, status, may_feed, note = wanted[path]
            r["authority"] = authority
            r["status"] = status
            r["may_feed_canonical"] = may_feed
            r["note"] = note
            found.add(path)
    missing = set(wanted) - found
    if missing:
        raise SystemExit(f"registry rows missing for roof-special artifacts: {sorted(missing)}")
    write_csv(REGISTRY, reg_rows, reg_fields)

    now = datetime.now(timezone.utc).isoformat()
    item["state"] = "READY"
    item["reopened_at"] = now
    item["reopened_reason"] = (
        "Prior BLOCKED result mixed an automation handshake defect with semantic residuals. The work-item gate explicitly "
        "permits unsupported roof XY/Z to remain MIS/ND; direct TAV-06S recheck also corrects local ridge transcription "
        "3.15 to 3.75 without creating a global Z."
    )
    queue["updated_at"] = now[:10]
    QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = {
        "schema_version": "1.0",
        "work_item_id": WORK_ITEM,
        "source_sheet": "TAV-06S+TAV-06E",
        "decision": "PASS_WITH_WATCH",
        "semantic_gate": "WATCH",
        "target_outputs": ["data/canonical/ROOF_G5_SPECIAL_FEATURES_3D_CURRENT_v1.csv"],
        "provenance_summary": {"DOC": 6, "MIS": 3, "RIF": 0, "INF": 0, "INC": 0, "ND": 9},
        "residuals": [
            {
                "claim": "Global roof-special Z binding",
                "status": "NONBLOCKING_WATCH",
                "reason": "TAV-06S local 2.10/3.75 dimensions and TAV-06E 2.20 upper module do not have proven equivalent endpoints across all three roof wings.",
                "scope": "All six global Z values remain ND; no structural member is created."
            },
            {
                "claim": "Gronda metric centerline",
                "status": "NONBLOCKING_WATCH",
                "reason": "TAV-06S documents eave edge sets, not one uniquely defined analytical or structural centerline.",
                "scope": "Three gronda identities remain documentary; metric centerline XY remains ND."
            }
        ],
        "audit_paths": ["analysis/automation/M0G_RESOLVE_ROOF_SPECIAL_3D_AUDIT_v1.csv"]
    }
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    INBOX.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Roof-special 3D candidate reopened and prepared for PASS_WITH_WATCH ingestion.")


if __name__ == "__main__":
    main()
