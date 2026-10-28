from __future__ import annotations

import inspect
import unittest

import cew_b01.drawing_grammar as drawing_grammar
from cew_b01.drawing_grammar import DrawingMotif
from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.records import SourceIdentity
from cew_b01.reuse_adapter import (
    OA3_CAPABILITY_ID,
    PR137_DESCRIPTOR_CAPABILITY_ID,
    build_human_taught_oa3_prototype,
    build_oa3_scene,
)
from cew_b01.reused_oa3_similarity import OA3_SOURCE_REF, find_similar


SOURCE = SourceIdentity(
    repository="antoniocorsano-boop/N12",
    commit="78c20a52db4f391ce0d13b9705b9f04737e218c9",
    path="archive/documentazione_originaria/tavola 5.pdf",
    git_blob_sha="ec32cd621877e9037cb26ebc083164140a8e3e68",
    sha256="2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    page_index=0,
)

BINDING = Task3RasterBinding(
    source=SOURCE,
    raster_width_px=3000,
    raster_height_px=2000,
    raster_sha256="1" * 64,
    png_sha256="2" * 64,
    renderer_tool_id="pypdfium2",
    renderer_tool_version="5.14.0",
)


def _motif(
    motif_id: str,
    *,
    x: int,
    y: int,
    width: int = 70,
    height: int = 80,
    context_signature: tuple[float, float, float, float] = (0.18, 0.16, 0.0, 0.0),
) -> DrawingMotif:
    return DrawingMotif(
        motif_id=motif_id,
        x=x,
        y=y,
        width=width,
        height=height,
        frame_coverage=0.91,
        internal_ink_ratio=0.072,
        internal_component_count=2,
        single_full_span_divider=False,
        context_signature=context_signature,
        semantic_identity=None,
    )


class ReuseAdapterTests(unittest.TestCase):
    def test_scene_preserves_exact_b01_source_and_uses_reused_descriptor_vocabulary(self) -> None:
        motif = _motif("M-A", x=120, y=240)

        scene = build_oa3_scene(BINDING, (motif,))

        self.assertEqual(scene["source"]["original_source"], SOURCE.to_mapping())
        self.assertEqual(scene["source"]["source_sha256"], SOURCE.sha256)
        self.assertTrue(scene["source"]["source_version_id"].startswith("CEW-B01-DERIVED-SV-"))
        self.assertTrue(scene["source"]["page_id"].startswith("CEW-B01-DERIVED-PAGE-"))
        self.assertTrue(scene["source"]["evidence_region_id"].startswith("CEW-B01-DERIVED-PAGE-REGION-"))
        self.assertEqual(scene["reuse"]["oa3_capability_id"], OA3_CAPABILITY_ID)
        self.assertEqual(scene["reuse"]["structured_descriptor_capability_id"], PR137_DESCRIPTOR_CAPABILITY_ID)

        obj = scene["objects"][0]
        self.assertEqual(obj["object_id"], "M-A")
        self.assertEqual(obj["geometry"]["type"], "RECTANGLE")
        self.assertEqual(obj["structured_descriptor"]["provider_id"], "CEW_STRUCTURED_GRAPHIC_DESCRIPTOR_V1")
        self.assertEqual(
            obj["structured_descriptor"]["feature_signature"]["primitive_family"],
            "RECTILINEAR_CLOSED_SHAPE",
        )
        self.assertIsNone(obj["properties"]["associated_text"])
        self.assertFalse(obj["authority"]["structural_identity_authorized"])
        self.assertFalse(obj["authority"]["canonical_write_authorized"])

    def test_human_taught_prototype_requires_explicit_human_decision(self) -> None:
        scene = build_oa3_scene(BINDING, (_motif("M-A", x=100, y=200),))

        with self.assertRaises(ValueError):
            build_human_taught_oa3_prototype(
                scene,
                anchor_object_id="M-A",
                human_decision_id="",
                prototype_id="PROTO-1",
                object_type="LOCAL_GRAPHIC_CONCEPT",
                family_id="LOCAL-GRAPHIC-FAMILY",
            )

        prototype = build_human_taught_oa3_prototype(
            scene,
            anchor_object_id="M-A",
            human_decision_id="HUMAN-DECISION-001",
            prototype_id="PROTO-1",
            object_type="LOCAL_GRAPHIC_CONCEPT",
            family_id="LOCAL-GRAPHIC-FAMILY",
        )
        self.assertEqual(prototype["state"], "HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE")
        self.assertEqual(prototype["human_decision_id"], "HUMAN-DECISION-001")
        self.assertEqual(prototype["source_evidence"], scene["source"])
        self.assertFalse(prototype["canonical_write_authorized"])
        self.assertFalse(prototype["structural_identity_authorized"])

    def test_reused_oa3_ranks_translated_compatible_above_context_incompatible(self) -> None:
        prototype_motif = _motif("M-A", x=40, y=60)
        translated = _motif("M-B", x=1700, y=1200, width=72, height=82)
        incompatible = _motif(
            "M-C",
            x=900,
            y=400,
            context_signature=(0.0, 0.0, 0.17, 0.16),
        )
        scene = build_oa3_scene(BINDING, (incompatible, translated, prototype_motif))
        prototype = build_human_taught_oa3_prototype(
            scene,
            anchor_object_id="M-A",
            human_decision_id="HUMAN-DECISION-002",
            prototype_id="PROTO-2",
            object_type="LOCAL_GRAPHIC_CONCEPT",
            family_id="LOCAL-GRAPHIC-FAMILY",
        )

        result = find_similar(scene, prototype)

        self.assertEqual(OA3_SOURCE_REF, "a7020bef3934156c917f5bfe975d888c6ba9e684")
        self.assertEqual(result["candidates"][0]["candidate_object_id"], "M-B")
        scores = {row["candidate_object_id"]: row["score"] for row in result["candidates"]}
        self.assertGreater(scores["M-B"], scores["M-C"])
        self.assertGreaterEqual(scores["M-B"], 0.75)
        self.assertTrue(all(row["human_confirmation_required"] for row in result["candidates"]))
        self.assertFalse(result["auto_confirm_cluster_authorized"])
        self.assertFalse(result["structural_identity_created"])
        self.assertFalse(result["canonical_write_authorized"])

    def test_b01_feature_channel_does_not_own_generic_similarity_or_family_discovery(self) -> None:
        source = inspect.getsource(drawing_grammar)
        for forbidden in (
            "class LocalSymbolFamilyCandidate",
            "def discover_local_families",
            "def find_similar",
            "def motif_similarity",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
