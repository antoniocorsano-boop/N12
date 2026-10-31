#!/usr/bin/env python3
from __future__ import annotations

from build_cew_col02_mobile_manifest import select_residual_occurrences


def _search() -> dict:
    return {
        "review_panels": [
            {"panel_id": "S01", "candidate_id": "COL02-FP-0001", "bbox": {"x": 0.10, "y": 0.10, "width": 0.05, "height": 0.05}},
            {"panel_id": "S02", "candidate_id": "COL02-FP-0002", "bbox": {"x": 0.40, "y": 0.10, "width": 0.05, "height": 0.05}},
        ]
    }


def _sweep() -> dict:
    return {
        "panels": [
            {
                "panel_id": "S01",
                "target_candidate_id": "COL02-FP-0001",
                "visible_sibling_candidates": [
                    {
                        "candidate_id": "COL02-FP-0100",
                        "bbox": {"x": 0.16, "y": 0.12, "width": 0.04, "height": 0.04},
                        "score": 0.81,
                        "visible_fraction_in_crop": 0.72,
                    },
                    {
                        "candidate_id": "COL02-FP-0002",
                        "bbox": {"x": 0.40, "y": 0.10, "width": 0.05, "height": 0.05},
                        "score": 0.90,
                        "visible_fraction_in_crop": 0.95,
                    },
                ],
            },
            {
                "panel_id": "S02",
                "target_candidate_id": "COL02-FP-0002",
                "visible_sibling_candidates": [
                    {
                        "candidate_id": "COL02-FP-0100",
                        "bbox": {"x": 0.17, "y": 0.13, "width": 0.04, "height": 0.04},
                        "score": 0.84,
                        "visible_fraction_in_crop": 0.88,
                    },
                    {
                        "candidate_id": "COL02-FP-0200",
                        "bbox": {"x": 0.46, "y": 0.14, "width": 0.04, "height": 0.04},
                        "score": 0.79,
                        "visible_fraction_in_crop": 0.76,
                    },
                ],
            },
        ]
    }


def main() -> int:
    residuals = select_residual_occurrences(_search(), _sweep())
    assert [item["candidate_id"] for item in residuals] == ["COL02-FP-0100", "COL02-FP-0200"]

    first = residuals[0]
    assert first["source_panel_id"] == "S02", "duplicate residual must use the most visible occurrence"
    assert first["context_target_candidate_id"] == "COL02-FP-0002"
    assert first["target_bbox"] == {"x": 0.17, "y": 0.13, "width": 0.04, "height": 0.04}
    assert first["visible_fraction_in_crop"] == 0.88

    ids = {item["candidate_id"] for item in residuals}
    assert "COL02-FP-0001" not in ids
    assert "COL02-FP-0002" not in ids, "already-reviewed S01-S24 targets must never re-enter residual review"
    assert len(ids) == len(residuals), "residual candidates must be unique"

    print("CEW_COL02_MOBILE_ADAPTER_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
