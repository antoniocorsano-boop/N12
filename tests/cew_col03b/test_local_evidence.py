from __future__ import annotations

import unittest

from experiments.cew_col03b.local_evidence import (
    build_callout_evidence,
    build_local_topology_signature,
    build_text_evidence,
    classify_text_relation,
    derive_local_region,
)


class LocalEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.occurrence_bbox = {"x": 0.40, "y": 0.40, "width": 0.10, "height": 0.10}
        self.local_region = derive_local_region(
            {"primary_graphical_representation": {"bbox": self.occurrence_bbox}},
            margin_x=0.10,
            margin_y=0.10,
        )

    def test_local_region_clips_to_source_bounds(self) -> None:
        region = derive_local_region(
            {"primary_graphical_representation": {"bbox": {"x": 0.01, "y": 0.02, "width": 0.05, "height": 0.04}}},
            margin_x=0.10,
            margin_y=0.10,
        )
        self.assertEqual(region, {"x": 0.0, "y": 0.0, "width": 0.16, "height": 0.16})

    def test_classifies_internal_intersecting_nearby_and_outside_text(self) -> None:
        internal = {"x": 0.42, "y": 0.42, "width": 0.02, "height": 0.02}
        intersecting = {"x": 0.48, "y": 0.44, "width": 0.05, "height": 0.02}
        nearby = {"x": 0.52, "y": 0.42, "width": 0.03, "height": 0.02}
        outside = {"x": 0.80, "y": 0.80, "width": 0.03, "height": 0.02}
        self.assertEqual(classify_text_relation(occurrence_bbox=self.occurrence_bbox, text_bbox=internal, local_region=self.local_region), "INTERNAL")
        self.assertEqual(classify_text_relation(occurrence_bbox=self.occurrence_bbox, text_bbox=intersecting, local_region=self.local_region), "INTERSECTING")
        self.assertEqual(classify_text_relation(occurrence_bbox=self.occurrence_bbox, text_bbox=nearby, local_region=self.local_region), "NEARBY")
        self.assertEqual(classify_text_relation(occurrence_bbox=self.occurrence_bbox, text_bbox=outside, local_region=self.local_region), "OUTSIDE")

    def test_text_evidence_preserves_raw_and_normalized_observation(self) -> None:
        evidence = build_text_evidence(
            evidence_id="TXT-1",
            occurrence_id="COL-OCC-0001",
            occurrence_bbox=self.occurrence_bbox,
            text_bbox={"x": 0.52, "y": 0.42, "width": 0.03, "height": 0.02},
            local_region=self.local_region,
            raw_text="  P 12 ",
            normalized_text="P12",
            extraction_method="OCR",
            provenance_ref="SRC-REGION-1",
        )
        self.assertEqual(evidence["raw_text"], "  P 12 ")
        self.assertEqual(evidence["normalized_text"], "P12")
        self.assertEqual(evidence["relation"], "NEARBY")
        self.assertEqual(evidence["evidence_class"], "PROXIMITY_ONLY")
        self.assertGreater(evidence["normalized_distance"], 0.0)

    def test_callout_without_connector_is_not_direct_binding(self) -> None:
        downgraded = build_callout_evidence(
            evidence_id="CALL-1",
            occurrence_id="COL-OCC-0001",
            text_evidence_id="TXT-1",
            connector_geometry=None,
            provenance_ref="SRC-REGION-1",
        )
        direct = build_callout_evidence(
            evidence_id="CALL-2",
            occurrence_id="COL-OCC-0001",
            text_evidence_id="TXT-2",
            connector_geometry={"points": [[0.45, 0.45], [0.55, 0.45]]},
            provenance_ref="SRC-REGION-2",
        )
        self.assertEqual(downgraded["evidence_class"], "PROXIMITY_ONLY")
        self.assertEqual(downgraded["binding_state"], "NO_CONNECTOR")
        self.assertEqual(direct["evidence_class"], "DIRECT_GRAPHICAL_BINDING")
        self.assertEqual(direct["binding_state"], "CONNECTOR_PRESENT")

    def test_local_topology_is_documentary_not_canonical(self) -> None:
        signature = build_local_topology_signature(
            occurrence_id="COL-OCC-0001",
            neighbors={"left": "COL-OCC-0002", "right": None, "up": "COL-OCC-0003", "down": None},
            contacts=["HORIZONTAL", "VERTICAL"],
            bay_order=3,
            provenance_ref="SRC-REGION-1",
        )
        self.assertEqual(signature["bay_order"], 3)
        self.assertEqual(signature["contacts"], ["HORIZONTAL", "VERTICAL"])
        for forbidden in ("canonical_node_id", "fixed_line_id", "grid_id", "vertical_chain_id"):
            self.assertNotIn(forbidden, signature)


if __name__ == "__main__":
    unittest.main()
