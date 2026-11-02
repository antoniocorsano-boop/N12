import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from experiments.cew_cal01.interval_ocr_compare import build_interval_ocr_comparison
from experiments.cew_cal01.interval_ocr_exact import LOCAL_OCR_FAMILIES, run_local_interval_ocr


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "historical_support_identity_authorized": False,
}


def _manifest():
    return {
        "schema": "CEW_CAL01_INTERVAL_TEXT_REVIEW_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-02S", "sha256": "a" * 64},
        "review_request_count": 2,
        "review_requests": [
            {
                "review_id": "TAV-02S:TOP:C1:I0",
                "crop_file": "review-crops/i0.png",
                "crop_sha256": "sha256:" + "1" * 64,
                "recognition_status": "HANDWRITTEN_RECOGNIZER_REQUIRED",
                "primary_anchor_authorized": False,
                "eligible_for_metric_calibration": False,
            },
            {
                "review_id": "TAV-02S:TOP:C1:I1",
                "crop_file": "review-crops/i1.png",
                "crop_sha256": "sha256:" + "2" * 64,
                "recognition_status": "HANDWRITTEN_RECOGNIZER_REQUIRED",
                "primary_anchor_authorized": False,
                "eligible_for_metric_calibration": False,
            },
        ],
        "recognizer_binding_status": "HANDWRITTEN_RECOGNIZER_NOT_BOUND",
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "review_digest": "sha256:" + "f" * 64,
    }


def _obs(review_id, crop_sha256, family_id, raw_text, confidence=0.8, provider_id="TESSERACT"):
    return {
        "review_id": review_id,
        "crop_sha256": crop_sha256,
        "family_id": family_id,
        "provider_id": provider_id,
        "model_id": "tesseract-system" if provider_id == "TESSERACT" else "trocr-candidate",
        "raw_text": raw_text,
        "confidence": confidence,
    }


def _write_review_dir(root: Path) -> tuple[Path, list[bytes]]:
    review_dir = root / "review"
    crop_dir = review_dir / "review-crops"
    crop_dir.mkdir(parents=True)
    payloads = [b"synthetic-crop-zero", b"synthetic-crop-one"]
    requests = []
    for index, payload in enumerate(payloads):
        path = crop_dir / f"i{index}.png"
        path.write_bytes(payload)
        requests.append(
            {
                "review_id": f"TAV-02S:TOP:C1:I{index}",
                "crop_file": f"review-crops/i{index}.png",
                "crop_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
                "recognition_status": "HANDWRITTEN_RECOGNIZER_REQUIRED",
                "primary_anchor_authorized": False,
                "eligible_for_metric_calibration": False,
            }
        )
    manifest = {
        "schema": "CEW_CAL01_INTERVAL_TEXT_REVIEW_v1",
        "program": "CEW-CAL-01",
        "source": {"source_id": "TAV-02S", "sha256": "a" * 64},
        "review_request_count": 2,
        "review_requests": requests,
        "recognizer_binding_status": "HANDWRITTEN_RECOGNIZER_NOT_BOUND",
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
        "review_digest": "sha256:" + "f" * 64,
    }
    (review_dir / "interval-text-review-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return review_dir, payloads


class IntervalOcrComparisonContractTests(unittest.TestCase):
    def test_crop_digest_mismatch_fails_closed(self):
        manifest = _manifest()
        with self.assertRaisesRegex(ValueError, "CAL01_INTERVAL_OCR_CROP_DIGEST_MISMATCH"):
            build_interval_ocr_comparison(
                manifest,
                [_obs("TAV-02S:TOP:C1:I0", "sha256:" + "9" * 64, "GRAY_PSM7", "470")],
            )

    def test_same_family_duplicates_cannot_manufacture_agreement(self):
        manifest = _manifest()
        crop = manifest["review_requests"][0]["crop_sha256"]
        result = build_interval_ocr_comparison(
            manifest,
            [
                _obs("TAV-02S:TOP:C1:I0", crop, "GRAY_PSM7", "470", 0.82),
                _obs("TAV-02S:TOP:C1:I0", crop, "GRAY_PSM7", "4.70", 0.91),
            ],
        )
        row = result["reviews"][0]
        self.assertEqual(row["comparison_status"], "OCR_COMPARATIVE_INSUFFICIENT")
        self.assertEqual(row["distinct_family_count"], 1)
        self.assertIsNone(row["consensus_normalized_text"])

    def test_two_distinct_families_can_form_diagnostic_agreement_only(self):
        manifest = _manifest()
        crop = manifest["review_requests"][0]["crop_sha256"]
        result = build_interval_ocr_comparison(
            manifest,
            [
                _obs("TAV-02S:TOP:C1:I0", crop, "GRAY_PSM7", "470", 0.72),
                _obs("TAV-02S:TOP:C1:I0", crop, "LINE_SUPPRESSED_PSM7", "4.70", 0.87),
            ],
        )
        row = result["reviews"][0]
        self.assertEqual(row["comparison_status"], "OCR_COMPARATIVE_AGREEMENT")
        self.assertEqual(row["consensus_normalized_text"], "4.70")
        self.assertTrue(row["human_review_required"])
        self.assertFalse(row["primary_anchor_authorized"])
        self.assertFalse(row["eligible_for_metric_calibration"])

    def test_distinct_valid_readings_remain_conflict(self):
        manifest = _manifest()
        crop = manifest["review_requests"][0]["crop_sha256"]
        result = build_interval_ocr_comparison(
            manifest,
            [
                _obs("TAV-02S:TOP:C1:I0", crop, "GRAY_PSM7", "470"),
                _obs("TAV-02S:TOP:C1:I0", crop, "ENLARGED_PSM13", "405"),
            ],
        )
        row = result["reviews"][0]
        self.assertEqual(row["comparison_status"], "OCR_COMPARATIVE_CONFLICT")
        self.assertEqual(row["normalized_texts"], ["4.05", "4.70"])
        self.assertIsNone(row["consensus_normalized_text"])

    def test_invalid_text_yields_no_proposal_and_authority_stays_closed(self):
        manifest = _manifest()
        crop = manifest["review_requests"][0]["crop_sha256"]
        result = build_interval_ocr_comparison(
            manifest,
            [_obs("TAV-02S:TOP:C1:I0", crop, "GRAY_PSM7", "beam")],
        )
        first = result["reviews"][0]
        second = result["reviews"][1]
        self.assertEqual(first["comparison_status"], "OCR_NO_PROPOSAL")
        self.assertEqual(second["comparison_status"], "OCR_NO_PROPOSAL")
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["eligible_for_metric_calibration"])
        self.assertEqual(result["authority"], AUTHORITY_CLOSED)
        self.assertTrue(all(row["human_review_required"] for row in result["reviews"]))

    def test_digest_and_rows_are_independent_of_observation_input_order(self):
        manifest = _manifest()
        crop = manifest["review_requests"][0]["crop_sha256"]
        observations = [
            _obs("TAV-02S:TOP:C1:I0", crop, "GRAY_PSM7", "470", 0.72),
            _obs("TAV-02S:TOP:C1:I0", crop, "LINE_SUPPRESSED_PSM7", "4.70", 0.87),
        ]
        forward = build_interval_ocr_comparison(manifest, observations)
        reverse = build_interval_ocr_comparison(manifest, list(reversed(observations)))
        self.assertEqual(forward["comparison_digest"], reverse["comparison_digest"])
        self.assertEqual(forward["reviews"], reverse["reviews"])


