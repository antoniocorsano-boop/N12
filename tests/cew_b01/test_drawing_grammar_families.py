from __future__ import annotations

import inspect
import unittest

from cew_b01.drawing_grammar import (
    DrawingMotif,
    discover_local_families,
    find_similar,
)


def _motif(
    motif_id: str,
    *,
    x: int,
    y: int,
    width: int = 70,
    height: int = 80,
    frame_coverage: float = 0.92,
    internal_ink_ratio: float = 0.072,
    internal_component_count: int = 1,
    context_signature: tuple[float, float, float, float] = (0.18, 0.16, 0.0, 0.0),
) -> DrawingMotif:
    return DrawingMotif(
        motif_id=motif_id,
        x=x,
        y=y,
        width=width,
        height=height,
        frame_coverage=frame_coverage,
        internal_ink_ratio=internal_ink_ratio,
        internal_component_count=internal_component_count,
        single_full_span_divider=False,
        context_signature=context_signature,
        semantic_identity=None,
    )


class LocalFamilyDiscoveryTests(unittest.TestCase):
    def test_family_discovery_is_deterministic_and_keeps_incompatible_residual_unknown(self) -> None:
        first = _motif("M-A", x=20, y=30)
        translated = _motif(
            "M-B",
            x=420,
            y=330,
            width=72,
            height=82,
            internal_ink_ratio=0.075,
        )
        incompatible = _motif(
            "M-C",
            x=800,
            y=50,
            context_signature=(0.0, 0.0, 0.17, 0.16),
        )

        forward = discover_local_families((first, translated, incompatible), threshold=0.80)
        reverse = discover_local_families((incompatible, translated, first), threshold=0.80)

        self.assertEqual(forward, reverse)
        self.assertEqual(len(forward), 2)

        family = next(item for item in forward if item.classification == "LOCAL_FAMILY")
        unknown = next(item for item in forward if item.classification == "UNKNOWN")

        self.assertEqual(set(family.member_motif_ids), {"M-A", "M-B"})
        self.assertIn(family.prototype_motif_id, family.member_motif_ids)
        self.assertEqual(unknown.member_motif_ids, ("M-C",))
        self.assertIsNone(family.semantic_identity)
        self.assertIsNone(unknown.semantic_identity)

    def test_find_similar_recovers_translated_variant_without_identifier_or_coordinates_as_oracles(self) -> None:
        prototype = _motif("P-19", x=40, y=60)
        compatible = _motif(
            "P-22",
            x=960,
            y=740,
            width=73,
            height=81,
            frame_coverage=0.89,
            internal_ink_ratio=0.078,
        )
        incompatible = _motif(
            "BEAM-BAY",
            x=300,
            y=500,
            width=118,
            height=42,
            internal_ink_ratio=0.035,
            context_signature=(0.0, 0.0, 0.19, 0.18),
        )

        matches = find_similar(prototype, (incompatible, compatible, prototype), threshold=0.80)

        self.assertEqual(tuple(item.motif_id for item in matches), ("P-22",))
        source = inspect.getsource(find_similar).lower()
        for forbidden in ("ocr", "identifier", "semantic_identity", ".x", ".y"):
            self.assertNotIn(forbidden, source)

    def test_invalid_similarity_threshold_fails_closed(self) -> None:
        prototype = _motif("P", x=0, y=0)
        with self.assertRaises(ValueError):
            find_similar(prototype, (prototype,), threshold=0.0)
        with self.assertRaises(ValueError):
            discover_local_families((prototype,), threshold=1.01)


if __name__ == "__main__":
    unittest.main()
