import unittest

try:
    from experiments.cew_cal01.internal_dimension import (
        classify_internal_role_result,
        select_internal_search_roi,
    )
except (ImportError, ModuleNotFoundError):
    classify_internal_role_result = None
    select_internal_search_roi = None


SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"


def perimeter_payload(*, candidate_count=0, status="PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED"):
    return {
        "source": {"sha256": SOURCE_SHA256},
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


if __name__ == "__main__":
    unittest.main()
