from __future__ import annotations

import unittest

from cew_spiral.dxf_documentary_bridge import analyze_dxf_documentary_grammar


class DxfDocumentaryBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = {
            "schema": "CEW_DXF01_OBSERVATION_BUNDLE_v1",
            "authority": {"authority_effect": "NONE"},
            "observations": [
                {
                    "source": {
                        "artifact_name": "TAV5_CARPENTERIA.dxf",
                        "sha256": "a" * 64,
                    },
                    "inventories": {
                        "text_entities": [
                            {"stable_id": "A", "text": "N001", "layer": "S-PIL-ID", "insert": [100.0, 200.0, 0.0], "rotation": 0.0, "height": 70.0},
                            {"stable_id": "B", "text": "N001", "layer": "S-ID-CAND-INF", "insert": [70.0, 170.0, 0.0], "rotation": 0.0, "height": 80.0},
                            {"stable_id": "C", "text": "N099", "layer": "S-ID-CAND-INF", "insert": [500.0, 600.0, 0.0], "rotation": 0.0, "height": 80.0},
                            {"stable_id": "D", "text": "G03 1.20m*", "layer": "S-METRIC-TEXT-INF", "insert": [300.0, 400.0, 0.0], "rotation": 0.0, "height": 60.0},
                            {"stable_id": "E", "text": "ORIGINAL NOTE", "layer": "0", "insert": [10.0, 20.0, 0.0], "rotation": 0.0, "height": 50.0},
                        ]
                    },
                    "authority": {
                        "authority_effect": "NONE",
                        "structural_identity_authorized": False,
                        "canonical_write_authorized": False,
                    },
                }
            ],
        }

    def test_cew_s_layers_are_derived_annotation_grammar_not_original_drafter_grammar(self) -> None:
        result = analyze_dxf_documentary_grammar(self.bundle)
        tav5 = result["sources"][0]
        by_id = {row["stable_id"]: row for row in tav5["tokens"]}
        self.assertEqual(by_id["A"]["grammar_origin"], "HISTORICAL_CEW_DERIVED_ANNOTATION")
        self.assertEqual(by_id["B"]["grammar_origin"], "HISTORICAL_CEW_DERIVED_ANNOTATION")
        self.assertFalse(by_id["A"]["eligible_to_teach_original_drafter_grammar"])
        self.assertFalse(by_id["B"]["eligible_to_teach_original_drafter_grammar"])
        self.assertEqual(by_id["E"]["grammar_origin"], "UNDETERMINED_SOURCE_GRAPHICS")

    def test_repeated_n_label_offset_is_recorded_as_historical_reconstruction_pattern(self) -> None:
        result = analyze_dxf_documentary_grammar(self.bundle)
        patterns = result["sources"][0]["cross_layer_patterns"]
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern["token"], "N001")
        self.assertAlmostEqual(pattern["delta_x"], -30.0)
        self.assertAlmostEqual(pattern["delta_y"], -30.0)
        self.assertAlmostEqual(pattern["distance"], 42.4264068712, places=6)
        self.assertEqual(pattern["interpretation"], "HISTORICAL_RECONSTRUCTION_DUPLICATION_PATTERN")
        self.assertFalse(pattern["structural_identity_authorized"])
        self.assertFalse(pattern["eligible_to_teach_original_drafter_grammar"])

    def test_token_classes_remain_proposal_only(self) -> None:
        result = analyze_dxf_documentary_grammar(self.bundle)
        tokens = {row["stable_id"]: row for row in result["sources"][0]["tokens"]}
        self.assertEqual(tokens["A"]["token_class"], "HISTORICAL_N_LABEL_TOKEN")
        self.assertEqual(tokens["C"]["token_class"], "HISTORICAL_N_LABEL_TOKEN")
        self.assertEqual(tokens["D"]["token_class"], "HISTORICAL_METRIC_TOKEN")
        for row in tokens.values():
            self.assertFalse(row["structural_identity_authorized"])
            self.assertFalse(row["canonical_write_authorized"])

    def test_result_preserves_closed_authority(self) -> None:
        result = analyze_dxf_documentary_grammar(self.bundle)
        self.assertEqual(result["authority"]["engineering_authority_effect"], "NONE")
        self.assertFalse(result["authority"]["structural_identity_authorized"])
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])
        self.assertFalse(result["authority"]["canonical_write_authorized"])
        self.assertFalse(result["authority"]["original_drafter_grammar_promotion_authorized"])

    def test_analysis_is_deterministic(self) -> None:
        self.assertEqual(
            analyze_dxf_documentary_grammar(self.bundle),
            analyze_dxf_documentary_grammar(self.bundle),
        )


if __name__ == "__main__":
    unittest.main()
