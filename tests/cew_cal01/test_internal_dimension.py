import unittest
from pathlib import Path

try:
    from experiments.cew_cal01.internal_dimension import (
        build_internal_dimension_discovery,
        build_internal_manifest,
        classify_internal_role_result,
        select_internal_search_roi,
    )
except (ImportError, ModuleNotFoundError):
    build_internal_dimension_discovery = None
    build_internal_manifest = None
    classify_internal_role_result = None
    select_internal_search_roi = None


SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"


def perimeter_payload(*, candidate_count=0, status="PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED"):
    return {
        "source": {"sha256": SOURCE_SHA256},
        "perimeter_discovery_digest": "sha256:perimeter-test",
        "candidate_count": candidate_count,
        "status": status,
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "structural_plan_envelope": {
            "envelope_bbox_source_px": [347.0, 3759.0, 6384.0, 11061.0]
        },
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }


class Cal01InternalDimensionContractTests(unittest.TestCase):
    def test_contract_functions_exist(self):
        self.assertTrue(callable(select_internal_search_roi))
        self.assertTrue(callable(classify_internal_role_result))
        self.assertTrue(callable(build_internal_manifest))
        self.assertTrue(callable(build_internal_dimension_discovery))

    def test_internal_roi_uses_qualified_perimeter_source_envelope(self):
        self.assertEqual(
            select_internal_search_roi(perimeter_payload()),
            [347, 3759, 6384, 11061],
        )

    def test_perimeter_candidates_defer_internal_search(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "CAL01_INTERNAL_SEARCH_DEFERRED_PERIMETER_CANDIDATES_PRESENT",
        ):
            select_internal_search_roi(
                perimeter_payload(
                    candidate_count=1,
                    status="PERIMETER_DIMENSION_CHAINS_OBSERVED",
                )
            )

    def test_only_linear_dimension_role_becomes_internal_candidate(self):
        cluster = {
            "cluster_index": 7,
            "representative": {
                "raw_ocr_text": "470",
                "bbox_px": [100.0, 200.0, 150.0, 225.0],
            },
        }
        role_result = {
            "role": "LINEAR_DIMENSION",
            "documented_text": "470",
            "reason": "CONSENSUS_AND_DIMENSION_TICK_GRAMMAR_CONFIRMED",
            "dimension_relation": {
                "confirmed": True,
                "orientation": "HORIZONTAL",
                "endpoint_a_px": [80.0, 240.0],
                "endpoint_b_px": [520.0, 240.0],
            },
        }
        result = classify_internal_role_result(cluster, role_result)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["candidate"]["semantic_role"], "INTERNAL_LINEAR_DIMENSION_CANDIDATE")
        self.assertTrue(result["candidate"]["primary_visual_validation_required"])
        self.assertFalse(result["candidate"]["fit_eligible"])
        self.assertFalse(result["candidate"]["metric_anchor_promoted"])

    def test_section_measure_is_rejected_from_internal_candidate_set(self):
        cluster = {"cluster_index": 3, "representative": {"raw_ocr_text": "120"}}
        role_result = {
            "role": "SECTION_MEASURE",
            "documented_text": "120",
            "reason": "CONSENSUS_NEAR_CLOSED_FRAME_WITHOUT_DIMENSION_TICK_GRAMMAR",
            "dimension_relation": None,
        }
        result = classify_internal_role_result(cluster, role_result)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["rejected"]["role"], "SECTION_MEASURE")
        self.assertEqual(result["rejected"]["cluster_index"], 3)

    def test_manifest_is_order_independent_and_keeps_authority_closed(self):
        candidates = [
            {
                "candidate_id": "CEW-CAL01-INTDIM-B",
                "cluster_index": 5,
                "semantic_role": "INTERNAL_LINEAR_DIMENSION_CANDIDATE",
            },
            {
                "candidate_id": "CEW-CAL01-INTDIM-A",
                "cluster_index": 2,
                "semantic_role": "INTERNAL_LINEAR_DIMENSION_CANDIDATE",
            },
        ]
        rejected = [
            {"cluster_index": 7, "role": "UNRESOLVED"},
            {"cluster_index": 3, "role": "SECTION_MEASURE"},
        ]
        kwargs = {
            "source": {"sha256": SOURCE_SHA256},
            "perimeter": perimeter_payload(),
            "search_roi_px": [347, 3759, 6384, 11061],
            "location_clusters": [{"cluster_index": 0}, {"cluster_index": 1}],
            "ocr_pass_count": 12,
        }
        first = build_internal_manifest(candidates=candidates, rejected=rejected, **kwargs)
        second = build_internal_manifest(
            candidates=list(reversed(candidates)),
            rejected=list(reversed(rejected)),
            **kwargs,
        )
        self.assertEqual(first["internal_discovery_digest"], second["internal_discovery_digest"])
        self.assertEqual(first["candidate_count"], 2)
        self.assertEqual(first["rejected_location_count"], 2)
        self.assertEqual(first["primary_anchor_count"], 0)
        self.assertEqual(first["status"], "INTERNAL_LINEAR_DIMENSION_CANDIDATES_OBSERVED")
        self.assertFalse(first["historical_comparator_loaded"])
        self.assertFalse(first["historical_affine_loaded"])
        self.assertFalse(first["tav02s_evidence_loaded"])
        self.assertFalse(first["authority"]["canonical_geometry_authorized"])
        self.assertFalse(first["authority"]["canonical_write_authorized"])

    def test_workflow_runs_and_asserts_internal_exact_source_stage(self):
        workflow = Path(".github/workflows/validate-cew-cal01.yml").read_text(encoding="utf-8")
        self.assertIn("python -m experiments.cew_cal01.internal_dimension", workflow)
        self.assertIn("--perimeter-discovery", workflow)
        self.assertIn("perimeter/perimeter-dimension-discovery.json", workflow)
        self.assertIn("--output-dir \"$RUNNER_TEMP/cew-cal01-dimension-discovery/internal\"", workflow)
        self.assertIn("internal/internal-dimension-discovery.json", workflow)
        self.assertIn("assert internal['source']['sha256'] == expected_sha", workflow)
        self.assertIn("assert internal['primary_anchor_count'] == 0", workflow)
        self.assertIn("assert internal['perimeter_trigger']['candidate_count'] == 0", workflow)
        self.assertIn("INTERNAL_LINEAR_DIMENSION_CANDIDATES_OBSERVED", workflow)
        self.assertIn("INTERNAL_DIMENSION_CHAINS_NOT_OBSERVED", workflow)


if __name__ == "__main__":
    unittest.main()
