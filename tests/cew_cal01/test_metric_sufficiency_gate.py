import unittest

from experiments.cew_cal01.metric_sufficiency import (
    audit_metric_relation_network,
    evaluate_metric_sufficiency,
    rank_targeted_human_review,
)


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}

SOURCE_SHA = "c" * 64


def _relation(review_id, side, chain_id, interval_index, orientation, px_per_m=200.0):
    span = float(px_per_m)
    if orientation == "HORIZONTAL":
        point_a = [float(interval_index) * span, 10.0]
        point_b = [(float(interval_index) + 1.0) * span, 10.0]
    else:
        point_a = [20.0, float(interval_index) * span]
        point_b = [20.0, (float(interval_index) + 1.0) * span]
    return {
        "review_id": review_id,
        "side": side,
        "chain_id": chain_id,
        "interval_index": interval_index,
        "orientation": orientation,
        "source_point_a_px": point_a,
        "source_point_b_px": point_b,
        "pixel_span": span,
        "validated_value_m": 1.0,
        "px_per_m": float(px_per_m),
        "human_provenance_state": "DIRECT_HUMAN_DECISION",
        "eligible_for_metric_calibration": False,
        "primary_anchor_authorized": False,
    }


def _pending(review_id, side, chain_id, interval_index, orientation):
    return {
        "review_id": review_id,
        "side": side,
        "chain_id": chain_id,
        "interval_index": interval_index,
        "orientation": orientation,
        "validated_value_m": None,
    }


def _network(relations, pending, chain_stats):
    orientation_counts = {}
    side_counts = {}
    for row in relations:
        orientation_counts[row["orientation"]] = orientation_counts.get(row["orientation"], 0) + 1
        side_counts[row["side"]] = side_counts.get(row["side"], 0) + 1
    return {
        "schema": "CEW_CAL01_METRIC_RELATION_NETWORK_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-X", "sha256": SOURCE_SHA},
        "review_manifest_digest": "sha256:" + "a" * 64,
        "human_review_packet_digest": "sha256:" + "b" * 64,
        "relation_count": len(relations),
        "pending_review_count": len(pending),
        "orientation_counts": dict(sorted(orientation_counts.items())),
        "side_counts": dict(sorted(side_counts.items())),
        "chain_stats": sorted(chain_stats, key=lambda row: row["chain_id"]),
        "complete_chain_ids": sorted(row["chain_id"] for row in chain_stats if row["complete"]),
        "relations": sorted(relations, key=lambda row: row["review_id"]),
        "pending_reviews": sorted(pending, key=lambda row: row["review_id"]),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "network_digest": "sha256:" + "n" * 64,
    }


def _coherent_network():
    relations = [
        _relation("TAV-X:TOP:TOP:R1:I0", "TOP", "TOP:R1", 0, "HORIZONTAL"),
        _relation("TAV-X:TOP:TOP:R1:I1", "TOP", "TOP:R1", 1, "HORIZONTAL"),
        _relation("TAV-X:RIGHT:RIGHT:R1:I0", "RIGHT", "RIGHT:R1", 0, "VERTICAL"),
        _relation("TAV-X:RIGHT:RIGHT:R1:I1", "RIGHT", "RIGHT:R1", 1, "VERTICAL"),
    ]
    chain_stats = [
        {
            "chain_id": "TOP:R1",
            "total_interval_count": 2,
            "validated_interval_count": 2,
            "pending_interval_count": 0,
            "complete": True,
        },
        {
            "chain_id": "RIGHT:R1",
            "total_interval_count": 2,
            "validated_interval_count": 2,
            "pending_interval_count": 0,
            "complete": True,
        },
    ]
    return _network(relations, [], chain_stats)


