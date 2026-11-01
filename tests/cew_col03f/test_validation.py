from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from experiments.cew_col03f.validate_artifact import validate_col03f_artifact
except (ImportError, ModuleNotFoundError):
    validate_col03f_artifact = None


EXPECTED_SOURCE_SHA = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_SOURCE_VERSION = "CEW-N12-SRC-TAV05S-V2143DBCF"
EXPECTED_ORDER = ["COL-OCC-0001", "COL-OCC-0015"] + [
    f"COL-OCC-{index:04d}" for index in range(1, 23) if index not in {1, 15}
]
AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "vertical_chain_assignment_authorized",
    "structural_identity_authorized",
    "canonical_node_assignment_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def _write_valid_artifact(root: Path) -> None:
    review = root / "review"
    review.mkdir(parents=True)
    source_ref = {
        "source_version_id": EXPECTED_SOURCE_VERSION,
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        "source_sha256": EXPECTED_SOURCE_SHA,
        "raster_sha256": "c" * 64,
        "raster_width_px": 7016,
        "raster_height_px": 12530,
    }
    rows = []
    queue_entries = []
    for queue_index, occurrence_id in enumerate(EXPECTED_ORDER, start=1):
        source_name = f"{occurrence_id}-source-only.png"
        overlay_name = f"{occurrence_id}-target-overlay.png"
        source_path = review / source_name
        overlay_path = review / overlay_name
        source_path.write_bytes(f"source:{occurrence_id}".encode())
        overlay_path.write_bytes(f"overlay:{occurrence_id}".encode())
        import hashlib
        source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        overlay_digest = hashlib.sha256(overlay_path.read_bytes()).hexdigest()
        row = {
            "queue_index": queue_index,
            "occurrence_id": occurrence_id,
            "source_ref": source_ref,
            "crop_manifest": {
                "FOOTPRINT": {"bounds_px": [1, 2, 3, 4]},
                "LOCAL": {"bounds_px": [1, 2, 5, 6]},
                "CONTEXT": {"bounds_px": [0, 0, 7, 8]},
                "source_only_path": f"review/{source_name}",
                "source_only_sha256": source_digest,
                "target_overlay_path": f"review/{overlay_name}",
                "target_overlay_sha256": overlay_digest,
            },
            "acquisition_state": "NO_DIRECT_LABEL_OBSERVED",
            "candidate_values": [],
            "direct_observed_values": [],
            "documentary_candidate_values": ["4"] if occurrence_id == "COL-OCC-0001" else (["30"] if occurrence_id == "COL-OCC-0015" else []),
            "identity_promoted": False,
            "historical_identity_positive_evidence_used": False,
        }
        for key in AUTHORITY_KEYS:
            row[key] = False
        rows.append(row)
        queue_entries.append({
            "queue_index": queue_index,
            "occurrence_id": occurrence_id,
            "candidate_values": [],
            "identity_promoted": False,
            "source_only_path": f"review/{source_name}",
            "source_only_sha256": source_digest,
            "target_overlay_path": f"review/{overlay_name}",
            "target_overlay_sha256": overlay_digest,
        })
    atlas = review / "primary-bridge-atlas.png"
    atlas.write_bytes(b"atlas")
    import hashlib
    atlas_digest = hashlib.sha256(atlas.read_bytes()).hexdigest()
    ledger = {
        "occurrence_count": 22,
        "inspection_order": EXPECTED_ORDER,
        "candidate_occurrence_ids": [],
        "identity_promotion_authorized": False,
        "source_ref": source_ref,
        "occurrences": rows,
    }
    queue = {
        "occurrence_count": 22,
        "inspection_order": EXPECTED_ORDER,
        "priority_occurrence_ids": ["COL-OCC-0001", "COL-OCC-0015"],
        "entries": queue_entries,
        "all_authority_closed": True,
        "any_identity_resolved": False,
        "atlas_path": "review/primary-bridge-atlas.png",
        "atlas_sha256": atlas_digest,
    }
    closure = {
        "occurrence_count": 22,
        "candidate_occurrence_ids": [],
        "unresolved_occurrence_ids": EXPECTED_ORDER,
        "candidate_probe_results": {
            "COL-OCC-0001": {"acquisition_state": "NO_DIRECT_LABEL_OBSERVED", "candidate_values": [], "direct_observed_values": [], "documentary_candidate_values": ["4"]},
            "COL-OCC-0015": {"acquisition_state": "NO_DIRECT_LABEL_OBSERVED", "candidate_values": [], "direct_observed_values": [], "documentary_candidate_values": ["30"]},
        },
        "state_counts": {"NO_DIRECT_LABEL_OBSERVED": 22},
        "primary_source_replayable": True,
        "historical_identity_positive_evidence_used": False,
        "any_identity_resolved": False,
        "all_authority_closed": True,
        "identity_promotion_authorized": False,
        "next_required_action": "ACQUIRE_EXTERNAL_OR_MANUAL_PRIMARY_IDENTITY_EVIDENCE",
        "atlas_path": "review/primary-bridge-atlas.png",
        "atlas_sha256": atlas_digest,
    }
    for name, payload in (
        ("primary-bridge-evidence-ledger.json", ledger),
        ("primary-bridge-inspection-queue.json", queue),
        ("primary-bridge-closure.json", closure),
    ):
        (root / name).write_text(json.dumps(payload), encoding="utf-8")


class ArtifactSemanticValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(validate_col03f_artifact, "COL-03F semantic artifact validator missing")

    def test_valid_semantic_surface_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_valid_artifact(root)
            result = validate_col03f_artifact(root)
            self.assertEqual(result["occurrence_count"], 22)
            self.assertEqual(result["candidate_count"], 0)
            self.assertTrue(result["all_authority_closed"])
            self.assertFalse(result["any_identity_resolved"])

    def test_candidate_authority_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_valid_artifact(root)
            path = root / "primary-bridge-evidence-ledger.json"
            ledger = json.loads(path.read_text())
            ledger["occurrences"][0]["structural_identity_authorized"] = True
            path.write_text(json.dumps(ledger))
            with self.assertRaisesRegex(ValueError, "COL03F_SEMANTIC_AUTHORITY_DRIFT"):
                validate_col03f_artifact(root)

    def test_review_image_hash_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_valid_artifact(root)
            (root / "review" / "COL-OCC-0001-source-only.png").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "COL03F_SEMANTIC_REVIEW_HASH_DRIFT"):
                validate_col03f_artifact(root)

    def test_next_action_must_match_candidate_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_valid_artifact(root)
            path = root / "primary-bridge-closure.json"
            closure = json.loads(path.read_text())
            closure["next_required_action"] = "HUMAN_ADJUDICATE_PRIMARY_LABEL_BRIDGE_CANDIDATES"
            path.write_text(json.dumps(closure))
            with self.assertRaisesRegex(ValueError, "COL03F_SEMANTIC_NEXT_ACTION_DRIFT"):
                validate_col03f_artifact(root)


if __name__ == "__main__":
    unittest.main()
