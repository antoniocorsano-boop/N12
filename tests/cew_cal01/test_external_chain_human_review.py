import unittest

from experiments.cew_cal01.external_chain_human_review import (
    normalize_source_bbox_ccw,
    reconcile_direct_human_decisions,
    reconcile_human_receipts,
)


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _manifest(source_id, source_sha, rows):
    return {
        "schema": "CEW_CAL01_INTERVAL_TEXT_REVIEW_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": source_id, "sha256": source_sha},
        "review_request_count": len(rows),
        "review_requests": rows,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "review_digest": "sha256:" + "a" * 64,
    }


def _request(review_id, crop_bbox, crop_sha="1"):
    side = review_id.split(":")[1]
    chain_id = review_id.split(":")[2] + ":" + review_id.split(":")[3]
    interval_index = int(review_id.rsplit("I", 1)[1])
    return {
        "review_id": review_id,
        "side": side,
        "chain_id": chain_id,
        "interval_index": interval_index,
        "crop_file": f"review-crops/{review_id.replace(':', '_')}.png",
        "crop_sha256": "sha256:" + crop_sha * 64,
        "crop_bbox_normalized_px": list(crop_bbox),
        "primary_anchor_authorized": False,
        "eligible_for_metric_calibration": False,
    }


def _receipt(
    review_id,
    source_id,
    source_sha,
    source_bbox,
    value_m,
    *,
    reviewer_role="HUMAN_PROFESSIONAL_USER",
    metric_relation_state="PRIMARY_VISUAL_VALIDATED",
    calibration_role="LINEAR_DIMENSION",
    relation_network=True,
    primary_anchor_authorized=False,
):
    return {
        "schema": "CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_STRUCTURAL_GRID_v1",
        "program": "CEW-CAL-01",
        "review_id": review_id,
        "reviewer_role": reviewer_role,
        "source_document": source_id,
        "source_sha256": source_sha,
        "source_bbox_px": list(source_bbox),
        "human_reading": f"{value_m:.2f} m",
        "value": {"length_m": value_m},
        "calibration_role": calibration_role,
        "metric_relation_state": metric_relation_state,
        "metric_source_kind": f"PRIMARY_{source_id.replace('-', '')}_DOCUMENTED_RELATION",
        "eligible_for_metric_relation_network": relation_network,
        "eligible_for_metric_calibration": False,
        "primary_anchor_authorized": primary_anchor_authorized,
        "authority": dict(AUTHORITY_CLOSED),
    }


