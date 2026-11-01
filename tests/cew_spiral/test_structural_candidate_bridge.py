from __future__ import annotations

import unittest

from cew_b01.records import SourceIdentity
from cew_spiral.structural_candidate_bridge import build_structural_candidate_bridge


SOURCE = SourceIdentity(
    repository="antoniocorsano-boop/N12",
    commit="78c20a52db4f391ce0d13b9705b9f04737e218c9",
    path="archive/documentazione_originaria/tavola 5.pdf",
    git_blob_sha="ec32cd621877e9037cb26ebc083164140a8e3e68",
    sha256="2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    page_index=0,
)


def occurrence(
    occurrence_id: str,
    *,
    bbox: dict[str, float],
    decisions: list[str] | None = None,
    receipts: list[str] | None = None,
) -> dict:
    return {
        "occurrence_id": occurrence_id,
        "candidate_id": f"COL02-FP-{occurrence_id[-4:]}",
        "source_proposal_ids": [f"COL02-FP-{occurrence_id[-4:]}"],
        "evidence_ids": [f"EVIDENCE:{occurrence_id}"],
        "graphical_decisions": decisions or ["COLUMN_FOOTPRINT_CONFIRMED"],
        "human_review_receipts": receipts or ["governance/cew-col02/review.json"],
        "normalized_bbox": bbox,
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_path": SOURCE.path,
        "source_sha256": SOURCE.sha256,
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_index": 0,
        "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "conflict_state": "NONE",
        "documentary_label_state": "NOT_EVALUATED",
        "structural_identity_state": "NOT_EVALUATED",
        "canonical_geometry_state": "NOT_AUTHORIZED",
        "canonical_write_authorized": False,
    }


