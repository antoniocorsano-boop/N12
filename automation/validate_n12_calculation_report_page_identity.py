#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "recovery" / "N12_CALCULATION_REPORT_PAGE_IDENTITY_GATE_v1.json"
GROUPS = ROOT / "recovery" / "N12_CALCULATION_REPORT_DOCUMENT_GROUPS_v3.csv"


def fail(msg: str):
    print(f"N12_CALCULATION_REPORT_PAGE_IDENTITY_FAIL: {msg}")
    raise SystemExit(1)


def main():
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    with GROUPS.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if gate["promotion_policy"].get("minimum_independent_supports") != 2:
        fail("minimum independent supports must remain 2")
    if gate["promotion_policy"].get("duplicate_photo_or_crop_counts_as_independent_support") is not False:
        fail("duplicate photographs cannot count as independent supports")
    if gate["promotion_policy"].get("feature_matching_counts_as_identity_support") is not False:
        fail("feature matching cannot promote page identity")
    if gate["promotion_policy"].get("sequence_inference_counts_as_identity_support") is not False:
        fail("sequence inference cannot promote page identity")

    verified = {x["page_id"] for x in gate["verified_identities"]}
    if verified != {"RC-P02", "RC-P10", "RC-P13"}:
        fail(f"unexpected verified identity set: {sorted(verified)}")
    for item in gate["verified_identities"]:
        if len(set(item.get("supports", []))) < 2:
            fail(f"{item['page_id']} lacks two independent support classes")

    group_verified = {
        r["document_identity"]
        for r in rows
        if r["identity_state"] == "VERIFIED_HISTORICAL_AND_VISUAL"
    }
    if group_verified != verified:
        fail(f"group register verified set differs from gate: {sorted(group_verified)}")

    blocked_labels = {x["visible_label"] for x in gate["blocked_visible_labels"]}
    if blocked_labels != {"4", "7", "11", "12", "14", "15"}:
        fail("blocked visible-label set changed without governed reconciliation")

    for r in rows:
        state = r["identity_state"]
        ident = r["document_identity"]
        if state == "VISIBLE_LABEL_NEEDS_HISTORICAL_RECONCILIATION" and ident.startswith("RC-P"):
            fail(f"visible-label-only group incorrectly promoted: {r['group_id']} -> {ident}")
        if r.get("promotion_authorized") != "NO":
            fail(f"catalog must not authorize promotion: {r['group_id']}")

    auth = gate["authority"]
    if auth.get("page_identity_autopromotion_authorized") is not False:
        fail("page identity autopromotion must remain forbidden")
    if auth.get("canonical_structural_write_authorized") is not False:
        fail("canonical structural write must remain forbidden")

    print("N12_CALCULATION_REPORT_PAGE_IDENTITY_GATE_PASS")
    print("VERIFIED_PAGE_IDENTITIES RC-P02 RC-P10 RC-P13")
    print("PENDING_VISIBLE_LABELS 4 7 11 12 14 15")
    print("CANDIDATE_PAGE_IDENTITIES RC-P03")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
