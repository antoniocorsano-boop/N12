from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


def _identifier_sort_key(value: str) -> tuple[int, int, str]:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    number = int(digits) if digits else 10**9
    apostrophe = 1 if text.endswith("'") else 0
    return number, apostrophe, text


def evaluate_benchmark(
    records: list[dict[str, Any]],
    *,
    benchmark_ids: Iterable[str],
    elongated_ids: Iterable[str],
) -> dict[str, Any]:
    benchmark = sorted({str(value) for value in benchmark_ids}, key=_identifier_sort_key)
    elongated = sorted({str(value) for value in elongated_ids}, key=_identifier_sort_key)

    observations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        identifier = record.get("anchor_id")
        if identifier is None:
            continue
        value = str(identifier)
        if value:
            observations[value].append(record)

    matched = [identifier for identifier in benchmark if identifier in observations]
    unmatched = [identifier for identifier in benchmark if identifier not in observations]
    duplicate_ids = {
        identifier: count
        for identifier, count in sorted(
            Counter(
                str(record.get("anchor_id"))
                for record in records
                if record.get("anchor_id") is not None
            ).items(),
            key=lambda item: _identifier_sort_key(item[0]),
        )
        if count > 1
    }

    if not benchmark:
        coverage_fraction: float | None = None
        status = "UNVERIFIED"
    else:
        coverage_fraction = len(matched) / len(benchmark)
        status = "SUPPORTED" if coverage_fraction >= 0.90 else "REJECTED"

    elongated_witnesses = []
    for identifier in elongated:
        items = observations.get(identifier, [])
        elongated_witnesses.append(
            {
                "identifier": identifier,
                "observation_count": len(items),
                "graphical_states": sorted(
                    {
                        str(item.get("graphical_state"))
                        for item in items
                        if item.get("graphical_state") is not None
                    }
                ),
            }
        )

    return {
        "benchmark_count": len(benchmark),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "matched_ids": matched,
        "unmatched_ids": unmatched,
        "duplicate_ids": duplicate_ids,
        "coverage_fraction": coverage_fraction,
        "h_col_01_status": status,
        "engineering_fact_authorized": False,
        "elongated_witnesses": elongated_witnesses,
    }
