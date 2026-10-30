from __future__ import annotations

from typing import Any, Iterable

PARTIAL = "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES"
THROUGH = "THROUGH_CONTINUOUS"
G1 = "G1_LINE_TRACKS"
RASTER = "RASTER_LOCAL_PROFILE"


def _review_priority(record: dict[str, Any]) -> str | None:
    band = record["transverse_band"]
    evidence = {str(value) for value in band.get("evidence_sources", [])}
    matched = int(band.get("matched_cross_side_pair_count", 0))
    negative = int(band.get("negative_side_count", 0))
    positive = int(band.get("positive_side_count", 0))
    strongest_side = max(negative, positive)

    if matched >= 1 and {G1, RASTER}.issubset(evidence):
        return "A"
    if matched == 0 and {G1, RASTER}.issubset(evidence) and strongest_side >= 3:
        return "B"
    if matched == 0 and RASTER in evidence and G1 not in evidence and strongest_side >= 3:
        return "C"
    return None


def shortlist_prototype_guided_occurrences(
    records: Iterable[dict[str, Any]], excluded_ids: set[str]
) -> list[dict[str, Any]]:
    """Return non-semantic T1/T2 Human Review candidates from existing replay records.

    The function does not alter detector thresholds and does not assign a prototype
    family. It only selects first-pass partial, through-continuous occurrences and
    attaches a deterministic review priority.
    """

    shortlisted: list[dict[str, Any]] = []
    for record in records:
        marker_id = str(record["marker_primitive_id"])
        if marker_id in excluded_ids:
            continue
        band = record["transverse_band"]
        if str(band.get("graphical_state")) != PARTIAL:
            continue
        topology = str(record["carrier_topology"].get("topology_state"))
        if topology != THROUGH:
            continue

        priority = _review_priority(record)
        if priority is None:
            continue

        shortlisted.append(
            {
                "marker_primitive_id": marker_id,
                "review_priority": priority,
                "graphical_state": PARTIAL,
                "topology_state": THROUGH,
                "carrier_orientation": record.get("carrier_orientation"),
                "source_marker_geometry": record.get("source_marker_geometry"),
                "review_marker_geometry": record.get("review_marker_geometry"),
                "carrier_id": record.get("carrier_id"),
                "carrier_track_ids": list(record.get("carrier_track_ids", [])),
                "negative_side_count": int(band.get("negative_side_count", 0)),
                "positive_side_count": int(band.get("positive_side_count", 0)),
                "matched_cross_side_pair_count": int(
                    band.get("matched_cross_side_pair_count", 0)
                ),
                "evidence_sources": sorted(
                    str(value) for value in band.get("evidence_sources", [])
                ),
                "prototype_match_state": "PROTOTYPE_MATCH_PENDING_HUMAN_REVIEW",
                "proposed_graphical_match": None,
                "semantic_classification_authorized": False,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
                "g2c_promotion_authorized": False,
                "g3_authorized": False,
                "merge_authorized": False,
            }
        )

    shortlisted.sort(
        key=lambda item: (str(item["review_priority"]), str(item["marker_primitive_id"]))
    )
    return shortlisted
