from __future__ import annotations

import unittest

from experiments.cew_b01.g2b_core_context_refinement import refine_candidate


def bundle(bid: str, families: list[str], *, x: float, y: float, w: float, h: float, members: list[str] | None = None):
    return {
        "bundle_id": bid,
        "families": families,
        "geometry": {"x": x, "y": y, "width": w, "height": h},
        "member_primitive_ids": members or [bid + "-p"],
    }


def candidate(core_bundles, relations, *, context_ids=None, context_primitives=None):
    seed = core_bundles[0]
    return {
        "candidate_id": "cand",
        "seed_bundle_id": seed["bundle_id"],
        "seed_primitive_id": seed["member_primitive_ids"][0],
        "core_bundle_count": len(core_bundles),
        "core_bundle_ids": [b["bundle_id"] for b in core_bundles],
        "core_primitive_ids_expanded": sorted({p for b in core_bundles for p in b["member_primitive_ids"]}),
        "context_bundle_ids": list(context_ids or ["ctx-old"]),
        "context_primitive_ids_expanded": list(context_primitives or ["ctx-old-p"]),
        "core_bundles": core_bundles,
        "relations": relations,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }


class G2BCoreContextRefinementTests(unittest.TestCase):
    def test_near_only_bundle_moves_to_context(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=0, y=0, w=100, h=40)
        near = bundle("near", ["FILLED_OR_HATCHED_REGION"], x=108, y=5, w=15, h=15)
        c = candidate([seed, near], [{"a": "seed", "b": "near", "relations": ["NEAR"]}])
        out = refine_candidate(c)
        self.assertEqual(out["g2b_core_bundle_ids"], ["seed"])
        self.assertIn("near", out["g2b_context_bundle_ids"])
        self.assertEqual(out["boundary_decisions"]["near"]["reason"], "NEAR_ONLY")

    def test_dominant_attached_line_moves_to_context(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=100, y=100, w=120, h=40)
        line = bundle("line", ["LINE_SEGMENT"], x=90, y=141, w=300, h=2)
        c = candidate([seed, line], [{"a": "seed", "b": "line", "relations": ["TOUCHING"]}])
        out = refine_candidate(c)
        self.assertEqual(out["g2b_core_bundle_ids"], ["seed"])
        self.assertEqual(out["boundary_decisions"]["line"]["reason"], "DOMINANT_LINEAR_CONTEXT")

    def test_dominant_closed_or_complex_bundle_moves_to_context(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=100, y=100, w=100, h=50)
        large = bundle("large", ["COMPLEX_GRAPHIC_GROUP"], x=90, y=90, w=180, h=90)
        c = candidate([seed, large], [{"a": "seed", "b": "large", "relations": ["CONTAINS", "OVERLAPS"]}])
        out = refine_candidate(c)
        self.assertEqual(out["g2b_core_bundle_ids"], ["seed"])
        self.assertEqual(out["boundary_decisions"]["large"]["reason"], "DOMINANT_CLOSED_OR_COMPLEX_CONTEXT")

    def test_directional_relations_are_normalized_from_seed_viewpoint(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=100, y=100, w=100, h=50)
        large = bundle("large", ["COMPLEX_GRAPHIC_GROUP"], x=90, y=90, w=180, h=90)
        c = candidate([seed, large], [{"a": "large", "b": "seed", "relations": ["CONTAINS", "OVERLAPS"]}])
        out = refine_candidate(c)
        self.assertEqual(
            out["boundary_decisions"]["large"]["seed_relations"],
            ["CONTAINED_BY", "OVERLAPS"],
        )

    def test_compact_overlapping_derived_event_stays_core(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=100, y=100, w=100, h=50)
        local = bundle("local", ["INTERSECTION", "T_JUNCTION", "T_SHAPED_MOTIF"], x=190, y=105, w=12, h=12, members=["i", "t", "ts"])
        c = candidate([seed, local], [{"a": "seed", "b": "local", "relations": ["OVERLAPS"]}])
        out = refine_candidate(c)
        self.assertEqual(out["g2b_core_bundle_ids"], ["seed", "local"])
        self.assertEqual(out["boundary_decisions"]["local"]["reason"], "RETAIN_COMPACT_CONTACT")

    def test_membership_and_primitive_provenance_are_conserved(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=0, y=0, w=100, h=40, members=["s"])
        near = bundle("near", ["FILLED_OR_HATCHED_REGION"], x=108, y=5, w=15, h=15, members=["n1", "n2"])
        local = bundle("local", ["INTERSECTION"], x=95, y=10, w=10, h=10, members=["l1", "l2"])
        c = candidate(
            [seed, near, local],
            [
                {"a": "seed", "b": "near", "relations": ["NEAR"]},
                {"a": "seed", "b": "local", "relations": ["OVERLAPS"]},
            ],
            context_ids=["ctx-old"],
            context_primitives=["ctx-old-p"],
        )
        out = refine_candidate(c)
        incoming_bundles = set(c["core_bundle_ids"]) | set(c["context_bundle_ids"])
        outgoing_bundles = set(out["g2b_core_bundle_ids"]) | set(out["g2b_context_bundle_ids"])
        incoming_primitives = set(c["core_primitive_ids_expanded"]) | set(c["context_primitive_ids_expanded"])
        outgoing_primitives = set(out["g2b_core_primitive_ids_expanded"]) | set(out["g2b_context_primitive_ids_expanded"])
        self.assertEqual(incoming_bundles, outgoing_bundles)
        self.assertEqual(incoming_primitives, outgoing_primitives)
        self.assertEqual(len(out["g2b_context_bundle_ids"]), len(set(out["g2b_context_bundle_ids"])))
        self.assertEqual(len(out["g2b_context_primitive_ids_expanded"]), len(set(out["g2b_context_primitive_ids_expanded"])))

    def test_refinement_is_deterministic_for_core_order(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=0, y=0, w=100, h=40)
        near = bundle("near", ["FILLED_OR_HATCHED_REGION"], x=108, y=5, w=15, h=15)
        line = bundle("line", ["LINE_SEGMENT"], x=-10, y=40, w=250, h=2)
        rel = [
            {"a": "seed", "b": "near", "relations": ["NEAR"]},
            {"a": "seed", "b": "line", "relations": ["TOUCHING"]},
        ]
        first = refine_candidate(candidate([seed, near, line], rel))
        second_input = candidate([seed, line, near], list(reversed(rel)))
        second = refine_candidate(second_input)
        self.assertEqual(first, second)

    def test_authority_remains_false(self):
        seed = bundle("seed", ["RECTILINEAR_CLOSED_SHAPE"], x=0, y=0, w=100, h=40)
        out = refine_candidate(candidate([seed], []))
        self.assertIsNone(out["semantic_meaning"])
        self.assertFalse(out["structural_identity_authorized"])
        self.assertFalse(out["canonical_write_authorized"])
        self.assertFalse(out["g3_authorized"])
        self.assertFalse(out["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