def _direct_decision(
    interval_review_id,
    source_id,
    source_sha,
    crop_sha256,
    value_m,
    *,
    reviewer_role="HUMAN_PROFESSIONAL_USER",
    decision="DOCUMENTED_LINEAR_DIMENSION",
    metric_relation_state="PRIMARY_VISUAL_VALIDATED",
    calibration_role="LINEAR_DIMENSION",
):
    return {
        "schema": "CEW_CAL01_EXTERNAL_CHAIN_HUMAN_DECISION_v1",
        "program": "CEW-CAL-01",
        "reviewer_role": reviewer_role,
        "source_document": source_id,
        "source_sha256": source_sha,
        "interval_review_id": interval_review_id,
        "crop_sha256": crop_sha256,
        "human_reading": f"{value_m:.2f} m",
        "decision": decision,
        "value": {"length_m": value_m},
        "calibration_role": calibration_role,
        "metric_relation_state": metric_relation_state,
        "metric_source_kind": f"PRIMARY_{source_id.replace('-', '')}_DOCUMENTED_RELATION",
        "eligible_for_metric_relation_network": True,
        "eligible_for_metric_calibration": False,
        "primary_anchor_authorized": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class ExternalChainHumanReceiptReconciliationTests(unittest.TestCase):
    def test_source_bbox_rotates_90_counterclockwise_into_normalized_frame(self):
        self.assertEqual(
            normalize_source_bbox_ccw([492.0, 8291.0, 541.0, 8499.0], source_width_px=7016),
            [8291.0, 6475.0, 8499.0, 6524.0],
        )

    def test_existing_t01_human_receipt_binds_to_right_interval(self):
        source_sha = "abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8"
        manifest = _manifest(
            "TAV-01S",
            source_sha,
            [_request("TAV-01S:RIGHT:RIGHT:R1:I0", [11798, 3072, 12058, 3571])],
        )
        receipt = _receipt(
            "SG-T01-02",
            "TAV-01S",
            source_sha,
            [6552.0, 11788.0, 6659.5, 11822.0],
            2.00,
        )
        result = reconcile_human_receipts(manifest, [receipt], source_width_px=9933)
        self.assertEqual(result["reused_count"], 1)
        self.assertEqual(
            result["bindings"]["TAV-01S:RIGHT:RIGHT:R1:I0"]["receipt_review_id"],
            "SG-T01-02",
        )
        self.assertEqual(result["bindings"]["TAV-01S:RIGHT:RIGHT:R1:I0"]["value_m"], 2.0)

    def test_existing_t02_human_receipts_bind_to_bottom_i2_and_i3(self):
        source_sha = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
        manifest = _manifest(
            "TAV-02S",
            source_sha,
            [
                _request("TAV-02S:BOTTOM:BOTTOM:R1:I2", [6324, 6488, 7791, 6748], "2"),
                _request("TAV-02S:BOTTOM:BOTTOM:R1:I3", [7821, 6481, 8962, 6741], "3"),
            ],
        )
        receipts = [
            _receipt(
                "SG-T02-01",
                "TAV-02S",
                source_sha,
                [492.0, 8291.0, 541.0, 8499.0],
                4.95,
            ),
            _receipt(
                "SG-T02-02",
                "TAV-02S",
                source_sha,
                [486.0, 6865.0, 536.0, 7069.0],
                6.25,
            ),
        ]
        result = reconcile_human_receipts(manifest, receipts, source_width_px=7016)
        self.assertEqual(result["reused_count"], 2)
        self.assertEqual(result["bindings"]["TAV-02S:BOTTOM:BOTTOM:R1:I2"]["value_m"], 6.25)
        self.assertEqual(result["bindings"]["TAV-02S:BOTTOM:BOTTOM:R1:I3"]["value_m"], 4.95)

    def test_t01_receipt_outside_external_interval_crops_is_not_reused(self):
        source_sha = "abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8"
        manifest = _manifest(
            "TAV-01S",
            source_sha,
            [_request("TAV-01S:BOTTOM:BOTTOM:R1:I0", [4579, 9122, 7171, 9382])],
        )
        receipt = _receipt(
            "SG-T01-01",
            "TAV-01S",
            source_sha,
            [1032.0, 6147.0, 1062.0, 6249.0],
            4.05,
        )
        result = reconcile_human_receipts(manifest, [receipt], source_width_px=9933)
        self.assertEqual(result["reused_count"], 0)
        self.assertEqual(result["unmatched_receipt_ids"], ["SG-T01-01"])

    def test_non_human_or_non_validated_receipts_are_not_reused(self):
        source_sha = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
        manifest = _manifest(
            "TAV-02S",
            source_sha,
            [_request("TAV-02S:BOTTOM:BOTTOM:R1:I3", [7821, 6481, 8962, 6741])],
        )
        source_bbox = [492.0, 8291.0, 541.0, 8499.0]
        receipts = [
            _receipt("AI-1", "TAV-02S", source_sha, source_bbox, 4.95, reviewer_role="AI_VISUAL_PRECHECK"),
            _receipt("H-2", "TAV-02S", source_sha, source_bbox, 4.95, metric_relation_state="PENDING_HUMAN_CONFIRMATION"),
            _receipt("H-3", "TAV-02S", source_sha, source_bbox, 4.95, calibration_role="SECTION_MEASURE"),
        ]
        result = reconcile_human_receipts(manifest, receipts, source_width_px=7016)
        self.assertEqual(result["reused_count"], 0)
        self.assertEqual(sorted(result["ineligible_receipt_ids"]), ["AI-1", "H-2", "H-3"])

    def test_source_sha_mismatch_is_not_reused(self):
        source_sha = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
        manifest = _manifest(
            "TAV-02S",
            source_sha,
            [_request("TAV-02S:BOTTOM:BOTTOM:R1:I3", [7821, 6481, 8962, 6741])],
        )
        receipt = _receipt(
            "SG-T02-01",
            "TAV-02S",
            "0" * 64,
            [492.0, 8291.0, 541.0, 8499.0],
            4.95,
        )
        result = reconcile_human_receipts(manifest, [receipt], source_width_px=7016)
        self.assertEqual(result["reused_count"], 0)
        self.assertEqual(result["source_mismatch_receipt_ids"], ["SG-T02-01"])

    def test_one_receipt_matching_multiple_intervals_fails_closed(self):
        source_sha = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
        manifest = _manifest(
            "TAV-02S",
            source_sha,
            [
                _request("TAV-02S:BOTTOM:BOTTOM:R1:I2", [6300, 6400, 8500, 6800], "2"),
                _request("TAV-02S:BOTTOM:BOTTOM:R1:I3", [7800, 6400, 9000, 6800], "3"),
            ],
        )
        receipt = _receipt(
            "SG-T02-01",
            "TAV-02S",
            source_sha,
            [492.0, 8291.0, 541.0, 8499.0],
            4.95,
        )
        with self.assertRaisesRegex(ValueError, "CAL01_HUMAN_RECEIPT_INTERVAL_AMBIGUOUS"):
            reconcile_human_receipts(manifest, [receipt], source_width_px=7016)

    def test_conflicting_human_receipts_for_same_interval_fail_closed(self):
        source_sha = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
        manifest = _manifest(
            "TAV-02S",
            source_sha,
            [_request("TAV-02S:BOTTOM:BOTTOM:R1:I3", [7821, 6481, 8962, 6741])],
        )
        source_bbox = [492.0, 8291.0, 541.0, 8499.0]
        receipts = [
            _receipt("SG-T02-01-A", "TAV-02S", source_sha, source_bbox, 4.95),
            _receipt("SG-T02-01-B", "TAV-02S", source_sha, source_bbox, 4.70),
        ]
        with self.assertRaisesRegex(ValueError, "CAL01_HUMAN_RECEIPT_VALUE_CONFLICT"):
            reconcile_human_receipts(manifest, receipts, source_width_px=7016)


class ExternalChainDirectHumanDecisionTests(unittest.TestCase):
    def setUp(self):
        self.source_sha = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
        self.review_id = "TAV-02S:TOP:TOP:R1:I4"
        self.request = _request(self.review_id, [8509, 345, 9729, 605], "5")
        self.manifest = _manifest("TAV-02S", self.source_sha, [self.request])

    def test_direct_decision_binds_by_exact_interval_and_crop_without_source_bbox(self):
        decision = _direct_decision(
            self.review_id,
            "TAV-02S",
            self.source_sha,
            self.request["crop_sha256"],
            5.30,
        )
        result = reconcile_direct_human_decisions(self.manifest, [decision])
        self.assertEqual(result["direct_count"], 1)
        binding = result["bindings"][self.review_id]
        self.assertEqual(binding["review_state"], "DIRECT_HUMAN_DECISION")
        self.assertEqual(binding["value_m"], 5.30)
        self.assertEqual(binding["crop_sha256"], self.request["crop_sha256"])

    def test_direct_decision_crop_sha_mismatch_fails_closed(self):
        decision = _direct_decision(
            self.review_id,
            "TAV-02S",
            self.source_sha,
            "sha256:" + "9" * 64,
            5.30,
        )
        with self.assertRaisesRegex(ValueError, "CAL01_DIRECT_HUMAN_DECISION_CROP_MISMATCH"):
            reconcile_direct_human_decisions(self.manifest, [decision])

    def test_direct_decision_unknown_interval_fails_closed(self):
        decision = _direct_decision(
            "TAV-02S:TOP:TOP:R1:I99",
            "TAV-02S",
            self.source_sha,
            self.request["crop_sha256"],
            5.30,
        )
        with self.assertRaisesRegex(ValueError, "CAL01_DIRECT_HUMAN_DECISION_INTERVAL_UNKNOWN"):
            reconcile_direct_human_decisions(self.manifest, [decision])

    def test_duplicate_same_value_direct_decisions_deduplicate(self):
        decision = _direct_decision(
            self.review_id,
            "TAV-02S",
            self.source_sha,
            self.request["crop_sha256"],
            5.30,
        )
        result = reconcile_direct_human_decisions(self.manifest, [decision, dict(decision)])
        self.assertEqual(result["direct_count"], 1)
        self.assertEqual(result["bindings"][self.review_id]["value_m"], 5.30)

    def test_conflicting_direct_decisions_fail_closed(self):
        first = _direct_decision(
            self.review_id,
            "TAV-02S",
            self.source_sha,
            self.request["crop_sha256"],
            5.30,
        )
        second = _direct_decision(
            self.review_id,
            "TAV-02S",
            self.source_sha,
            self.request["crop_sha256"],
            4.70,
        )
        with self.assertRaisesRegex(ValueError, "CAL01_DIRECT_HUMAN_DECISION_VALUE_CONFLICT"):
            reconcile_direct_human_decisions(self.manifest, [first, second])


if __name__ == "__main__":
    unittest.main()
