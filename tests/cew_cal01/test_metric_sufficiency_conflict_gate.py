import unittest

from experiments.cew_cal01.metric_sufficiency import evaluate_metric_sufficiency


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _relation(review_id, side, chain_id, interval_index, orientation, px_per_m):
    return {
        "review_id": review_id,
        "side": side,
        "chain_id": chain_id,
        "interval_index": interval_index,
        "orientation": orientation,
        "source_point_a_px": [0.0, 0.0],
        "source_point_b_px": [float(px_per_m), 0.0],
        "pixel_span": float(px_per_m),
        "validated_value_m": 1.0,
        "px_per_m": float(px_per_m),
        "human_provenance_state": "DIRECT_HUMAN_DECISION",
        "eligible_for_metric_calibration": False,
        "primary_anchor_authorized": False,
    }


def _network_with_documented_scale_conflict_and_pending_review():
    relations = [
        _relation("TAV-X:TOP:TOP:R1:I0", "TOP", "TOP:R1", 0, "HORIZONTAL", 200.0),
        _relation("TAV-X:TOP:TOP:R1:I1", "TOP", "TOP:R1", 1, "HORIZONTAL", 230.0),
        _relation("TAV-X:RIGHT:RIGHT:R1:I0", "RIGHT", "RIGHT:R1", 0, "VERTICAL", 200.0),
        _relation("TAV-X:RIGHT:RIGHT:R1:I1", "RIGHT", "RIGHT:R1", 1, "VERTICAL", 200.0),
    ]
    return {
        "schema": "CEW_CAL01_METRIC_RELATION_NETWORK_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-X", "sha256": "c" * 64},
        "review_manifest_digest": "sha256:" + "a" * 64,
        "human_review_packet_digest": "sha256:" + "b" * 64,
        "relation_count": 4,
        "pending_review_count": 1,
        "orientation_counts": {"HORIZONTAL": 2, "VERTICAL": 2},
        "side_counts": {"RIGHT": 2, "TOP": 2},
        "chain_stats": [
            {
                "chain_id": "TOP:R1",
                "total_interval_count": 2,
                "validated_interval_count": 2,
                "pending_interval_count": 0,
                "complete": True,
            },
            {
                "chain_id": "RIGHT:R1",
                "total_interval_count": 3,
                "validated_interval_count": 2,
                "pending_interval_count": 1,
                "complete": False,
            },
        ],
        "complete_chain_ids": ["TOP:R1"],
        "relations": relations,
        "pending_reviews": [
            {
                "review_id": "TAV-X:RIGHT:RIGHT:R1:I2",
                "side": "RIGHT",
                "chain_id": "RIGHT:R1",
                "interval_index": 2,
                "orientation": "VERTICAL",
                "validated_value_m": None,
            }
        ],
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "network_digest": "sha256:" + "n" * 64,
    }


class MetricSufficiencyConflictGateTests(unittest.TestCase):
    def test_documented_scale_conflict_is_non_review_blocker_even_when_pending_rows_exist(self):
        gate = evaluate_metric_sufficiency(_network_with_documented_scale_conflict_and_pending_review())

        self.assertEqual(gate["gate_state"], "INSUFFICIENT")
        self.assertEqual(gate["next_action"], "RESOLVE_METRIC_RELATION_CONFLICT")
        self.assertEqual(gate["targeted_human_review_ids"], [])
        self.assertIn("HORIZONTAL_SCALE_OUTLIER", gate["blockers"])
        self.assertIn("ORIENTATION_SCALE_DRIFT", gate["blockers"])
        self.assertFalse(gate["eligible_for_metric_calibration"])
        self.assertEqual(gate["authority"], AUTHORITY_CLOSED)


if __name__ == "__main__":
    unittest.main()
