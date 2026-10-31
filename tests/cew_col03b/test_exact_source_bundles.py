from __future__ import annotations

from copy import deepcopy
import unittest

from experiments.cew_col03b.exact_source import build_exact_source_bundles


def _occurrence(index: int, *, x: float, y: float) -> dict:
    return {
        "occurrence_id": f"COL-OCC-{index:04d}",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_path": "archive/documentazione_originaria/tavola 5.pdf",
        "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_index": 0,
        "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        "primary_graphical_representation": {
            "kind": "FROZEN_PROPOSAL",
            "candidate_id": f"COL02-FP-{index:04d}",
            "repair_id": None,
            "bbox": {"x": x, "y": y, "width": 0.05, "height": 0.05},
        },
        "source_proposal_ids": [f"COL02-FP-{index:04d}"],
        "dedup_state": "SINGLE_GOVERNED_LINEAGE",
        "conflict_state": "NONE",
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "documentary_label_state": "NOT_EVALUATED",
        "structural_identity_state": "NOT_EVALUATED",
        "canonical_geometry_state": "NOT_AUTHORIZED",
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_promotion_authorized": False,
    }


def _ledger() -> dict:
    occurrences = []
    for index in range(1, 23):
        column = (index - 1) % 6
        row = (index - 1) // 6
        occurrences.append(_occurrence(index, x=0.08 + column * 0.14, y=0.10 + row * 0.20))
    return {"occurrence_count": 22, "occurrences": occurrences}


class ExactSourceBundleTests(unittest.TestCase):
    def test_internal_ocr_creates_documentary_label_hypothesis_without_promotion(self) -> None:
        ledger = _ledger()
        first_bbox = ledger["occurrences"][0]["primary_graphical_representation"]["bbox"]
        text = {
            "token_id": "TXT-001",
            "raw_text": "12",
            "normalized_text": "12",
            "confidence": 91.0,
            "bbox": {
                "x": first_bbox["x"] + 0.01,
                "y": first_bbox["y"] + 0.01,
                "width": 0.01,
                "height": 0.01,
            },
        }
        bundles = build_exact_source_bundles(
            ledger=ledger,
            text_observations=[text],
            raster_sha256="r" * 64,
            raster_width_px=4000,
            raster_height_px=3000,
        )
        first = bundles[0]
        self.assertEqual(len(first["internal_text_evidence"]), 1)
        self.assertEqual(first["internal_text_evidence"][0]["raw_text"], "12")
        self.assertEqual(len(first["hypotheses"]), 1)
        hypothesis = first["hypotheses"][0]
        self.assertEqual(hypothesis["hypothesis_kind"], "DOCUMENTARY_LABEL_CANDIDATE")
        self.assertEqual(hypothesis["candidate_value"], "12")
        self.assertEqual(hypothesis["state"], "SINGLE_CHANNEL")
        self.assertFalse(hypothesis["promotion_authorized"])
        self.assertFalse(first["support_identity_authorized"])
        self.assertFalse(first["canonical_write_authorized"])

    def test_nearby_text_remains_proximity_evidence_and_does_not_create_identity_hypothesis(self) -> None:
        ledger = _ledger()
        first_bbox = ledger["occurrences"][0]["primary_graphical_representation"]["bbox"]
        text = {
            "token_id": "TXT-002",
            "raw_text": "370",
            "normalized_text": "370",
            "confidence": 88.0,
            "bbox": {
                "x": first_bbox["x"] + first_bbox["width"] + 0.01,
                "y": first_bbox["y"] + 0.01,
                "width": 0.015,
                "height": 0.01,
            },
        }
        bundles = build_exact_source_bundles(
            ledger=ledger,
            text_observations=[text],
            raster_sha256="r" * 64,
            raster_width_px=4000,
            raster_height_px=3000,
        )
        first = bundles[0]
        self.assertEqual(len(first["nearby_text_evidence"]), 1)
        self.assertEqual(first["nearby_text_evidence"][0]["evidence_class"], "PROXIMITY_ONLY")
        self.assertEqual(first["hypotheses"], [])

    def test_every_occurrence_has_all_channels_explicitly_evaluated(self) -> None:
        bundles = build_exact_source_bundles(
            ledger=_ledger(),
            text_observations=[],
            raster_sha256="r" * 64,
            raster_width_px=4000,
            raster_height_px=3000,
        )
        self.assertEqual(len(bundles), 22)
        for bundle in bundles:
            self.assertEqual(bundle["documentary_evidence_state"], "COMPLETE")
            self.assertEqual(bundle["missing_channels"], [])
            self.assertEqual(len(bundle["high_resolution_read_evidence"]), 1)
            self.assertEqual(len(bundle["local_topology_evidence"]), 1)
            self.assertEqual(bundle["callout_evidence"][0]["status"], "NO_EVIDENCE")
            self.assertEqual(bundle["cross_document_evidence"][0]["status"], "NO_EVIDENCE")

    def test_text_input_order_does_not_change_bundle_payloads(self) -> None:
        ledger = _ledger()
        first_bbox = ledger["occurrences"][0]["primary_graphical_representation"]["bbox"]
        observations = [
            {
                "token_id": "TXT-002",
                "raw_text": "B",
                "normalized_text": "B",
                "confidence": 80.0,
                "bbox": {"x": first_bbox["x"] + 0.02, "y": first_bbox["y"] + 0.02, "width": 0.01, "height": 0.01},
            },
            {
                "token_id": "TXT-001",
                "raw_text": "A",
                "normalized_text": "A",
                "confidence": 81.0,
                "bbox": {"x": first_bbox["x"] + 0.01, "y": first_bbox["y"] + 0.01, "width": 0.01, "height": 0.01},
            },
        ]
        first = build_exact_source_bundles(
            ledger=deepcopy(ledger), text_observations=observations, raster_sha256="r" * 64, raster_width_px=4000, raster_height_px=3000
        )
        second = build_exact_source_bundles(
            ledger=deepcopy(ledger), text_observations=list(reversed(observations)), raster_sha256="r" * 64, raster_width_px=4000, raster_height_px=3000
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