def _eligible_anchor_inventory(collinear=False):
    if collinear:
        source_points = [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]]
        metric_points = [[0.0, 0.0], [2.0, 0.0], [4.0, 0.0], [6.0, 0.0]]
    else:
        source_points = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        metric_points = [[0.0, 0.0], [2.0, 0.0], [0.0, 2.0], [2.0, 2.0]]
    anchors = []
    for index, (source_point, metric_point) in enumerate(zip(source_points, metric_points)):
        anchors.append(
            {
                "anchor_id": f"A{index}",
                "source_version_sha256": SOURCE_SHA,
                "source_point_px": source_point,
                "metric_xy_m": metric_point,
                "eligible_for_fit": True,
                "rejection_reasons": [],
                "authority": dict(AUTHORITY_CLOSED),
            }
        )
    return {
        "program": "CEW-CAL-01",
        "artifact": "CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1",
        "source_version_sha256": SOURCE_SHA,
        "anchor_count": len(anchors),
        "eligible_anchor_count": len(anchors),
        "anchors": anchors,
        "authority": dict(AUTHORITY_CLOSED),
    }


class MetricRelationAuditTests(unittest.TestCase):
    def test_coherent_two_orientation_network_is_diagnostically_sufficient(self):
        audit = audit_metric_relation_network(_coherent_network())
        self.assertEqual(audit["diagnostic_status"], "RELATION_NETWORK_DIAGNOSTIC_SUFFICIENT")
        self.assertEqual(audit["blockers"], [])
        self.assertEqual(audit["orientation_diagnostics"]["HORIZONTAL"]["median_px_per_m"], 200.0)
        self.assertEqual(audit["orientation_diagnostics"]["VERTICAL"]["median_px_per_m"], 200.0)
        self.assertEqual(audit["cross_orientation_median_drift_ratio"], 0.0)
        self.assertEqual(audit["authority"], AUTHORITY_CLOSED)
        self.assertFalse(audit["eligible_for_metric_calibration"])

    def test_relation_scale_outlier_above_five_percent_fails_diagnostic_sufficiency(self):
        network = _coherent_network()
        horizontal = next(
            row for row in network["relations"]
            if row["review_id"] == "TAV-X:TOP:TOP:R1:I1"
        )
        horizontal["px_per_m"] = 230.0
        horizontal["pixel_span"] = 230.0
        audit = audit_metric_relation_network(network)
        self.assertEqual(audit["diagnostic_status"], "RELATION_NETWORK_DIAGNOSTIC_INSUFFICIENT")
        self.assertIn("HORIZONTAL_SCALE_OUTLIER", audit["blockers"])


class TargetedHumanReviewTests(unittest.TestCase):
    def test_one_missing_chain_interval_is_ranked_before_other_information_gaps(self):
        relations = [
            _relation("TAV-X:RIGHT:RIGHT:R1:I0", "RIGHT", "RIGHT:R1", 0, "VERTICAL")
        ]
        pending = [
            _pending("TAV-X:RIGHT:RIGHT:R1:I1", "RIGHT", "RIGHT:R1", 1, "VERTICAL"),
            _pending("TAV-X:TOP:TOP:R1:I0", "TOP", "TOP:R1", 0, "HORIZONTAL"),
            _pending("TAV-X:BOTTOM:BOTTOM:R1:I0", "BOTTOM", "BOTTOM:R1", 0, "HORIZONTAL"),
            _pending("TAV-X:LEFT:LEFT:R1:I0", "LEFT", "LEFT:R1", 0, "VERTICAL"),
        ]
        chain_stats = [
            {
                "chain_id": "RIGHT:R1",
                "total_interval_count": 2,
                "validated_interval_count": 1,
                "pending_interval_count": 1,
                "complete": False,
            },
            {
                "chain_id": "TOP:R1",
                "total_interval_count": 1,
                "validated_interval_count": 0,
                "pending_interval_count": 1,
                "complete": False,
            },
            {
                "chain_id": "BOTTOM:R1",
                "total_interval_count": 1,
                "validated_interval_count": 0,
                "pending_interval_count": 1,
                "complete": False,
            },
            {
                "chain_id": "LEFT:R1",
                "total_interval_count": 1,
                "validated_interval_count": 0,
                "pending_interval_count": 1,
                "complete": False,
            },
        ]
        network = _network(relations, pending, chain_stats)
        ranked = rank_targeted_human_review(network)
        self.assertEqual(ranked[0], "TAV-X:RIGHT:RIGHT:R1:I1")
        self.assertLess(ranked.index("TAV-X:BOTTOM:BOTTOM:R1:I0"), ranked.index("TAV-X:LEFT:LEFT:R1:I0"))
        self.assertLess(ranked.index("TAV-X:TOP:TOP:R1:I0"), ranked.index("TAV-X:LEFT:LEFT:R1:I0"))

    def test_tav01_like_network_requests_targeted_review_without_inventing_values(self):
        relations = [
            _relation("TAV-X:RIGHT:RIGHT:R1:I0", "RIGHT", "RIGHT:R1", 0, "VERTICAL")
        ]
        pending = [
            _pending("TAV-X:RIGHT:RIGHT:R1:I1", "RIGHT", "RIGHT:R1", 1, "VERTICAL"),
            _pending("TAV-X:TOP:TOP:R1:I0", "TOP", "TOP:R1", 0, "HORIZONTAL"),
        ]
        chain_stats = [
            {
                "chain_id": "RIGHT:R1",
                "total_interval_count": 2,
                "validated_interval_count": 1,
                "pending_interval_count": 1,
                "complete": False,
            },
            {
                "chain_id": "TOP:R1",
                "total_interval_count": 1,
                "validated_interval_count": 0,
                "pending_interval_count": 1,
                "complete": False,
            },
        ]
        gate = evaluate_metric_sufficiency(_network(relations, pending, chain_stats))
        self.assertEqual(gate["gate_state"], "TARGETED_HUMAN_REVIEW")
        self.assertEqual(gate["next_action"], "TARGETED_HUMAN_REVIEW")
        self.assertTrue(gate["targeted_human_review_ids"])
        self.assertNotIn("validated_value_m", gate["targeted_human_review_ids"])
        self.assertFalse(gate["eligible_for_metric_calibration"])


