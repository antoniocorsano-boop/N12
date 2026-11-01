import unittest

from experiments.cew_cal01.anchor_inventory import (
    FIT_ELIGIBLE_METRIC_SOURCE_POLICY,
    make_anchor_candidate,
)


SOURCE_SHA = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"


class Cal01MetricValidationGateTests(unittest.TestCase):
    def _candidate(self, **overrides):
        kwargs = {
            "anchor_class": "DIMENSION_CHAIN_ENDPOINT",
            "source_version_sha256": SOURCE_SHA,
            "source_page": 0,
            "source_point_px": [1200.0, 2200.0],
            "metric_xy_m": [4.70, 9.80],
            "metric_provenance": {"x": "DOC", "y": "DOC"},
            "evidence_refs": ["TAV5:dimension-chain:reviewed"],
            "metric_source_kind": "PRIMARY_TAV5_DOCUMENTED_RELATION",
            "source_layer": "ORIGINAL_DRAWING",
            "metric_validation_state": "PRIMARY_VISUAL_VALIDATED",
            "metric_validation_ref": "CEW-CAL01-PRIMARY-REVIEW:receipt-001",
        }
        kwargs.update(overrides)
        return make_anchor_candidate(**kwargs)

    def test_fit_eligible_metric_source_policy_is_positive_and_bounded(self):
        self.assertEqual(
            FIT_ELIGIBLE_METRIC_SOURCE_POLICY,
            {
                "PRIMARY_TAV5_DOCUMENTED_RELATION": {"PRIMARY_VISUAL_VALIDATED"},
                "PRIMARY_TAV5_SOURCE_NATIVE_METRIC": {"SOURCE_NATIVE_VERIFIED"},
                "PRIMARY_MEASURED_CONTROL": {"MEASURED_CONTROL_VALIDATED"},
            },
        )

    def test_documented_relation_requires_primary_visual_validation_receipt(self):
        valid = self._candidate()
        self.assertTrue(valid["eligible_for_fit"])
        self.assertEqual(valid["metric_validation_state"], "PRIMARY_VISUAL_VALIDATED")
        self.assertEqual(valid["metric_validation_ref"], "CEW-CAL01-PRIMARY-REVIEW:receipt-001")

        missing_state = self._candidate(metric_validation_state=None)
        self.assertFalse(missing_state["eligible_for_fit"])
        self.assertIn("METRIC_VALIDATION_STATE_NOT_ELIGIBLE", missing_state["rejection_reasons"])

        missing_ref = self._candidate(metric_validation_ref=None)
        self.assertFalse(missing_ref["eligible_for_fit"])
        self.assertIn("METRIC_VALIDATION_REFERENCE_MISSING", missing_ref["rejection_reasons"])

    def test_ocr_consensus_cannot_become_fit_eligible_by_claiming_doc_provenance(self):
        row = self._candidate(
            metric_source_kind="OCR_CONSENSUS_ONLY",
            metric_validation_state="PRIMARY_VISUAL_VALIDATED",
            metric_validation_ref="CEW-CAL01-PRIMARY-REVIEW:receipt-001",
        )
        self.assertFalse(row["eligible_for_fit"])
        self.assertIn("METRIC_SOURCE_KIND_NOT_FIT_ELIGIBLE", row["rejection_reasons"])

    def test_wrong_validation_state_for_source_kind_fails_closed(self):
        row = self._candidate(
            metric_source_kind="PRIMARY_TAV5_DOCUMENTED_RELATION",
            metric_validation_state="SOURCE_NATIVE_VERIFIED",
            metric_validation_ref="CEW-CAL01-SOURCE-BINDING:001",
        )
        self.assertFalse(row["eligible_for_fit"])
        self.assertIn("METRIC_VALIDATION_STATE_NOT_ELIGIBLE", row["rejection_reasons"])

    def test_source_native_and_measured_controls_have_distinct_validation_states(self):
        native = self._candidate(
            anchor_class="SOURCE_NATIVE_METRIC_POINT",
            metric_source_kind="PRIMARY_TAV5_SOURCE_NATIVE_METRIC",
            metric_validation_state="SOURCE_NATIVE_VERIFIED",
            metric_validation_ref="CEW-CAL01-SOURCE-BINDING:001",
        )
        self.assertTrue(native["eligible_for_fit"])

        measured = self._candidate(
            metric_source_kind="PRIMARY_MEASURED_CONTROL",
            metric_provenance={"x": "MIS", "y": "MIS"},
            metric_validation_state="MEASURED_CONTROL_VALIDATED",
            metric_validation_ref="CEW-CAL01-MEASUREMENT:001",
        )
        self.assertTrue(measured["eligible_for_fit"])


if __name__ == "__main__":
    unittest.main()
