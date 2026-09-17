from __future__ import annotations

import copy
import json
from pathlib import Path

from cew_roleview_adapter_v1 import (
    ENGINEERING_AUTHORITY,
    PRODUCT_AUTHORITY,
    build_cew_roleview,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "3087c715e403d29418e5bb3ec81e6376caab93d9"


def load_json(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def assert_roleview_shape(snapshot: dict) -> None:
    required = {
        "schemaVersion",
        "product",
        "scope",
        "role",
        "focus",
        "stage",
        "status",
        "headline",
        "maturity",
        "gates",
        "kpis",
        "blockers",
        "nextActions",
        "evidence",
        "provenance",
    }
    assert required <= snapshot.keys()
    assert snapshot["schemaVersion"] == "roleview.v0"
    assert snapshot["product"] == "CEW"
    assert snapshot["status"] in {"READY", "ATTENTION", "BLOCKED"}
    assert all(
        item["state"] in {"NOT_ASSESSED", "IN_PROGRESS", "READY", "BLOCKED"}
        for item in snapshot["maturity"]
    )
    assert all(
        item["status"] in {"PASS", "WARN", "BLOCKED", "NOT_APPLICABLE"}
        for item in snapshot["gates"]
    )
    assert all("score" not in item for item in snapshot["maturity"])


def build(product: dict, engineering: dict, **kwargs) -> dict:
    params = {
        "exact_revision": BASELINE_REVISION,
        "product_revision": BASELINE_REVISION,
        "engineering_revision": BASELINE_REVISION,
        "focus": "PRODUCT_PROGRESS",
        "role": "REVIEWER",
    }
    params.update(kwargs)
    return build_cew_roleview(product, engineering, **params)


def gate(snapshot: dict, gate_id: str) -> dict:
    return next(item for item in snapshot["gates"] if item["id"] == gate_id)


def kpi(snapshot: dict, kpi_id: str) -> dict:
    return next(item for item in snapshot["kpis"] if item["id"] == kpi_id)


def main() -> None:
    product = load_json(PRODUCT_AUTHORITY)
    engineering = load_json(ENGINEERING_AUTHORITY)

    progress = build(product, engineering, focus="PRODUCT_PROGRESS")
    assert_roleview_shape(progress)
    assert progress["status"] == "ATTENTION"
    assert gate(progress, "ENGINEERING_REFERENCE_STATE")["status"] == "WARN"
    assert not any(
        blocker["code"].startswith("PROMOTION_GATE:")
        for blocker in progress["blockers"]
    )
    assert kpi(progress, "promotion_blocker_count")["value"] == len(
        product["current_product_work_item"]["promotion_blockers"]
    )
    assert progress["evidence"] == progress["provenance"]

    promotion = build(product, engineering, focus="PRODUCT_PROMOTION")
    assert_roleview_shape(promotion)
    assert promotion["status"] == "BLOCKED"
    for gate_id in {
        "PROMOTION_BLOCKERS",
        "HUMAN_ACCEPTANCE",
        "ACCESSIBILITY",
        "SAME_REVISION_PRODUCTION_SMOKE",
        "PRODUCTION_PROMOTION_AUTHORIZED",
    }:
        assert gate(promotion, gate_id)["status"] == "BLOCKED"

    ready_product = copy.deepcopy(product)
    ready_product["current_product_work_item"]["state"] = "COMPLETE"
    ready_product["current_product_work_item"]["promotion_blockers"] = []
    ready_product["runtime"]["preview"]["human_acceptance_status"] = "PASS"
    ready_product["runtime"]["preview"]["accessibility_status"] = "PASS"
    ready_product["runtime"]["preview"]["production_promotion_authorized"] = True
    ready_product["runtime"]["production"]["smoke_status"] = (
        "EXTENDED_B1_SAME_REVISION_PRODUCTION_SMOKE_PASS"
    )
    ready = build(ready_product, engineering, focus="PRODUCT_PROMOTION")
    assert_roleview_shape(ready)
    assert ready["status"] == "READY"
    assert ready["blockers"] == []

    human_block = copy.deepcopy(ready_product)
    human_block["current_product_work_item"]["state"] = "HUMAN_AUTHORITY_REQUIRED"
    blocked = build(human_block, engineering, focus="PRODUCT_PROGRESS")
    assert blocked["status"] == "BLOCKED"
    assert gate(blocked, "CURRENT_PRODUCT_WORK_ITEM")["status"] == "BLOCKED"

    missing_revision = build(
        product,
        engineering,
        exact_revision="",
        product_revision="",
        engineering_revision="",
    )
    assert missing_revision["status"] == "BLOCKED"
    assert gate(missing_revision, "EXACT_SOURCE_REVISION")["status"] == "BLOCKED"

    revision_mismatch = build(
        product,
        engineering,
        engineering_revision="1111111111111111111111111111111111111111",
    )
    assert revision_mismatch["status"] == "BLOCKED"
    assert gate(revision_mismatch, "EXACT_SOURCE_REVISION")["status"] == "BLOCKED"

    authority_mismatch = build(
        product,
        engineering,
        engineering_authority_path="knowledge/OTHER_STATE.json",
    )
    assert authority_mismatch["status"] == "BLOCKED"
    assert gate(authority_mismatch, "SOURCE_AUTHORITY_BINDING")["status"] == "BLOCKED"

    projected_mismatch = copy.deepcopy(product)
    projected_mismatch["engineering_state"]["current_work_item"] = "OTHER-WORK-ITEM"
    mismatch = build(projected_mismatch, engineering)
    assert mismatch["status"] == "BLOCKED"

    print("CEW_ROLEVIEW_ADAPTER_PASS")


if __name__ == "__main__":
    main()