class MetricSufficiencyGateTests(unittest.TestCase):
    def test_coherent_relation_network_without_primary_anchors_remains_insufficient(self):
        gate = evaluate_metric_sufficiency(_coherent_network())
        self.assertEqual(gate["relation_audit"]["diagnostic_status"], "RELATION_NETWORK_DIAGNOSTIC_SUFFICIENT")
        self.assertEqual(gate["gate_state"], "INSUFFICIENT")
        self.assertEqual(gate["blockers"], ["PRIMARY_ANCHOR_REQUIRED"])
        self.assertEqual(gate["next_action"], "PRIMARY_ANCHOR_DISCOVERY")
        self.assertEqual(gate["targeted_human_review_ids"], [])
        self.assertFalse(gate["eligible_for_metric_calibration"])
        self.assertEqual(gate["authority"], AUTHORITY_CLOSED)

    def test_four_non_collinear_eligible_anchors_allow_calibration_candidate_gate_only(self):
        gate = evaluate_metric_sufficiency(_coherent_network(), _eligible_anchor_inventory())
        self.assertEqual(gate["gate_state"], "SUFFICIENT_FOR_CALIBRATION_CANDIDATE")
        self.assertEqual(gate["blockers"], [])
        self.assertEqual(gate["next_action"], "BUILD_CALIBRATION_CANDIDATE")
        self.assertEqual(gate["eligible_primary_anchor_count"], 4)
        self.assertEqual(gate["holdout_anchor_capacity"], 1)
        self.assertTrue(gate["eligible_for_metric_calibration"])
        self.assertEqual(gate["authority"], AUTHORITY_CLOSED)
        self.assertFalse(gate["authority"]["canonical_geometry_authorized"])

    def test_collinear_eligible_anchors_fail_closed(self):
        gate = evaluate_metric_sufficiency(_coherent_network(), _eligible_anchor_inventory(collinear=True))
        self.assertEqual(gate["gate_state"], "INSUFFICIENT")
        self.assertIn("PRIMARY_ANCHOR_GEOMETRY_DEGENERATE", gate["blockers"])
        self.assertFalse(gate["eligible_for_metric_calibration"])

    def test_anchor_inventory_source_mismatch_fails_closed(self):
        inventory = _eligible_anchor_inventory()
        inventory["source_version_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "CAL01_METRIC_GATE_ANCHOR_SOURCE_DRIFT"):
            evaluate_metric_sufficiency(_coherent_network(), inventory)


if __name__ == "__main__":
    unittest.main()
