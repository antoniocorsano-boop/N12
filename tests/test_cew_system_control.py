import unittest
from copy import deepcopy

from scripts import cew_system_control as ctrl


class CEWSystemCompletenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = ctrl.load(ctrl.MATRIX_PATH)
        cls.queue = ctrl.load(ctrl.QUEUE_PATH)
        cls.state = ctrl.load(ctrl.STATE_PATH)
        cls.registry = ctrl.load(ctrl.REGISTRY_PATH)

    def test_repository_has_complete_w0_w8_control_plane(self):
        ok, errors = ctrl.validate(self.matrix, self.queue, self.state, self.registry)
        self.assertTrue(ok, errors)
        self.assertEqual(set(self.matrix["workstreams"]), {f"W{i}" for i in range(9)})

    def test_investigation_dossier_and_3d_workspace_are_owned(self):
        owners = ctrl.capability_owners(self.queue)
        self.assertIn("INV-001", owners["investigation.voi"])
        self.assertIn("DOS-001", owners["dossier.lifecycle"])
        self.assertIn("WS3D-001", owners["model.ifc_projection"])

    def test_control_plane_preserves_non_promotive_boundary(self):
        health = ctrl.health(self.matrix, self.queue, self.state, self.registry)
        self.assertEqual(health["canonical_boundary"]["canonical_promotion"], "DISABLED")
        self.assertEqual(self.queue["status"], "EXPERIMENTAL_NON_PROMOTIVE")

    def test_missing_workstream_fails_closed(self):
        matrix = deepcopy(self.matrix)
        matrix["workstreams"].pop("W8")
        ok, errors = ctrl.validate(matrix, self.queue, self.state, self.registry)
        self.assertFalse(ok)
        self.assertTrue(any("workstream coverage mismatch" in error for error in errors))

    def test_unowned_domain_capability_fails_closed(self):
        registry = deepcopy(self.registry)
        registry["capabilities"]["future.domain"] = {
            "class": "CEW_DOMAIN_CAPABILITY",
            "providers": ["future-provider"],
            "required_invariants": ["explicit"],
        }
        ok, errors = ctrl.validate(self.matrix, self.queue, self.state, registry)
        self.assertFalse(ok)
        self.assertIn("unowned CEW_DOMAIN_CAPABILITY capability: future.domain", errors)

    def test_real_blocker_is_health_signal_not_fake_failure(self):
        health = ctrl.health(self.matrix, self.queue, self.state, self.registry)
        self.assertEqual(health["status"], "PASS")
        self.assertEqual(
            health["workstreams"]["W4"]["blockers"]["FEM-001"],
            "BLOCKED_EVIDENCE",
        )
        self.assertEqual(health["workstreams"]["W2"]["work_items"]["MOD-001"], "READY")


if __name__ == "__main__":
    unittest.main()
