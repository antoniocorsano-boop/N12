from __future__ import annotations

import unittest

from cew_spiral.metric_comparison_replay import build_metric_comparison_replay


REGISTRATION_CSV = """sheet_id,level_id,source_frame,frame_width_px,frame_height_px,registration_method,metric_x_from_u,metric_x_from_v,metric_x_offset,metric_y_from_u,metric_y_from_v,metric_y_offset,evidence_state,validation_state,usage_rule\nTAV-05S,G4,ROT90_CCW_300DPI,12530,7016,SIFT_RANSAC_AFFINE_TO_TAV06S_PLUS_TAV06S_NUMBERED_SUPPORT_ANCHOR,0,-0.004,28,0.004,0,0,MIS+DOC,CROSS_VALIDATED,REGISTER_SHEET_TO_COMMON_PT_XY\n"""

NODES_CSV = """node_id,level_id,node_role,support_id,x_m,y_m\nM0G-C-G4-A,G4,SUPPORT_CORE,A,4.0,16.0\nM0G-C-G4-B,G4,SUPPORT_CORE,B,24.0,8.0\nM0G-C-G3-X,G3,SUPPORT_CORE,X,0.0,0.0\n"""


def bridge_payload() -> dict:
    return {
        "schema": "CEW_SPIRAL_EXACT_SOURCE_STRUCTURAL_CANDIDATE_BRIDGE_v1",
        "bridge": {
            "source": {"sha256": "2143dbcf" + "0" * 56, "path": "archive/documentazione_originaria/tavola 5.pdf", "page_index": 0},
            "governed_raster": {
                "frame": "RASTER_PIXEL",
                "width_px": 7016,
                "height_px": 12530,
                "raster_sha256": "4" * 64,
                "renderer_tool_id": "pypdfium2",
                "renderer_tool_version": "5.14.0",
            },
            "occurrence_bridge": [
                {
                    "occurrence_id": "COL-OCC-0001",
                    "object_candidate_id": "OBJ-1",
                    "evidence_candidate_id": "EV-1",
                    "pixel_geometry": {"frame": "RASTER_PIXEL", "x": 916.0, "y": 4925.0, "width": 200.0, "height": 150.0},
                    "structural_identity_authorized": False,
                    "canonical_write_authorized": False,
                }
            ],
            "structural_candidate_count": 1,
            "authority": {
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
                "m0g_authorized": False,
            },
        },
        "qualification": {
            "exact_source_replayable": True,
            "structural_candidate_count": 1,
            "historical_comparator_loaded": False,
        },
    }


class MetricComparisonReplayTests(unittest.TestCase):
    def test_builds_replay_from_frozen_bridge_and_csv_witnesses(self) -> None:
        result = build_metric_comparison_replay(
            structural_bridge_payload=bridge_payload(),
            registration_csv=REGISTRATION_CSV,
            historical_nodes_csv=NODES_CSV,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
        )
        self.assertEqual(result["schema"], "CEW_SPIRAL_METRIC_COMPARISON_REPLAY_v1")
        self.assertEqual(result["comparison"]["projection_count"], 1)
        self.assertEqual(result["comparison"]["comparison_count"], 1)
        self.assertEqual(result["comparison"]["summary"]["distance_count"], 1)
        self.assertEqual(result["input_boundary"]["structural_candidate_count"], 1)
        self.assertEqual(result["input_boundary"]["historical_comparator_loaded_before_replay"], False)
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])
        self.assertFalse(result["authority"]["structural_identity_authorized"])
        self.assertFalse(result["authority"]["canonical_write_authorized"])
        self.assertFalse(result["authority"]["m0g_authorized"])

    def test_rejects_unqualified_or_preloaded_bridge(self) -> None:
        bad = bridge_payload()
        bad["qualification"]["exact_source_replayable"] = False
        with self.assertRaisesRegex(ValueError, "STRUCTURAL_BRIDGE_NOT_EXACT_SOURCE_QUALIFIED"):
            build_metric_comparison_replay(
                structural_bridge_payload=bad,
                registration_csv=REGISTRATION_CSV,
                historical_nodes_csv=NODES_CSV,
                registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
                comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
            )
        bad = bridge_payload()
        bad["qualification"]["historical_comparator_loaded"] = True
        with self.assertRaisesRegex(ValueError, "HISTORICAL_COMPARATOR_PRELOADED"):
            build_metric_comparison_replay(
                structural_bridge_payload=bad,
                registration_csv=REGISTRATION_CSV,
                historical_nodes_csv=NODES_CSV,
                registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
                comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
            )

    def test_same_inputs_are_deterministic(self) -> None:
        kwargs = dict(
            structural_bridge_payload=bridge_payload(),
            registration_csv=REGISTRATION_CSV,
            historical_nodes_csv=NODES_CSV,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
        )
        self.assertEqual(build_metric_comparison_replay(**kwargs), build_metric_comparison_replay(**kwargs))


if __name__ == "__main__":
    unittest.main()