def ledger(rows: list[dict]) -> dict:
    return {
        "schema_id": "CEW_COL03A_GOVERNED_COLUMN_OCCURRENCE_LEDGER",
        "schema_version": 1,
        "source": {
            "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
            "source_path": SOURCE.path,
            "source_sha256": SOURCE.sha256,
            "page_id": "CEW-N12-PAGE-TAV05S-P001",
            "page_index": 0,
            "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        },
        "occurrence_count": len(rows),
        "conflict_count": 0,
        "occurrences": rows,
        "conflicts": [],
        "authority": {
            "support_identity_authorized": False,
            "text_identity_binding_authorized": False,
            "family_assignment_authorized": False,
            "section_assignment_authorized": False,
            "fixed_line_assignment_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "g2c_promotion_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
        },
    }


class StructuralCandidateBridgeTests(unittest.TestCase):
    def test_human_positive_occurrences_map_without_historical_identifier(self) -> None:
        payload = ledger(
            [
                occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08}),
                occurrence("COL-OCC-0002", bbox={"x": 0.40, "y": 0.50, "width": 0.06, "height": 0.09}, decisions=["PILASTRO"]),
            ]
        )
        result = build_structural_candidate_bridge(
            ledger=payload,
            source=SOURCE,
            raster_width_px=4000,
            raster_height_px=3000,
            raster_sha256="a" * 64,
            renderer_tool_version="5.14.0",
        )
        self.assertEqual(result["occurrence_count"], 2)
        self.assertEqual(result["structural_candidate_count"], 2)
        self.assertEqual(result["pre_comparator_bundle"]["structural_candidate_count"], 2)
        self.assertFalse(result["pre_comparator_bundle"]["historical_comparator_loaded"])
        for row in result["structural_candidates"]:
            self.assertEqual(row["semantic_label"], "COLUMN")
            self.assertIsNone(row["support_identifier"])
            self.assertIsNone(row["section_family"])
            self.assertFalse(row["canonical"])
            self.assertFalse(row["structural_identity_authorized"])

    def test_normalized_bbox_is_transformed_only_from_governed_raster_dimensions(self) -> None:
        payload = ledger(
            [occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08})]
        )
        result = build_structural_candidate_bridge(
            ledger=payload,
            source=SOURCE,
            raster_width_px=4000,
            raster_height_px=3000,
            raster_sha256="b" * 64,
            renderer_tool_version="5.14.0",
        )
        bridge = result["occurrence_bridge"][0]
        self.assertEqual(
            bridge["pixel_geometry"],
            {"frame": "RASTER_PIXEL", "x": 400.0, "y": 600.0, "width": 200.0, "height": 240.0},
        )
        self.assertEqual(bridge["occurrence_id"], "COL-OCC-0001")
        self.assertTrue(bridge["review_normalized_from_existing_human_receipt"])

    def test_non_positive_or_conflicted_occurrence_fails_closed(self) -> None:
        negative = ledger(
            [occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08}, decisions=["NOT_COLUMN"])]
        )
        with self.assertRaisesRegex(ValueError, "OCCURRENCE_NOT_HUMAN_POSITIVE"):
            build_structural_candidate_bridge(
                ledger=negative,
                source=SOURCE,
                raster_width_px=4000,
                raster_height_px=3000,
                raster_sha256="c" * 64,
                renderer_tool_version="5.14.0",
            )
        conflicted = ledger(
            [occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08})]
        )
        conflicted["occurrences"][0]["conflict_state"] = "AMBIGUOUS_DUPLICATE"
        with self.assertRaisesRegex(ValueError, "OCCURRENCE_CONFLICT_NOT_CLOSED"):
            build_structural_candidate_bridge(
                ledger=conflicted,
                source=SOURCE,
                raster_width_px=4000,
                raster_height_px=3000,
                raster_sha256="d" * 64,
                renderer_tool_version="5.14.0",
            )

    def test_source_or_authority_drift_fails_closed(self) -> None:
        payload = ledger(
            [occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08})]
        )
        payload["authority"]["structural_identity_authorized"] = True
        with self.assertRaisesRegex(ValueError, "LEDGER_AUTHORITY_DRIFT"):
            build_structural_candidate_bridge(
                ledger=payload,
                source=SOURCE,
                raster_width_px=4000,
                raster_height_px=3000,
                raster_sha256="e" * 64,
                renderer_tool_version="5.14.0",
            )
        payload = ledger(
            [occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08})]
        )
        payload["source"]["source_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "LEDGER_SOURCE_DRIFT"):
            build_structural_candidate_bridge(
                ledger=payload,
                source=SOURCE,
                raster_width_px=4000,
                raster_height_px=3000,
                raster_sha256="e" * 64,
                renderer_tool_version="5.14.0",
            )

    def test_existing_human_receipt_provenance_is_retained_outside_review_coordinates(self) -> None:
        payload = ledger(
            [
                occurrence(
                    "COL-OCC-0001",
                    bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08},
                    receipts=[
                        "governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json",
                        "governance/cew-col03a/COL03A_OCCURRENCE_EQUIVALENCE_HUMAN_REVIEW_v1.json",
                    ],
                )
            ]
        )
        result = build_structural_candidate_bridge(
            ledger=payload,
            source=SOURCE,
            raster_width_px=4000,
            raster_height_px=3000,
            raster_sha256="f" * 64,
            renderer_tool_version="5.14.0",
        )
        bridge = result["occurrence_bridge"][0]
        self.assertEqual(len(bridge["human_review_receipts"]), 2)
        decision = result["pre_comparator_bundle"]["review_decisions"][0]
        self.assertEqual(decision["disposition"], "ACCEPT")
        self.assertEqual(decision["semantic_label"], "COLUMN")
        self.assertNotIn("x", decision)
        self.assertNotIn("y", decision)

    def test_same_inputs_are_deterministic(self) -> None:
        payload = ledger(
            [
                occurrence("COL-OCC-0002", bbox={"x": 0.40, "y": 0.50, "width": 0.06, "height": 0.09}),
                occurrence("COL-OCC-0001", bbox={"x": 0.10, "y": 0.20, "width": 0.05, "height": 0.08}),
            ]
        )
        kwargs = dict(
            source=SOURCE,
            raster_width_px=4000,
            raster_height_px=3000,
            raster_sha256="1" * 64,
            renderer_tool_version="5.14.0",
        )
        first = build_structural_candidate_bridge(ledger=payload, **kwargs)
        second_payload = dict(payload)
        second_payload["occurrences"] = list(reversed(payload["occurrences"]))
        second = build_structural_candidate_bridge(ledger=second_payload, **kwargs)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
