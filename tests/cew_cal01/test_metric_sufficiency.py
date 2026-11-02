import copy
import unittest

from experiments.cew_cal01.metric_sufficiency import build_metric_relation_network


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}

SOURCE_SHA = "c" * 64
REVIEW_DIGEST = "sha256:" + "d" * 64


def _manifest():
    rows = [
        {
            "review_id": "TAV-X:TOP:TOP:R1:I0",
            "side": "TOP",
            "chain_id": "TOP:R1",
            "interval_index": 0,
            "orientation": "HORIZONTAL",
            "carrier_axis_px": 50.0,
            "interval_start_px": 100.0,
            "interval_end_px": 300.0,
        },
        {
            "review_id": "TAV-X:TOP:TOP:R1:I1",
            "side": "TOP",
            "chain_id": "TOP:R1",
            "interval_index": 1,
            "orientation": "HORIZONTAL",
            "carrier_axis_px": 50.0,
            "interval_start_px": 300.0,
            "interval_end_px": 500.0,
        },
        {
            "review_id": "TAV-X:RIGHT:RIGHT:R1:I0",
            "side": "RIGHT",
            "chain_id": "RIGHT:R1",
            "interval_index": 0,
            "orientation": "VERTICAL",
            "carrier_axis_px": 600.0,
            "interval_start_px": 50.0,
            "interval_end_px": 250.0,
        },
        {
            "review_id": "TAV-X:RIGHT:RIGHT:R1:I1",
            "side": "RIGHT",
            "chain_id": "RIGHT:R1",
            "interval_index": 1,
            "orientation": "VERTICAL",
            "carrier_axis_px": 600.0,
            "interval_start_px": 250.0,
            "interval_end_px": 450.0,
        },
    ]
    return {
        "schema": "CEW_CAL01_INTERVAL_TEXT_REVIEW_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-X", "sha256": SOURCE_SHA},
        "review_request_count": len(rows),
        "review_requests": rows,
        "review_digest": REVIEW_DIGEST,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


def _packet():
    rows = [
        {
            "review_id": "TAV-X:TOP:TOP:R1:I0",
            "side": "TOP",
            "chain_id": "TOP:R1",
            "interval_index": 0,
            "review_state": "DIRECT_HUMAN_DECISION",
            "validated_value_m": 1.0,
            "eligible_for_metric_calibration": False,
            "primary_anchor_authorized": False,
        },
        {
            "review_id": "TAV-X:TOP:TOP:R1:I1",
            "side": "TOP",
            "chain_id": "TOP:R1",
            "interval_index": 1,
            "review_state": "REUSED_HUMAN_RECEIPT",
            "validated_value_m": 1.0,
            "eligible_for_metric_calibration": False,
            "primary_anchor_authorized": False,
        },
        {
            "review_id": "TAV-X:RIGHT:RIGHT:R1:I0",
            "side": "RIGHT",
            "chain_id": "RIGHT:R1",
            "interval_index": 0,
            "review_state": "DIRECT_HUMAN_DECISION",
            "validated_value_m": 1.0,
            "eligible_for_metric_calibration": False,
            "primary_anchor_authorized": False,
        },
        {
            "review_id": "TAV-X:RIGHT:RIGHT:R1:I1",
            "side": "RIGHT",
            "chain_id": "RIGHT:R1",
            "interval_index": 1,
            "review_state": "PENDING_HUMAN_REVIEW",
            "validated_value_m": None,
            "eligible_for_metric_calibration": False,
            "primary_anchor_authorized": False,
        },
    ]
    return {
        "schema": "CEW_CAL01_EXTERNAL_CHAIN_HUMAN_REVIEW_PACKET_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-X", "sha256": SOURCE_SHA},
        "review_manifest_digest": REVIEW_DIGEST,
        "review_count": len(rows),
        "validated_human_relation_count": 3,
        "pending_human_review_count": 1,
        "reviews": rows,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class MetricRelationNetworkTests(unittest.TestCase):
    def test_builds_source_local_relations_from_governed_geometry_and_human_values(self):
        network = build_metric_relation_network(_manifest(), _packet())
        self.assertEqual(network["source"], {"source_id": "TAV-X", "sha256": SOURCE_SHA})
        self.assertEqual(network["relation_count"], 3)
        self.assertEqual(network["pending_review_count"], 1)
        self.assertEqual(network["orientation_counts"], {"HORIZONTAL": 2, "VERTICAL": 1})
        self.assertEqual(network["side_counts"], {"RIGHT": 1, "TOP": 2})
        self.assertEqual(network["complete_chain_ids"], ["TOP:R1"])

        rows = {row["review_id"]: row for row in network["relations"]}
        top = rows["TAV-X:TOP:TOP:R1:I0"]
        self.assertEqual(top["source_point_a_px"], [100.0, 50.0])
        self.assertEqual(top["source_point_b_px"], [300.0, 50.0])
        self.assertEqual(top["pixel_span"], 200.0)
        self.assertEqual(top["validated_value_m"], 1.0)
        self.assertEqual(top["px_per_m"], 200.0)
        self.assertEqual(top["human_provenance_state"], "DIRECT_HUMAN_DECISION")
        self.assertFalse(top["eligible_for_metric_calibration"])
        self.assertFalse(top["primary_anchor_authorized"])

        right = rows["TAV-X:RIGHT:RIGHT:R1:I0"]
        self.assertEqual(right["source_point_a_px"], [600.0, 50.0])
        self.assertEqual(right["source_point_b_px"], [600.0, 250.0])

        self.assertEqual(
            network["pending_reviews"],
            [
                {
                    "review_id": "TAV-X:RIGHT:RIGHT:R1:I1",
                    "side": "RIGHT",
                    "chain_id": "RIGHT:R1",
                    "interval_index": 1,
                    "orientation": "VERTICAL",
                    "validated_value_m": None,
                }
            ],
        )

    def test_source_or_manifest_digest_drift_fails_closed(self):
        packet = _packet()
        packet["source"]["sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "CAL01_METRIC_NETWORK_SOURCE_DRIFT"):
            build_metric_relation_network(_manifest(), packet)

        packet = _packet()
        packet["review_manifest_digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(ValueError, "CAL01_METRIC_NETWORK_MANIFEST_DIGEST_DRIFT"):
            build_metric_relation_network(_manifest(), packet)

    def test_validated_relation_requires_positive_metric_value(self):
        packet = _packet()
        packet["reviews"][0]["validated_value_m"] = 0.0
        with self.assertRaisesRegex(ValueError, "CAL01_METRIC_NETWORK_VALUE_INVALID"):
            build_metric_relation_network(_manifest(), packet)

    def test_output_is_deterministic_and_authority_remains_closed(self):
        forward = build_metric_relation_network(_manifest(), _packet())
        manifest = _manifest()
        packet = _packet()
        manifest["review_requests"] = list(reversed(manifest["review_requests"]))
        packet["reviews"] = list(reversed(packet["reviews"]))
        reverse = build_metric_relation_network(manifest, packet)
        self.assertEqual(forward["network_digest"], reverse["network_digest"])
        self.assertEqual(forward["relations"], reverse["relations"])
        self.assertEqual(forward["authority"], AUTHORITY_CLOSED)
        self.assertEqual(forward["primary_anchor_count"], 0)
        self.assertFalse(forward["eligible_for_metric_calibration"])


if __name__ == "__main__":
    unittest.main()
