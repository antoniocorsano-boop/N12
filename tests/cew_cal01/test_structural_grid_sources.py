import unittest

from experiments.cew_cal01.structural_grid_sources import (
    STRUCTURAL_GRID_SOURCES,
    build_structural_grid_manifest,
    validate_source_registry,
)


class Cal01StructuralGridSourceContractTests(unittest.TestCase):
    def test_registry_contains_only_frozen_primary_structural_grid_sources_in_order(self):
        self.assertEqual([row["source_id"] for row in STRUCTURAL_GRID_SOURCES], ["TAV-01S", "TAV-02S"])
        self.assertEqual(
            [row["path"] for row in STRUCTURAL_GRID_SOURCES],
            [
                "archive/documentazione_originaria/tavola1-2.pdf",
                "archive/documentazione_originaria/tavola2-2.pdf",
            ],
        )
        self.assertEqual(
            [row["sha256"] for row in STRUCTURAL_GRID_SOURCES],
            [
                "abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8",
                "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f",
            ],
        )
        self.assertTrue(all(row["source_commit"] == "78c20a52db4f391ce0d13b9705b9f04737e218c9" for row in STRUCTURAL_GRID_SOURCES))
        self.assertTrue(all(row["functional_role"] == "STRUCTURAL_GRID_PRIMARY_SOURCE" for row in STRUCTURAL_GRID_SOURCES))

    def test_registry_rejects_duplicate_source_ids(self):
        rows = [dict(STRUCTURAL_GRID_SOURCES[0]), dict(STRUCTURAL_GRID_SOURCES[0])]
        with self.assertRaisesRegex(ValueError, "CAL01_STRUCTURAL_GRID_SOURCE_ID_DUPLICATE"):
            validate_source_registry(rows)

    def test_registry_rejects_duplicate_source_paths(self):
        first = dict(STRUCTURAL_GRID_SOURCES[0])
        second = dict(STRUCTURAL_GRID_SOURCES[1])
        second["path"] = first["path"]
        with self.assertRaisesRegex(ValueError, "CAL01_STRUCTURAL_GRID_SOURCE_PATH_DUPLICATE"):
            validate_source_registry([first, second])

    def test_manifest_keeps_authority_closed_and_preserves_render_records(self):
        renders = [
            {
                "source_id": "TAV-01S",
                "source_sha256": STRUCTURAL_GRID_SOURCES[0]["sha256"],
                "raster_path": "TAV-01S-primary-300dpi.png",
                "width_px": 1000,
                "height_px": 2000,
                "pixel_sha256": "a" * 64,
            },
            {
                "source_id": "TAV-02S",
                "source_sha256": STRUCTURAL_GRID_SOURCES[1]["sha256"],
                "raster_path": "TAV-02S-primary-300dpi.png",
                "width_px": 1100,
                "height_px": 2100,
                "pixel_sha256": "b" * 64,
            },
        ]
        result = build_structural_grid_manifest(renders)
        self.assertEqual(result["schema"], "CEW_CAL01_STRUCTURAL_GRID_PRIMARY_SOURCES_v1")
        self.assertEqual(result["source_count"], 2)
        self.assertEqual([row["source_id"] for row in result["sources"]], ["TAV-01S", "TAV-02S"])
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["historical_comparator_loaded"])
        self.assertFalse(result["historical_affine_loaded"])
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])
        self.assertFalse(result["authority"]["canonical_write_authorized"])
        self.assertEqual(result["authority"]["engineering_authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
