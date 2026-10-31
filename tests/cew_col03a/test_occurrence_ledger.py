from __future__ import annotations

import copy
import unittest


SOURCE = {
    "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
    "source_path": "archive/documentazione_originaria/tavola 5.pdf",
    "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_id": "CEW-N12-PAGE-TAV05S-P001",
    "page_index": 0,
    "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
}


def _proposal_payload() -> dict:
    candidates = []
    for index in range(1, 612):
        candidates.append(
            {
                "candidate_id": f"COL02-FP-{index:04d}",
                "bbox": {
                    "x": ((index - 1) % 50) * 0.015,
                    "y": ((index - 1) // 50) * 0.02,
                    "width": 0.01,
                    "height": 0.012,
                },
                "detector": "TEST",
            }
        )
    candidates[362]["bbox"] = {"x": 0.10, "y": 0.20, "width": 0.020, "height": 0.030}
    candidates[251]["bbox"] = {"x": 0.30, "y": 0.40, "width": 0.018, "height": 0.024}
    return {"candidate_count": 611, "candidates": candidates}


def _evidence(candidate_id: str, *, repair_id: str | None = None) -> dict:
    return {
        "evidence_id": f"E:{candidate_id}:{repair_id or 'BASE'}",
        "candidate_id": candidate_id,
        "evidence_class": "REPAIRED_SUCCESSOR_CONFIRMED" if repair_id else "PROTOTYPE_CONFIRMED",
        "graphical_decision": "PASS" if repair_id else "COLUMN_FOOTPRINT_CONFIRMED",
        "discovery_path": "REFRAME_CONFIRMATION" if repair_id else "HUMAN_PROTOTYPE_REVIEW",
        "human_review_receipt": "fixture.json",
        "repair_id": repair_id,
        "human_added_point_event_ids": [],
        "lineage": {"fixture": True},
    }


def _repair_manifest() -> dict:
    return {
        "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_MANIFEST_v1",
        "repairs": [
            {
                "repair_id": "COL02-WSR-001",
                "source_candidate_id": "COL02-FP-0252",
                "status": "READY_FOR_HUMAN_GRAPHICAL_REVIEW",
                "reconstructed_bbox": {"x": 0.295, "y": 0.395, "width": 0.030, "height": 0.036},
            }
        ],
    }


class ExactSourceGeometryTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.cew_col03a import occurrence_ledger

        return occurrence_ledger

    def test_proposal_geometry_index_requires_exactly_611_unique_candidates(self):
        module = self._module()
        payload = _proposal_payload()
        index = module.build_proposal_geometry_index(payload)
        self.assertEqual(len(index), 611)
        self.assertEqual(index["COL02-FP-0363"]["bbox"], payload["candidates"][362]["bbox"])

        duplicate = copy.deepcopy(payload)
        duplicate["candidates"][-1]["candidate_id"] = duplicate["candidates"][0]["candidate_id"]
        with self.assertRaises(ValueError):
            module.build_proposal_geometry_index(duplicate)

        short = copy.deepcopy(payload)
        short["candidates"].pop()
        short["candidate_count"] = 610
        with self.assertRaises(ValueError):
            module.build_proposal_geometry_index(short)

    def test_non_repaired_occurrence_uses_frozen_proposal_geometry(self):
        module = self._module()
        proposal_index = module.build_proposal_geometry_index(_proposal_payload())
        records = module.attach_exact_source_geometry(
            evidence_items=[_evidence("COL02-FP-0363")],
            proposal_index=proposal_index,
            repair_manifest=_repair_manifest(),
            source=SOURCE,
        )
        self.assertEqual(len(records), 1)
        record = records[0]
        expected_bbox = {"x": 0.10, "y": 0.20, "width": 0.020, "height": 0.030}
        self.assertEqual(record["anchor_bbox"], expected_bbox)
        self.assertEqual(
            record["primary_graphical_representation"],
            {
                "kind": "FROZEN_PROPOSAL",
                "candidate_id": "COL02-FP-0363",
                "repair_id": None,
                "bbox": expected_bbox,
            },
        )
        self.assertTrue(record["exact_source_reconstructible"])
        self.assertTrue(record["lineage_complete"])
        self.assertEqual(record["source_version_id"], SOURCE["source_version_id"])
        self.assertEqual(record["source_path"], SOURCE["source_path"])
        self.assertEqual(record["source_sha256"], SOURCE["sha256"])
        self.assertEqual(record["page_transform_id"], SOURCE["page_transform_id"])

    def test_repaired_occurrence_keeps_anchor_but_promotes_governed_repair_for_review(self):
        module = self._module()
        proposal_index = module.build_proposal_geometry_index(_proposal_payload())
        records = module.attach_exact_source_geometry(
            evidence_items=[_evidence("COL02-FP-0252", repair_id="COL02-WSR-001")],
            proposal_index=proposal_index,
            repair_manifest=_repair_manifest(),
            source=SOURCE,
        )
        record = records[0]
        self.assertEqual(record["anchor_bbox"], {"x": 0.30, "y": 0.40, "width": 0.018, "height": 0.024})
        self.assertEqual(
            record["primary_graphical_representation"],
            {
                "kind": "GOVERNED_WHOLE_SYMBOL_REPAIR",
                "candidate_id": "COL02-FP-0252",
                "repair_id": "COL02-WSR-001",
                "bbox": {"x": 0.295, "y": 0.395, "width": 0.030, "height": 0.036},
            },
        )
        self.assertEqual(record["repair_id"], "COL02-WSR-001")

    def test_missing_candidate_cannot_be_synthesized_from_other_proposals(self):
        module = self._module()
        proposal_index = module.build_proposal_geometry_index(_proposal_payload())
        with self.assertRaises(ValueError):
            module.attach_exact_source_geometry(
                evidence_items=[_evidence("COL02-FP-9999")],
                proposal_index=proposal_index,
                repair_manifest=_repair_manifest(),
                source=SOURCE,
            )

    def test_missing_reconstructed_repair_geometry_fails_closed(self):
        module = self._module()
        proposal_index = module.build_proposal_geometry_index(_proposal_payload())
        repair = _repair_manifest()
        repair["repairs"][0]["reconstructed_bbox"] = None
        with self.assertRaises(ValueError):
            module.attach_exact_source_geometry(
                evidence_items=[_evidence("COL02-FP-0252", repair_id="COL02-WSR-001")],
                proposal_index=proposal_index,
                repair_manifest=repair,
                source=SOURCE,
            )

    def test_wrong_source_sha_or_missing_transform_fails_before_reconstruction(self):
        module = self._module()
        proposal_index = module.build_proposal_geometry_index(_proposal_payload())

        wrong_sha = dict(SOURCE)
        wrong_sha["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            module.attach_exact_source_geometry(
                evidence_items=[_evidence("COL02-FP-0363")],
                proposal_index=proposal_index,
                repair_manifest=_repair_manifest(),
                source=wrong_sha,
            )

        missing_transform = dict(SOURCE)
        missing_transform.pop("page_transform_id")
        with self.assertRaises(ValueError):
            module.attach_exact_source_geometry(
                evidence_items=[_evidence("COL02-FP-0363")],
                proposal_index=proposal_index,
                repair_manifest=_repair_manifest(),
                source=missing_transform,
            )

    def test_geometry_lookup_never_expands_the_governed_evidence_set(self):
        module = self._module()
        proposal_index = module.build_proposal_geometry_index(_proposal_payload())
        records = module.attach_exact_source_geometry(
            evidence_items=[_evidence("COL02-FP-0363")],
            proposal_index=proposal_index,
            repair_manifest=_repair_manifest(),
            source=SOURCE,
        )
        self.assertEqual([row["candidate_id"] for row in records], ["COL02-FP-0363"])


if __name__ == "__main__":
    unittest.main()
