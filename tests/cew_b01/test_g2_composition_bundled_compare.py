from __future__ import annotations

import unittest

from experiments.cew_b01.g2_composition_bundled_compare import build_bundled_candidates


def primitive(pid: str, family: str, *, x: float, y: float, w: float, h: float, orientation: str | None = None):
    sig = {}
    if orientation:
        sig["orientation"] = orientation
    return {
        "primitive_id": pid,
        "source": {"sha256": "s" * 64},
        "page_index": 0,
        "frame": "RASTER_PIXEL",
        "geometry": {"x": x, "y": y, "width": w, "height": h},
        "family": family,
        "detector": "TEST",
        "feature_signature": sig,
    }


class BundledCompositionTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            primitive("seed", "RECTILINEAR_CLOSED_SHAPE", x=80, y=80, w=60, h=40),
            primitive("i", "INTERSECTION", x=136, y=95, w=8, h=8),
            primitive("c", "CROSS_MOTIF", x=133, y=92, w=14, h=14),
            primitive("t", "T_SHAPED_MOTIF", x=134, y=92, w=14, h=14),
            primitive("line", "LINE_SEGMENT", x=20, y=99, w=220, h=2, orientation="HORIZONTAL"),
        ]

    def test_seed_identity_is_preserved_and_core_expands_to_original_primitives(self):
        candidates = build_bundled_candidates(self.items, ["seed"], max_core_members=24)
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["seed_primitive_id"], "seed")
        self.assertIn("seed", candidate["core_primitive_ids_expanded"])
        self.assertTrue({"i", "c", "t"}.issubset(set(candidate["core_primitive_ids_expanded"])))
        self.assertLess(candidate["core_bundle_count"], len(candidate["core_primitive_ids_expanded"]))

    def test_provenance_expansion_has_no_duplicate_or_missing_core_members(self):
        candidate = build_bundled_candidates(self.items, ["seed"], max_core_members=24)[0]
        expanded = candidate["core_primitive_ids_expanded"]
        self.assertEqual(len(expanded), len(set(expanded)))
        self.assertEqual(set(expanded), set().union(*(set(b["member_primitive_ids"]) for b in candidate["core_bundles"])))

    def test_reversed_input_is_deterministic(self):
        first = build_bundled_candidates(self.items, ["seed"], max_core_members=24)
        second = build_bundled_candidates(list(reversed(self.items)), ["seed"], max_core_members=24)
        self.assertEqual(first, second)

    def test_authority_flags_remain_false(self):
        candidate = build_bundled_candidates(self.items, ["seed"], max_core_members=24)[0]
        self.assertIsNone(candidate["semantic_meaning"])
        self.assertFalse(candidate["structural_identity_authorized"])
        self.assertFalse(candidate["canonical_write_authorized"])


if __name__ == "__main__":
    unittest.main()
