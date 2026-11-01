from __future__ import annotations

import unittest

try:
    from experiments.cew_col03f.exact_source import (
        context_region_from_bounds,
        parse_targeted_tsv,
    )
except (ImportError, ModuleNotFoundError):
    context_region_from_bounds = None
    parse_targeted_tsv = None


TSV = "\n".join(
    [
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext",
        "5\t1\t1\t1\t1\t1\t20\t20\t20\t20\t96.0\t4",
        "5\t1\t1\t1\t1\t2\t80\t80\t20\t20\t88.0\t30",
        "5\t1\t1\t1\t1\t3\t30\t30\t20\t20\t90.0\tN001",
        "5\t1\t1\t1\t1\t4\t40\t40\t20\t20\t10.0\t12",
    ]
) + "\n"


class TargetedOCRContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(context_region_from_bounds, "COL-03F context region helper missing")
        self.assertIsNotNone(parse_targeted_tsv, "COL-03F targeted TSV parser missing")

    def test_context_region_is_exact_normalized_projection_of_pixel_bounds(self):
        region = context_region_from_bounds((100, 200, 500, 700), page_width=1000, page_height=1000)
        self.assertEqual(region, {"x": 0.1, "y": 0.2, "width": 0.4, "height": 0.5})

    def test_targeted_tsv_retains_only_support_like_numeric_tokens_and_maps_them(self):
        observations = parse_targeted_tsv(
            TSV,
            occurrence_id="COL-OCC-0001",
            region_class="LOCAL",
            ocr_configuration="PSM11",
            crop_bounds=(0, 0, 200, 200),
            scale=1.0,
            page_width=1000,
            page_height=1000,
            occurrence_bbox={"x": 0.0, "y": 0.0, "width": 0.05, "height": 0.05},
            local_region={"x": 0.0, "y": 0.0, "width": 0.20, "height": 0.20},
            provenance_prefix="CEW-N12-XFORM-TAV05S-P001:COL03F",
        )
        self.assertEqual([row["normalized_text"] for row in observations], ["4", "30"])
        self.assertEqual(observations[0]["relation"], "INTERNAL")
        self.assertEqual(observations[1]["relation"], "NEARBY")
        self.assertNotIn("N001", [row["normalized_text"] for row in observations])
        self.assertNotIn("12", [row["normalized_text"] for row in observations])

    def test_targeted_tsv_rejects_unfrozen_ocr_configuration(self):
        with self.assertRaisesRegex(ValueError, "COL03F_OCR_CONFIGURATION_INVALID"):
            parse_targeted_tsv(
                TSV,
                occurrence_id="COL-OCC-0001",
                region_class="FOOTPRINT",
                ocr_configuration="PSM3",
                crop_bounds=(0, 0, 200, 200),
                scale=1.0,
                page_width=1000,
                page_height=1000,
                occurrence_bbox={"x": 0.0, "y": 0.0, "width": 0.05, "height": 0.05},
                local_region={"x": 0.0, "y": 0.0, "width": 0.20, "height": 0.20},
                provenance_prefix="P",
            )


if __name__ == "__main__":
    unittest.main()
