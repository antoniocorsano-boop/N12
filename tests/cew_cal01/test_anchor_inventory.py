import json
import unittest
from pathlib import Path

from experiments.cew_cal01.anchor_inventory import (
    ALLOWED_ANCHOR_CLASSES,
    FIT_ELIGIBLE_METRIC_SOURCE_POLICY,
    build_primary_anchor_inventory,
    make_anchor_candidate,
)


SCHEMA = Path("governance/cew-cal01/CEW_CAL01_ANCHOR_SCHEMA_v1.json")
SOURCE_SHA = "9d8f0c6a6f8c2be06b00d58f8f4f5db17f5a3b958637f35cf83bc5fdd7df2a30"


class Cal01PrimaryAnchorContractTests(unittest.TestCase):
    def _valid(self, **overrides):
        kwargs = {
            "anchor_class": "STRUCTURAL_AXIS_INTERSECTION",
            "source_version_sha256": SOURCE_SHA,
            "source_page": 1,
            "source_point_px": [1200.0, 2200.0],
            "metric_xy_m": [4.70, 9.80],
            "metric_provenance": {"x": "DOC", "y": "DOC"},
            "evidence_refs": ["TAV5:axis-A", "TAV5:axis-3"],
            "metric_source_kind": "PRIMARY_TAV5_DOCUMENTED_RELATION",
            "source_layer": "ORIGINAL_DRAWING",
            "metric_validation_state": "PRIMARY_VISUAL_VALIDATED",
            "metric_validation_ref": "CEW-CAL01-PRIMARY-REVIEW:synthetic-fixture",
        }
        kwargs.update(overrides)
        return make_anchor_candidate(**kwargs)

    def test_anchor_id_is_deterministic_and_inventory_digest_is_order_independent(self):
        a1 = self._valid()
        a2 = self._valid()
        self.assertEqual(a1["anchor_id"], a2["anchor_id"])
        self.assertTrue(a1["eligible_for_fit"])

        other = self._valid(
            source_point_px=[3200.0, 4200.0],
            metric_xy_m=[9.80, 13.95],
            evidence_refs=["TAV5:axis-B", "TAV5:axis-4"],
        )
        inv1 = build_primary_anchor_inventory([a1, other], SOURCE_SHA)
        inv2 = build_primary_anchor_inventory([other, a1], SOURCE_SHA)
        self.assertEqual(inv1["inventory_digest"], inv2["inventory_digest"])
        self.assertEqual([r["anchor_id"] for r in inv1["anchors"]], sorted([a1["anchor_id"], other["anchor_id"]]))

    def test_allowed_classes_are_bounded(self):
        self.assertEqual(
            ALLOWED_ANCHOR_CLASSES,
            {
                "STRUCTURAL_AXIS_INTERSECTION",
                "DIMENSION_CHAIN_ENDPOINT",
                "DOCUMENTED_REFERENCE_INTERSECTION",
                "SOURCE_NATIVE_METRIC_POINT",
            },
        )
        rejected = self._valid(anchor_class="NEAREST_HISTORICAL_NODE")
        self.assertFalse(rejected["eligible_for_fit"])
        self.assertIn("ANCHOR_CLASS_NOT_ALLOWED", rejected["rejection_reasons"])

    def test_historical_and_cew_derived_inputs_are_rejected_for_fit(self):
        for metric_source_kind in (
            "HISTORICAL_M0G",
            "HISTORICAL_AFFINE_REGISTRATION",
            "HISTORICAL_CEW_DERIVED_ANNOTATION",
        ):
            with self.subTest(metric_source_kind=metric_source_kind):
                row = self._valid(metric_source_kind=metric_source_kind)
                self.assertFalse(row["eligible_for_fit"])
                self.assertIn("FORBIDDEN_METRIC_SOURCE", row["rejection_reasons"])

        s_layer = self._valid(source_layer="S-PIL-ID")
        self.assertFalse(s_layer["eligible_for_fit"])
        self.assertIn("HISTORICAL_CEW_LAYER_NOT_PRIMARY", s_layer["rejection_reasons"])

    def test_ocr_text_without_geometric_binding_is_rejected(self):
        row = self._valid(
            source_point_px=None,
            metric_source_kind="OCR_TEXT_ONLY",
            evidence_refs=["OCR:470"],
            metric_validation_state=None,
            metric_validation_ref=None,
        )
        self.assertFalse(row["eligible_for_fit"])
        self.assertIn("SOURCE_POINT_MISSING", row["rejection_reasons"])
        self.assertIn("OCR_TEXT_WITHOUT_GEOMETRIC_BINDING", row["rejection_reasons"])
        self.assertIn("METRIC_SOURCE_KIND_NOT_FIT_ELIGIBLE", row["rejection_reasons"])

    def test_metric_coordinates_require_supported_provenance(self):
        missing = self._valid(metric_xy_m=None)
        self.assertFalse(missing["eligible_for_fit"])
        self.assertIn("METRIC_COORDINATE_MISSING", missing["rejection_reasons"])

        inferred = self._valid(metric_provenance={"x": "INF", "y": "DOC"})
        self.assertFalse(inferred["eligible_for_fit"])
        self.assertIn("METRIC_PROVENANCE_NOT_FIT_ELIGIBLE", inferred["rejection_reasons"])

    def test_schema_and_inventory_keep_authority_closed(self):
        self.assertTrue(SCHEMA.exists())
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["allowed_anchor_classes"]), ALLOWED_ANCHOR_CLASSES)
        self.assertEqual(
            {key: set(values) for key, values in schema["fit_eligible_metric_source_policy"].items()},
            FIT_ELIGIBLE_METRIC_SOURCE_POLICY,
        )
        self.assertTrue(schema["metric_validation_reference_required"])
        self.assertFalse(schema["authority"]["canonical_geometry_authorized"])
        self.assertFalse(schema["authority"]["structural_identity_authorized"])

        inventory = build_primary_anchor_inventory([self._valid()], SOURCE_SHA)
        self.assertEqual(
            inventory["authority"],
            {
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
                "m0g_authorized": False,
                "engineering_authority_effect": "NONE",
            },
        )


if __name__ == "__main__":
    unittest.main()
