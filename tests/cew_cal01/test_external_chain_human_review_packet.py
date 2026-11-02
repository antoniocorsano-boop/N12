import unittest

from experiments.cew_cal01.external_chain_human_review import (
    build_human_review_packet,
    render_human_review_board,
)


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}

SOURCE_SHA = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"


def _manifest():
    rows = [
        {
            "review_id": "TAV-02S:BOTTOM:BOTTOM:R1:I2",
            "side": "BOTTOM",
            "chain_id": "BOTTOM:R1",
            "interval_index": 2,
            "crop_file": "review-crops/i2.png",
            "crop_sha256": "sha256:" + "2" * 64,
            "crop_bbox_normalized_px": [6324, 6488, 7791, 6748],
            "primary_anchor_authorized": False,
            "eligible_for_metric_calibration": False,
        },
        {
            "review_id": "TAV-02S:BOTTOM:BOTTOM:R1:I3",
            "side": "BOTTOM",
            "chain_id": "BOTTOM:R1",
            "interval_index": 3,
            "crop_file": "review-crops/i3.png",
            "crop_sha256": "sha256:" + "3" * 64,
            "crop_bbox_normalized_px": [7821, 6481, 8962, 6741],
            "primary_anchor_authorized": False,
            "eligible_for_metric_calibration": False,
        },
        {
            "review_id": "TAV-02S:TOP:TOP:R1:I0",
            "side": "TOP",
            "chain_id": "TOP:R1",
            "interval_index": 0,
            "crop_file": "review-crops/top0.png",
            "crop_sha256": "sha256:" + "4" * 64,
            "crop_bbox_normalized_px": [4248, 353, 5331, 613],
            "primary_anchor_authorized": False,
            "eligible_for_metric_calibration": False,
        },
    ]
    return {
        "schema": "CEW_CAL01_INTERVAL_TEXT_REVIEW_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-02S", "sha256": SOURCE_SHA},
        "review_request_count": len(rows),
        "review_requests": rows,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "review_digest": "sha256:" + "a" * 64,
    }


def _comparison():
    rows = [
        {
            "review_id": "TAV-02S:BOTTOM:BOTTOM:R1:I2",
            "crop_file": "review-crops/i2.png",
            "crop_sha256": "sha256:" + "2" * 64,
            "comparison_status": "OCR_NO_PROPOSAL",
            "normalized_texts": [],
            "observations": [{"provider_id": "TESSERACT", "family_id": "GRAY_PSM7", "raw_text": ""}],
            "human_review_required": True,
            "primary_anchor_authorized": False,
            "eligible_for_metric_calibration": False,
        },
        {
            "review_id": "TAV-02S:BOTTOM:BOTTOM:R1:I3",
            "crop_file": "review-crops/i3.png",
            "crop_sha256": "sha256:" + "3" * 64,
            "comparison_status": "OCR_COMPARATIVE_INSUFFICIENT",
            "normalized_texts": ["4.95"],
            "observations": [{"provider_id": "TESSERACT", "family_id": "GRAY_PSM7", "raw_text": "495"}],
            "human_review_required": True,
            "primary_anchor_authorized": False,
            "eligible_for_metric_calibration": False,
        },
        {
            "review_id": "TAV-02S:TOP:TOP:R1:I0",
            "crop_file": "review-crops/top0.png",
            "crop_sha256": "sha256:" + "4" * 64,
            "comparison_status": "OCR_NO_PROPOSAL",
            "normalized_texts": [],
            "observations": [],
            "human_review_required": True,
            "primary_anchor_authorized": False,
            "eligible_for_metric_calibration": False,
        },
    ]
    return {
        "schema": "CEW_CAL01_INTERVAL_OCR_COMPARISON_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-02S", "sha256": SOURCE_SHA},
        "review_manifest_digest": "sha256:" + "a" * 64,
        "review_count": len(rows),
        "reviews": rows,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "comparison_digest": "sha256:" + "b" * 64,
    }