class IntervalOcrExactContractTests(unittest.TestCase):
    def test_local_family_contract_is_fixed_and_numeric_only(self):
        self.assertEqual(
            [row["family_id"] for row in LOCAL_OCR_FAMILIES],
            ["GRAY_PSM7", "LINE_SUPPRESSED_PSM7", "ENLARGED_PSM13"],
        )
        self.assertEqual([row["psm"] for row in LOCAL_OCR_FAMILIES], [7, 7, 13])
        self.assertEqual(
            [row["preprocess"] for row in LOCAL_OCR_FAMILIES],
            ["NORMALIZED_GRAY", "THRESHOLD_LINE_SUPPRESSED", "ENLARGED_THRESHOLD"],
        )
        self.assertTrue(all(row["whitelist"] == "0123456789.," for row in LOCAL_OCR_FAMILIES))

    def test_exact_runner_invokes_three_families_per_crop_and_writes_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            review_dir, _ = _write_review_dir(Path(temp))
            calls = []

            def fake_runner(crop_path, family):
                calls.append((crop_path.name, family["family_id"], family["psm"], family["whitelist"]))
                raw = "470" if family["family_id"] != "ENLARGED_PSM13" else "4.70"
                return {
                    "raw_text": raw,
                    "confidence": 0.85,
                    "provider_version": "tesseract-test",
                }

            result = run_local_interval_ocr(review_dir, ocr_runner=fake_runner)
            self.assertEqual(len(calls), 6)
            self.assertEqual(
                calls[:3],
                [
                    ("i0.png", "GRAY_PSM7", 7, "0123456789.,"),
                    ("i0.png", "LINE_SUPPRESSED_PSM7", 7, "0123456789.,"),
                    ("i0.png", "ENLARGED_PSM13", 13, "0123456789.,"),
                ],
            )
            self.assertEqual(result["review_count"], 2)
            self.assertTrue((review_dir / "interval-ocr-comparison.json").is_file())
            self.assertTrue(all(row["comparison_status"] == "OCR_COMPARATIVE_AGREEMENT" for row in result["reviews"]))
            self.assertTrue(all(row["human_review_required"] for row in result["reviews"]))
            self.assertEqual(result["primary_anchor_count"], 0)
            self.assertFalse(result["eligible_for_metric_calibration"])

    def test_exact_runner_rejects_crop_bytes_that_do_not_match_manifest_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            review_dir, _ = _write_review_dir(Path(temp))
            (review_dir / "review-crops" / "i0.png").write_bytes(b"mutated")

            with self.assertRaisesRegex(ValueError, "CAL01_INTERVAL_OCR_CROP_FILE_DIGEST_MISMATCH"):
                run_local_interval_ocr(
                    review_dir,
                    ocr_runner=lambda crop_path, family: {
                        "raw_text": "470",
                        "confidence": 0.8,
                        "provider_version": "tesseract-test",
                    },
                )


if __name__ == "__main__":
    unittest.main()
