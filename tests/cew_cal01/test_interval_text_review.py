import unittest

from experiments.cew_cal01.interval_text_review import (
    attach_text_proposal,
    build_interval_text_review_manifest,
)


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
}


def refined_fixture():
    def chain(chain_id, orientation, axis, tick_positions):
        return {
            "chain_id": chain_id,
            "orientation": orientation,
            "carrier_axis_px": axis,
            "carrier_start_px": tick_positions[0],
            "carrier_end_px": tick_positions[-1],
            "tick_positions_px": list(tick_positions),
            "intervals": [
                {
                    "interval_index": index,
                    "start_px": tick_positions[index],
                    "end_px": tick_positions[index + 1],
                    "member_observation_ids": [],
                }
                for index in range(len(tick_positions) - 1)
            ],
        }

    return {
        "schema": "CEW_CAL01_REFINED_EXTERNAL_DIMENSION_CHAIN_EXACT_v1",
        "program": "CEW-CAL-01",
        "source": {
            "source_id": "TAV-02S",
            "sha256": "c" * 64,
        },
        "side_order": ["TOP", "RIGHT", "BOTTOM", "LEFT"],
        "sides": [
            {
                "side": "TOP",
                "chains": [chain("TOP:R1", "HORIZONTAL", 555.0, [100, 200, 300, 400, 500, 600, 700])],
            },
            {
                "side": "RIGHT",
                "chains": [
                    chain("RIGHT:R1", "VERTICAL", 11000.0, [100, 200, 300, 400]),
                    chain("RIGHT:R2", "VERTICAL", 10900.0, [500, 600, 700]),
                ],
            },
            {
                "side": "BOTTOM",
                "chains": [chain("BOTTOM:R1", "HORIZONTAL", 6500.0, [100, 200, 300, 400, 500])],
            },
            {
                "side": "LEFT",
                "chains": [chain("LEFT:R1", "VERTICAL", 3900.0, [100, 200, 300, 400, 500])],
            },
        ],
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class IntervalTextReviewContractTests(unittest.TestCase):
    def test_manifest_creates_one_review_request_per_qualified_interval(self):
        manifest = build_interval_text_review_manifest(refined_fixture())
        self.assertEqual(manifest["review_request_count"], 19)
        self.assertEqual(
            [row["side"] for row in manifest["review_requests"]],
            ["TOP"] * 6 + ["RIGHT"] * 5 + ["BOTTOM"] * 4 + ["LEFT"] * 4,
        )
        self.assertEqual(len({row["review_id"] for row in manifest["review_requests"]}), 19)

    def test_crop_policy_is_side_aware_and_keeps_carrier_realign_separate_from_geometry(self):
        manifest = build_interval_text_review_manifest(refined_fixture())
        first_by_side = {}
        for row in manifest["review_requests"]:
            first_by_side.setdefault(row["side"], row)

        self.assertEqual(first_by_side["TOP"]["crop_policy"]["outward_normal"], "NEGATIVE_Y")
        self.assertEqual(first_by_side["BOTTOM"]["crop_policy"]["outward_normal"], "POSITIVE_Y")
        self.assertEqual(first_by_side["LEFT"]["crop_policy"]["outward_normal"], "NEGATIVE_X")
        self.assertEqual(first_by_side["RIGHT"]["crop_policy"]["outward_normal"], "POSITIVE_X")
        self.assertGreater(first_by_side["TOP"]["crop_policy"]["carrier_realign_radius_px"], 0)
        self.assertEqual(first_by_side["TOP"]["carrier_axis_px"], 555.0)
        self.assertEqual(first_by_side["TOP"]["recognition_status"], "HANDWRITTEN_RECOGNIZER_REQUIRED")

    def test_text_proposal_never_promotes_metric_or_canonical_authority(self):
        manifest = build_interval_text_review_manifest(refined_fixture())
        review_id = manifest["review_requests"][0]["review_id"]
        updated = attach_text_proposal(
            manifest,
            review_id=review_id,
            provider={"provider_id": "TEST_HANDWRITTEN", "model_id": "fixture-v1"},
            alternatives=[
                {"raw_text": "4,70", "confidence": 0.99},
                {"raw_text": "4.70", "confidence": 0.80},
            ],
        )
        row = next(item for item in updated["review_requests"] if item["review_id"] == review_id)
        self.assertEqual(row["recognition_status"], "OCR_PROPOSAL_ONLY")
        self.assertEqual([item["raw_text"] for item in row["text_proposals"]], ["4,70", "4.70"])
        self.assertFalse(row["primary_anchor_authorized"])
        self.assertFalse(row["eligible_for_metric_calibration"])
        self.assertFalse(updated["authority"]["canonical_geometry_authorized"])
        self.assertFalse(updated["authority"]["canonical_write_authorized"])

    def test_empty_or_unavailable_recognition_fails_closed(self):
        manifest = build_interval_text_review_manifest(refined_fixture())
        review_id = manifest["review_requests"][0]["review_id"]
        updated = attach_text_proposal(
            manifest,
            review_id=review_id,
            provider={"provider_id": "UNAVAILABLE", "model_id": "none"},
            alternatives=[],
        )
        row = next(item for item in updated["review_requests"] if item["review_id"] == review_id)
        self.assertEqual(row["recognition_status"], "MANUAL_OR_MULTIMODAL_REVIEW_REQUIRED")
        self.assertEqual(row["text_proposals"], [])
        self.assertEqual(updated["primary_anchor_count"], 0)
        self.assertFalse(updated["eligible_for_metric_calibration"])

    def test_manifest_is_deterministic_for_side_and_chain_input_order(self):
        source = refined_fixture()
        first = build_interval_text_review_manifest(source)
        source["sides"] = list(reversed(source["sides"]))
        for side in source["sides"]:
            side["chains"] = list(reversed(side["chains"]))
        second = build_interval_text_review_manifest(source)
        self.assertEqual(first["review_digest"], second["review_digest"])
        self.assertEqual(first["review_requests"], second["review_requests"])


if __name__ == "__main__":
    unittest.main()
