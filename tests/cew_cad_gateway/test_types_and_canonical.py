from __future__ import annotations

import math
import unittest
from dataclasses import dataclass
from enum import Enum

from cew_cad_gateway.canonical import canonical_json_bytes, sha256_json
from cew_cad_gateway.types import (
    ApprovalReceipt,
    EpistemicState,
    PathClass,
)


class DemoEnum(str, Enum):
    B = "b"
    A = "a"


@dataclass(frozen=True)
class DemoRecord:
    z: int
    a: DemoEnum


class CanonicalJsonTests(unittest.TestCase):
    def test_canonical_json_is_sorted_compact_utf8_and_stable(self) -> None:
        left = {"z": "è", "a": DemoRecord(z=2, a=DemoEnum.A)}
        right = {"a": DemoRecord(a=DemoEnum.A, z=2), "z": "è"}

        expected = b'{"a":{"a":"a","z":2},"z":"\xc3\xa8"}'
        self.assertEqual(canonical_json_bytes(left), expected)
        self.assertEqual(canonical_json_bytes(right), expected)
        self.assertEqual(sha256_json(left), sha256_json(right))

    def test_canonical_json_rejects_non_finite_numbers(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonical_json_bytes({"value": value})


class ContractTests(unittest.TestCase):
    def test_epistemic_state_values_are_exactly_canonical_cew_values(self) -> None:
        self.assertEqual(
            {item.value for item in EpistemicState},
            {"DOC", "MIS", "RIF", "INF", "INC", "ND"},
        )

    def test_path_classes_include_only_governed_zones(self) -> None:
        self.assertEqual(
            {item.value for item in PathClass},
            {"SOURCE", "BASELINE", "WORKING", "VERIFIED", "ISSUED"},
        )

    def test_approval_receipt_rejects_invalid_sha256(self) -> None:
        with self.assertRaises(ValueError):
            ApprovalReceipt(
                schema="cew.cad.approval.v1",
                approval_id="CEW-CAD-APP-000001",
                changeset_id="CEW-CAD-CS-000001",
                changeset_sha256="not-a-sha",
                document_sha256="0" * 64,
                document_id=1,
                base_revision=1,
                decision="APPROVED",
                approved_by="human",
                approved_at="2026-10-22T04:00:00+02:00",
                signature="AA==",
            )


if __name__ == "__main__":
    unittest.main()
