from pathlib import Path
import json
import unittest


ROOT = Path("governance/cew-cal01/reviews")
SOURCE_SHA = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
ARTIFACT_DIGEST = "sha256:803fa42b04d91bbdc8b8cc89575ca6fe6caae1160026021908dba307d837cf14"
EXPECTED = {
    "T02_TOP_I0": {
        "review_id": "TAV-02S:TOP:TOP:R1:I0",
        "crop_sha256": "sha256:b1e0bcb76052f38e4f575425e24eff62471f084c7e5017d4634df81fb8ec5be6",
        "value_m": 4.70,
    },
    "T02_TOP_I1": {
        "review_id": "TAV-02S:TOP:TOP:R1:I1",
        "crop_sha256": "sha256:bbf26f511105d12b6f5628be8ef41497e1fb1d990c41dcd5b2eef500c1d9077d",
        "value_m": 5.10,
    },
    "T02_TOP_I2": {
        "review_id": "TAV-02S:TOP:TOP:R1:I2",
        "crop_sha256": "sha256:239965ca84eecaffb5ea1e3d64de413fbae8a1f6acfae19b14b90953613daa83",
        "value_m": 4.15,
    },
    "T02_TOP_I3": {
        "review_id": "TAV-02S:TOP:TOP:R1:I3",
        "crop_sha256": "sha256:ba20508dede075885c3119c6d1587b95b46312351c2ff6650b4cbdd110e1584c",
        "value_m": 4.15,
    },
    "T02_TOP_I4": {
        "review_id": "TAV-02S:TOP:TOP:R1:I4",
        "crop_sha256": "sha256:53bf76ba55df3e967aeaba3fc8a6fa662dfea2ea25605bcd63e94313660b84b2",
        "value_m": 5.30,
    },
    "T02_TOP_I5": {
        "review_id": "TAV-02S:TOP:TOP:R1:I5",
        "crop_sha256": "sha256:12f4d75da50352dd47ba1a93070356ecc843092f26822917947f67c37b152695",
        "value_m": 4.70,
    },
    "T02_RIGHT_I0": {
        "review_id": "TAV-02S:RIGHT:RIGHT:R1:I0",
        "crop_sha256": "sha256:7c3e42250196f7cd4e754dcc4b67eb6935a715b9629f1495a2a84acacf77067c",
        "value_m": 2.10,
    },
    "T02_RIGHT_I1": {
        "review_id": "TAV-02S:RIGHT:RIGHT:R1:I1",
        "crop_sha256": "sha256:ca6f7871bcc800ed263aff6672dad7cf0aeba96a473485e6878c5fd315b6aad6",
        "value_m": 3.45,
    },
}


class ExternalChainHumanDecisionReceiptTests(unittest.TestCase):
    def test_tav02_human_decisions_are_exact_crop_bound_and_relation_only(self):
        for suffix, expected in EXPECTED.items():
            path = ROOT / f"CEW_CAL01_EXTERNAL_CHAIN_HUMAN_{suffix}_v1.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "CEW_CAL01_EXTERNAL_CHAIN_HUMAN_DECISION_v1")
            self.assertEqual(payload["program"], "CEW-CAL-01")
            self.assertEqual(payload["reviewer_role"], "HUMAN_PROFESSIONAL_USER")
            self.assertEqual(payload["source_document"], "TAV-02S")
            self.assertEqual(payload["source_sha256"], SOURCE_SHA)
            self.assertEqual(payload["interval_review_id"], expected["review_id"])
            self.assertEqual(payload["crop_sha256"], expected["crop_sha256"])
            self.assertEqual(payload["decision"], "DOCUMENTED_LINEAR_DIMENSION")
            self.assertAlmostEqual(payload["value"]["length_m"], expected["value_m"])
            self.assertEqual(payload["calibration_role"], "LINEAR_DIMENSION")
            self.assertEqual(payload["metric_relation_state"], "PRIMARY_VISUAL_VALIDATED")
            self.assertTrue(payload["eligible_for_metric_relation_network"])
            self.assertFalse(payload["eligible_for_metric_calibration"])
            self.assertFalse(payload["primary_anchor_authorized"])
            self.assertEqual(payload["qualified_interval_basis"]["artifact_digest"], ARTIFACT_DIGEST)
            self.assertFalse(payload["authority"]["structural_identity_authorized"])
            self.assertFalse(payload["authority"]["canonical_geometry_authorized"])
            self.assertFalse(payload["authority"]["canonical_write_authorized"])
            self.assertFalse(payload["authority"]["m0g_authorized"])
            self.assertEqual(payload["authority"]["engineering_authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