def _receipt(review_id, source_bbox, value_m):
    return {
        "schema": "CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_STRUCTURAL_GRID_v1",
        "program": "CEW-CAL-01",
        "review_id": review_id,
        "reviewer_role": "HUMAN_PROFESSIONAL_USER",
        "source_document": "TAV-02S",
        "source_sha256": SOURCE_SHA,
        "source_bbox_px": list(source_bbox),
        "human_reading": f"{value_m:.2f} m",
        "value": {"length_m": value_m},
        "calibration_role": "LINEAR_DIMENSION",
        "metric_relation_state": "PRIMARY_VISUAL_VALIDATED",
        "metric_source_kind": "PRIMARY_TAV02S_DOCUMENTED_RELATION",
        "eligible_for_metric_relation_network": True,
        "eligible_for_metric_calibration": False,
        "primary_anchor_authorized": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class ExternalChainHumanReviewPacketTests(unittest.TestCase):
    def test_packet_reuses_exact_human_receipts_and_leaves_other_rows_pending(self):
        receipts = [
            _receipt("SG-T02-01", [492.0, 8291.0, 541.0, 8499.0], 4.95),
            _receipt("SG-T02-02", [486.0, 6865.0, 536.0, 7069.0], 6.25),
        ]
        packet = build_human_review_packet(
            _manifest(),
            _comparison(),
            receipts,
            source_width_px=7016,
        )
        self.assertEqual(packet["review_count"], 3)
        self.assertEqual(packet["reused_human_receipt_count"], 2)
        self.assertEqual(packet["pending_human_review_count"], 1)
        states = {row["review_id"]: row["review_state"] for row in packet["reviews"]}
        self.assertEqual(states["TAV-02S:BOTTOM:BOTTOM:R1:I2"], "REUSED_HUMAN_RECEIPT")
        self.assertEqual(states["TAV-02S:BOTTOM:BOTTOM:R1:I3"], "REUSED_HUMAN_RECEIPT")
        self.assertEqual(states["TAV-02S:TOP:TOP:R1:I0"], "PENDING_HUMAN_REVIEW")

    def test_packet_preserves_exact_crop_binding_and_does_not_invent_pending_value(self):
        packet = build_human_review_packet(
            _manifest(),
            _comparison(),
            [],
            source_width_px=7016,
        )
        row = next(r for r in packet["reviews"] if r["review_id"] == "TAV-02S:TOP:TOP:R1:I0")
        self.assertEqual(row["crop_sha256"], "sha256:" + "4" * 64)
        self.assertEqual(row["crop_file"], "review-crops/top0.png")
        self.assertEqual(row["review_state"], "PENDING_HUMAN_REVIEW")
        self.assertIsNone(row["validated_value_m"])
        self.assertIsNone(row["human_receipt_ref"])
        self.assertFalse(row["eligible_for_metric_calibration"])
        self.assertFalse(row["primary_anchor_authorized"])

    def test_manifest_and_comparison_crop_drift_fails_closed(self):
        comparison = _comparison()
        comparison["reviews"][0]["crop_sha256"] = "sha256:" + "9" * 64
        with self.assertRaisesRegex(ValueError, "CAL01_HUMAN_REVIEW_CROP_BINDING_DRIFT"):
            build_human_review_packet(_manifest(), comparison, [], source_width_px=7016)

    def test_packet_digest_is_independent_of_receipt_input_order(self):
        receipts = [
            _receipt("SG-T02-01", [492.0, 8291.0, 541.0, 8499.0], 4.95),
            _receipt("SG-T02-02", [486.0, 6865.0, 536.0, 7069.0], 6.25),
        ]
        forward = build_human_review_packet(_manifest(), _comparison(), receipts, source_width_px=7016)
        reverse = build_human_review_packet(_manifest(), _comparison(), list(reversed(receipts)), source_width_px=7016)
        self.assertEqual(forward["packet_digest"], reverse["packet_digest"])
        self.assertEqual(forward["reviews"], reverse["reviews"])

    def test_packet_authority_remains_closed(self):
        packet = build_human_review_packet(_manifest(), _comparison(), [], source_width_px=7016)
        self.assertEqual(packet["authority"], AUTHORITY_CLOSED)
        self.assertEqual(packet["primary_anchor_count"], 0)
        self.assertFalse(packet["eligible_for_metric_calibration"])
        self.assertTrue(all(row["primary_anchor_authorized"] is False for row in packet["reviews"]))
        self.assertTrue(all(row["eligible_for_metric_calibration"] is False for row in packet["reviews"]))

    def test_static_review_board_references_relative_exact_crops_and_states(self):
        packet = build_human_review_packet(_manifest(), _comparison(), [], source_width_px=7016)
        html = render_human_review_board(packet)
        self.assertIn('src="review-crops/top0.png"', html)
        self.assertIn("TAV-02S:TOP:TOP:R1:I0", html)
        self.assertIn("PENDING_HUMAN_REVIEW", html)
        self.assertIn("OCR_NO_PROPOSAL", html)
        self.assertNotIn("PRIMARY_VISUAL_VALIDATED", html)


if __name__ == "__main__":
    unittest.main()
