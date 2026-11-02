import copy
import unittest

from experiments.cew_cal01.reference_lattice import build_reference_lattice


SOURCE_SHA = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _relation(review_id, side, chain_id, interval_index, orientation, a, b, value_m):
    span = (b[0] - a[0]) if orientation == "HORIZONTAL" else (b[1] - a[1])
    return {
        "review_id": review_id,
        "side": side,
        "chain_id": chain_id,
        "interval_index": interval_index,
        "orientation": orientation,
        "source_point_a_px": [float(a[0]), float(a[1])],
        "source_point_b_px": [float(b[0]), float(b[1])],
        "pixel_span": float(span),
        "validated_value_m": float(value_m),
        "px_per_m": float(span) / float(value_m),
        "human_provenance_state": "DIRECT_HUMAN_DECISION",
        "eligible_for_metric_calibration": False,
        "primary_anchor_authorized": False,
    }


def _network():
    x = [4233.375, 5346.2, 6542.75, 7517.5, 8493.625, 9743.5, 10857.166667]
    xv = [4.70, 5.10, 4.15, 4.15, 5.30, 4.70]
    y = [3805.0, 4290.458334, 5107.166667]
    yv = [2.10, 3.45]
    relations = []
    for i, value in enumerate(xv):
        relations.append(
            _relation(
                f"TAV-02S:TOP:TOP:R1:I{i}",
                "TOP",
                "TOP:R1",
                i,
                "HORIZONTAL",
                [x[i], 551.415493],
                [x[i + 1], 551.415493],
                value,
            )
        )
    for i, value in enumerate(yv):
        relations.append(
            _relation(
                f"TAV-02S:RIGHT:RIGHT:R1:I{i}",
                "RIGHT",
                "RIGHT:R1",
                i,
                "VERTICAL",
                [11158.421875, y[i]],
                [11158.421875, y[i + 1]],
                value,
            )
        )
    return {
        "schema": "CEW_CAL01_METRIC_RELATION_NETWORK_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-02S", "sha256": SOURCE_SHA},
        "review_manifest_digest": "sha256:" + "a" * 64,
        "human_review_packet_digest": "sha256:" + "b" * 64,
        "relation_count": len(relations),
        "pending_review_count": 9,
        "orientation_counts": {"HORIZONTAL": 6, "VERTICAL": 2},
        "side_counts": {"RIGHT": 2, "TOP": 6},
        "chain_stats": [],
        "complete_chain_ids": ["TOP:R1"],
        "relations": relations,
        "pending_reviews": [
            {
                "review_id": "TAV-02S:LEFT:LEFT:R1:I0",
                "side": "LEFT",
                "chain_id": "LEFT:R1",
                "interval_index": 0,
                "orientation": "VERTICAL",
                "validated_value_m": None,
            }
        ],
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "network_digest": "sha256:" + "n" * 64,
    }


class ReferenceLatticeTests(unittest.TestCase):
    def test_top_and_right_relations_build_local_reference_lattice(self):
        lattice = build_reference_lattice(_network())
        self.assertEqual(lattice["schema"], "CEW_CAL01_TAV02_REFERENCE_LATTICE_v1")
        self.assertEqual(lattice["coordinate_frame"], "LOCAL_RELATIVE_METRIC")
        self.assertEqual(lattice["x_reference_count"], 7)
        self.assertEqual(lattice["y_reference_count"], 3)
        self.assertEqual(lattice["lattice_node_count"], 21)
        self.assertEqual(
            [row["local_m"] for row in lattice["x_references"]],
            [0.0, 4.7, 9.8, 13.95, 18.1, 23.4, 28.1],
        )
        self.assertEqual(
            [row["local_m"] for row in lattice["y_references"]],
            [0.0, 2.1, 5.55],
        )
        self.assertEqual(lattice["reference_origin"]["local_xy_m"], [0.0, 0.0])
        self.assertFalse(lattice["reference_origin"]["absolute_origin_authorized"])
        self.assertEqual(lattice["authority"], AUTHORITY_CLOSED)

    def test_coordinate_provenance_is_cumulative_and_pending_relations_are_ignored(self):
        lattice = build_reference_lattice(_network())
        self.assertEqual(lattice["x_references"][0]["relation_refs"], [])
        self.assertEqual(
            lattice["x_references"][2]["relation_refs"],
            ["TAV-02S:TOP:TOP:R1:I0", "TAV-02S:TOP:TOP:R1:I1"],
        )
        self.assertEqual(
            lattice["y_references"][2]["relation_refs"],
            ["TAV-02S:RIGHT:RIGHT:R1:I0", "TAV-02S:RIGHT:RIGHT:R1:I1"],
        )
        serialized = repr(lattice)
        self.assertNotIn("TAV-02S:LEFT:LEFT:R1:I0", serialized)

    def test_input_order_does_not_change_lattice_digest(self):
        forward = build_reference_lattice(_network())
        reverse_network = copy.deepcopy(_network())
        reverse_network["relations"] = list(reversed(reverse_network["relations"]))
        reverse = build_reference_lattice(reverse_network)
        self.assertEqual(forward["lattice_digest"], reverse["lattice_digest"])
        self.assertEqual(forward["lattice_nodes"], reverse["lattice_nodes"])

    def test_missing_or_non_contiguous_required_chain_fails_closed(self):
        network = _network()
        network["relations"] = [
            row
            for row in network["relations"]
            if row["review_id"] != "TAV-02S:TOP:TOP:R1:I3"
        ]
        with self.assertRaisesRegex(ValueError, "CAL01_REFERENCE_LATTICE_TOP_CHAIN_INCOMPLETE"):
            build_reference_lattice(network)

        network = _network()
        network["relations"] = [
            row
            for row in network["relations"]
            if row["review_id"] != "TAV-02S:RIGHT:RIGHT:R1:I1"
        ]
        with self.assertRaisesRegex(ValueError, "CAL01_REFERENCE_LATTICE_RIGHT_CHAIN_INCOMPLETE"):
            build_reference_lattice(network)


if __name__ == "__main__":
    unittest.main()
