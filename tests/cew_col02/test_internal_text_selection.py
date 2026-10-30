from __future__ import annotations

import unittest

from experiments.cew_col02.text_footprint_binding import bind_text_observations


class InternalTextSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.footprint = {"x": 0.0, "y": 0.0, "width": 10.0, "height": 10.0}

    @staticmethod
    def observation(token_id: str, x: float, y: float, width: float, height: float, text: str) -> dict:
        return {
            "token_id": token_id,
            "raw_text": text,
            "bbox": {"x": x, "y": y, "width": width, "height": height},
        }

    def test_one_internal_token_is_preferred(self) -> None:
        result = bind_text_observations(
            self.footprint,
            [self.observation("T1", 3.0, 4.0, 2.0, 1.0, "18")],
        )
        self.assertEqual(result["binding_state"], "ONE_INTERNAL_TEXT")
        self.assertEqual(result["internal_token_ids"], ["T1"])
        self.assertEqual(result["preferred_internal_token_id"], "T1")

    def test_near_external_dimension_is_never_preferred(self) -> None:
        result = bind_text_observations(
            self.footprint,
            [
                self.observation("IN", 3.0, 4.0, 2.0, 1.0, "18"),
                self.observation("DIM", 10.5, 4.0, 2.0, 1.0, "30"),
            ],
        )
        self.assertEqual(result["preferred_internal_token_id"], "IN")
        by_id = {item["token_id"]: item for item in result["bindings"]}
        self.assertEqual(by_id["DIM"]["relation"], "NEAR_OUTSIDE_FOOTPRINT")
        self.assertFalse(by_id["DIM"]["preferred_internal_text"])

    def test_multiple_internal_tokens_remain_ambiguous(self) -> None:
        result = bind_text_observations(
            self.footprint,
            [
                self.observation("T1", 2.0, 3.0, 2.0, 1.0, "1"),
                self.observation("T2", 6.0, 6.0, 2.0, 1.0, "8"),
            ],
        )
        self.assertEqual(result["binding_state"], "MULTIPLE_INTERNAL_TEXT_AMBIGUOUS")
        self.assertEqual(result["internal_token_ids"], ["T1", "T2"])
        self.assertIsNone(result["preferred_internal_token_id"])

    def test_no_internal_token_remains_explicit(self) -> None:
        result = bind_text_observations(
            self.footprint,
            [self.observation("DIM", 11.0, 4.0, 2.0, 1.0, "30")],
        )
        self.assertEqual(result["binding_state"], "NO_INTERNAL_TEXT")
        self.assertEqual(result["internal_token_ids"], [])
        self.assertIsNone(result["preferred_internal_token_id"])

    def test_token_ids_must_be_unique(self) -> None:
        with self.assertRaises(ValueError):
            bind_text_observations(
                self.footprint,
                [
                    self.observation("T1", 2.0, 3.0, 2.0, 1.0, "1"),
                    self.observation("T1", 6.0, 6.0, 2.0, 1.0, "8"),
                ],
            )


if __name__ == "__main__":
    unittest.main()
