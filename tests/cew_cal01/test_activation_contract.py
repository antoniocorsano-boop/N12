import json
import unittest
from pathlib import Path


ACTIVATION = Path("governance/cew-cal01/CEW_CAL01_ACTIVATION_v1.json")


class Cal01ActivationContractTests(unittest.TestCase):
    def test_cal01_activation_freezes_qualified_predecessor_and_keeps_authority_closed(self):
        self.assertTrue(ACTIVATION.exists(), "CEW_CAL01_ACTIVATION_v1.json must exist")
        payload = json.loads(ACTIVATION.read_text(encoding="utf-8"))

        self.assertEqual(payload["program"], "CEW-CAL-01")
        self.assertEqual(payload["state"], "ACTIVE_SUCCESSOR")
        self.assertEqual(
            payload["predecessor"]["exact_sha"],
            "ee23c221118064022fa77b694ff88119530cc454",
        )
        self.assertEqual(payload["predecessor"]["workflow_run_id"], 41317800420)
        self.assertEqual(
            payload["predecessor"]["jobs"],
            {
                "adapter-contracts": "PASS",
                "dxf-documentary-exact-source": "PASS",
                "structural-candidate-exact-source": "PASS",
            },
        )

        metric = payload["diagnostic_metric_baseline"]
        self.assertEqual(metric["artifact_id"], 13088253052)
        self.assertEqual(
            metric["artifact_digest"],
            "sha256:c0ffc5ed72db1bc26db242f27b1f7bea5fbecb9977681ec6b61e2d32bf107974",
        )
        self.assertEqual(metric["comparison_count"], 22)
        self.assertEqual(metric["min_distance_m"], 0.2107452723974942)
        self.assertEqual(metric["median_distance_m"], 1.9936776850705247)
        self.assertEqual(metric["max_distance_m"], 2.663704443235022)
        self.assertEqual(metric["unique_nearest_historical_node_count"], 19)
        self.assertEqual(metric["semantics"], "DISTANCE_AUDIT_ONLY_NO_BINDING_NO_THRESHOLD")
        self.assertFalse(metric["may_be_used_for_calibration"])

        self.assertEqual(
            payload["authority"],
            {
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
                "m0g_authorized": False,
                "historical_support_identity_authorized": False,
                "engineering_authority_effect": "NONE",
            },
        )
        self.assertEqual(payload["next_required_action"], "BUILD_PRIMARY_METRIC_CALIBRATION")


if __name__ == "__main__":
    unittest.main()
