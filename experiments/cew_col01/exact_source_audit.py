from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
BENCHMARK_IDS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14",
    "15", "16", "17", "18", "19", "20", "21", "22", "22'", "23", "24", "25", "26",
    "27", "28", "29", "30", "31", "32", "33",
]
ELONGATED_IDS = ["18", "23", "30"]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def source_identity_metadata(
    contract: Any,
    materialized: Any,
    binding: Any,
    *,
    zone_set_digest: str,
) -> dict[str, Any]:
    return {
        "repository": contract.repository,
        "commit": contract.commit,
        "path": contract.path,
        "git_blob_sha": contract.git_blob_sha,
        "sha256": materialized.sha256,
        "page_index": contract.page_index,
        "source_role": contract.source_role,
        "raster_width_px": binding.raster_width_px,
        "raster_height_px": binding.raster_height_px,
        "zone_set_digest": zone_set_digest,
    }


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

    eligible_records = [record for record in records if bool(record.get("review_eligible"))]
    observations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in eligible_records:
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
                for record in eligible_records
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
        "eligible_record_count": len(eligible_records),
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


def _adapt_primitive(item: dict[str, Any]) -> dict[str, Any]:
    geometry = item["geometry"]
    return {
        "primitive_id": item["primitive_id"],
        "family": item["family"],
        "x": geometry["x"],
        "y": geometry["y"],
        "width": geometry["width"],
        "height": geometry["height"],
        "feature_signature": item.get("feature_signature", {}),
    }


def _raw_text_anchor_coverage(anchors: list[dict[str, Any]]) -> dict[str, Any]:
    observed = Counter(str(item["normalized_id"]) for item in anchors)
    matched = [identifier for identifier in BENCHMARK_IDS if identifier in observed]
    unmatched = [identifier for identifier in BENCHMARK_IDS if identifier not in observed]
    return {
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "matched_ids": matched,
        "unmatched_ids": unmatched,
        "coverage_fraction": len(matched) / len(BENCHMARK_IDS),
        "duplicate_ids": {
            identifier: count
            for identifier, count in sorted(observed.items(), key=lambda item: _identifier_sort_key(item[0]))
            if count > 1
        },
        "interpretation": "OCR_TEXT_ANCHOR_COVERAGE_ONLY_NOT_COLUMN_IDENTITY",
    }


def _tesseract_tsv(raster_path: Path) -> tuple[str, str]:
    version = subprocess.run(
        ["tesseract", "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0].strip()
    result = subprocess.run(
        ["tesseract", str(raster_path), "stdout", "--psm", "11", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout, version


def _record_sort_key(record: dict[str, Any]) -> tuple[int, int, tuple[int, int, str]]:
    box = record["anchor"]["bbox"]
    return int(box["y"]), int(box["x"]), _identifier_sort_key(str(record["anchor_id"]))


def _build_records(
    tsv_text: str,
    primitives: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from experiments.cew_col01.local_footprint import describe_local_footprint
    from experiments.cew_col01.number_anchor import parse_support_like_tsv

    anchors = parse_support_like_tsv(tsv_text)
    local_primitives = [_adapt_primitive(item) for item in primitives]
    records: list[dict[str, Any]] = []
    for anchor in anchors:
        descriptor = describe_local_footprint(anchor, local_primitives)
        record = {
            **descriptor,
            "anchor": anchor,
            "semantic_meaning": None,
        }
        records.append(record)
    records.sort(key=_record_sort_key)
    return anchors, records


def _review_selection(records: list[dict[str, Any]], benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()

    def add(record: dict[str, Any]) -> None:
        box = record["anchor"]["bbox"]
        key = (str(record["anchor_id"]), int(box["x"]), int(box["y"]))
        if key not in seen and len(selected) < 18:
            seen.add(key)
            selected.append(record)

    for identifier in ELONGATED_IDS:
        for record in records:
            if str(record["anchor_id"]) == identifier:
                add(record)

    for record in records:
        if record["graphical_state"] == "P2_NUMBER_FOOTPRINT_NO_AXES":
            add(record)

    duplicate_ids = set(benchmark.get("duplicate_ids", {}))
    for record in records:
        if str(record["anchor_id"]) in duplicate_ids:
            add(record)

    for record in records:
        if record["graphical_state"] == "P3_NUMBER_PARTIAL_FOOTPRINT":
            add(record)

    for record in records:
        if record["graphical_state"] == "P1_NUMBER_FOOTPRINT_AXES":
            add(record)

    for record in records:
        add(record)
    return selected


def _crop_bounds(record: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    anchor = record["anchor"]["bbox"]
    boxes = [
        (
            float(anchor["x"]),
            float(anchor["y"]),
            float(anchor["width"]),
            float(anchor["height"]),
        )
    ]
    footprint = record.get("footprint")
    if footprint is not None:
        box = footprint["bbox"]
        boxes.append((float(box["x"]), float(box["y"]), float(box["width"]), float(box["height"])))
    x0 = min(box[0] for box in boxes)
    y0 = min(box[1] for box in boxes)
    x1 = max(box[0] + box[2] for box in boxes)
    y1 = max(box[1] + box[3] for box in boxes)
    span = max(x1 - x0, y1 - y0, 60.0)
    margin = max(100.0, span * 1.4)
    return (
        max(0, int(round(x0 - margin))),
        max(0, int(round(y0 - margin))),
        min(width, int(round(x1 + margin))),
        min(height, int(round(y1 + margin))),
    )


def _export_review_package(image: Any, records: list[dict[str, Any]], benchmark: dict[str, Any], out: Path) -> list[dict[str, Any]]:
    import cv2
    import numpy as np

    selected = _review_selection(records, benchmark)
    review_dir = out / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    panels: list[Any] = []
    manifest: list[dict[str, Any]] = []
    height, width = image.shape[:2]
    for index, record in enumerate(selected, start=1):
        left, top, right, bottom = _crop_bounds(record, width, height)
        source_crop = image[top:bottom, left:right].copy()
        panel_id = f"C{index:02d}"
        identifier = str(record["anchor_id"]).replace("'", "prime")
        filename = f"{panel_id.lower()}-id-{identifier}-source-only.png"
        assert cv2.imwrite(str(review_dir / filename), source_crop)

        header_height = 72
        panel = cv2.copyMakeBorder(
            source_crop,
            header_height,
            0,
            0,
            0,
            cv2.BORDER_CONSTANT,
            value=255,
        )
        title = f"{panel_id} | id={record['anchor_id']} | {record['graphical_state']}"
        cv2.putText(panel, title, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.56, 0, 1, cv2.LINE_AA)
        subtitle = f"axes={record['axis_evidence_present']} | human review: COLUMN / NOT / UNCERTAIN / TEXT WRONG"
        cv2.putText(panel, subtitle, (12, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.42, 0, 1, cv2.LINE_AA)
        panels.append(panel)
        manifest.append(
            {
                "panel_id": panel_id,
                "identifier": record["anchor_id"],
                "graphical_state": record["graphical_state"],
                "source_only_crop": f"review/{filename}",
                "crop_bounds_px": {"left": left, "top": top, "right": right, "bottom": bottom},
                "human_decision": "PENDING_HUMAN_REVIEW",
            }
        )

    if panels:
        max_width = max(panel.shape[1] for panel in panels)
        padded = [
            cv2.copyMakeBorder(panel, 0, 0, 0, max_width - panel.shape[1], cv2.BORDER_CONSTANT, value=255)
            if panel.shape[1] < max_width else panel
            for panel in panels
        ]
        atlas = cv2.vconcat(padded)
    else:
        atlas = np.full((180, 1000), 255, dtype=np.uint8)
        cv2.putText(atlas, "CEW-COL-01: no review candidates generated", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2, cv2.LINE_AA)
    assert cv2.imwrite(str(out / "col01-review-atlas.png"), atlas)
    return manifest


def _authority() -> dict[str, bool]:
    return {
        "semantic_classification_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def main() -> None:
    import cv2

    from cew_b01.document_zoning import propose_document_zones
    from cew_b01.evidence_schema import Task3RasterBinding
    from cew_b01.pdf_probe import probe_pdf
    from cew_b01.primitive_census import _analysis_binary, _confirmed_analysis_mask, extract_neutral_primitives
    from cew_b01.source_contract import load_source_contract, materialize_source
    from cew_b01.zone_review_package import confirmed_zones_from_receipt, zone_set_digest

    runner_temp = Path(os.environ["RUNNER_TEMP"])
    out = Path("evidence/cew-col01/number-anchored-column-recovery")
    out.mkdir(parents=True, exist_ok=True)

    contract = load_source_contract("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
    materialized = materialize_source(contract, ".", runner_temp / "tavola5-col01-source.pdf")
    assert materialized.sha256 == SOURCE_SHA256

    probe_dir = runner_temp / "cew-col01-probe"
    probe = probe_pdf(materialized, probe_dir)
    binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())
    raster_path = probe_dir / "tav5-page0-300dpi.png"

    proposed_zones = propose_document_zones(binding, raster_path)
    zone_receipt = json.loads(
        Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_REVIEW_v1.json").read_text(encoding="utf-8")
    )
    zones = confirmed_zones_from_receipt(binding, proposed_zones, zone_receipt)
    assert all(zone.human_confirmed for zone in zones)
    assert zone_set_digest(zones) == zone_receipt["zone_set_digest"]

    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    assert image is not None
    mask = _confirmed_analysis_mask(binding, zones)
    analysis, _binary = _analysis_binary(image, mask)
    ocr_path = runner_temp / "cew-col01-structural-workarea.png"
    assert cv2.imwrite(str(ocr_path), analysis)

    primitives_a = [item.to_mapping() for item in extract_neutral_primitives(binding, raster_path, zones)]
    primitives_b = [item.to_mapping() for item in extract_neutral_primitives(binding, raster_path, zones)]
    assert canonical_bytes(primitives_a) == canonical_bytes(primitives_b)

    tsv_a, tesseract_version_a = _tesseract_tsv(ocr_path)
    tsv_b, tesseract_version_b = _tesseract_tsv(ocr_path)
    assert tesseract_version_a == tesseract_version_b

    anchors_a, records_a = _build_records(tsv_a, primitives_a)
    anchors_b, records_b = _build_records(tsv_b, primitives_b)
    replay_a = {"anchors": anchors_a, "records": records_a}
    replay_b = {"anchors": anchors_b, "records": records_b}
    assert canonical_bytes(replay_a) == canonical_bytes(replay_b)

    benchmark = evaluate_benchmark(records_a, benchmark_ids=BENCHMARK_IDS, elongated_ids=ELONGATED_IDS)
    raw_coverage = _raw_text_anchor_coverage(anchors_a)
    state_counts = dict(sorted(Counter(record["graphical_state"] for record in records_a).items()))
    review_manifest = _export_review_package(image, records_a, benchmark, out)

    for record in records_a:
        assert record["semantic_meaning"] is None
        assert all(value is False for value in record["authority"].values())

    source_metadata = source_identity_metadata(
        contract,
        materialized,
        binding,
        zone_set_digest=zone_receipt["zone_set_digest"],
    )
    payload = {
        "schema_id": "CEW_COL01_NUMBER_ANCHORED_COLUMN_RECOVERY_EXACT_SOURCE",
        "schema_version": 1,
        "status": "H_COL_01_AUDIT_READY_FOR_HUMAN_REVIEW",
        "source": source_metadata,
        "toolchain": {"tesseract": tesseract_version_a},
        "candidate_generation": {
            "starts_from_exact_source_ocr": True,
            "historical_ids_used_to_generate_candidates": False,
            "symmetry_axes_required": False,
            "raw_text_anchor_count": len(anchors_a),
            "graphical_state_counts": state_counts,
        },
        "raw_text_anchor_benchmark": raw_coverage,
        "footprint_supported_benchmark": benchmark,
        "hypothesis": {
            "id": "H-COL-01",
            "status": benchmark["h_col_01_status"],
            "threshold_fraction": 0.90,
            "meaning": "EXPERIMENTAL_PROJECT_HYPOTHESIS_ONLY",
            "engineering_fact_authorized": False,
        },
        "review_panels": review_manifest,
        "records": records_a,
        "authority": _authority(),
    }
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    payload["replay_sha256"] = digest
    (out / "col01-audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": payload["status"],
        "source_sha256": materialized.sha256,
        "tesseract": tesseract_version_a,
        "raw_text_anchor_count": len(anchors_a),
        "raw_text_anchor_coverage": raw_coverage["coverage_fraction"],
        "footprint_supported_coverage": benchmark["coverage_fraction"],
        "h_col_01_status": benchmark["h_col_01_status"],
        "matched_ids": benchmark["matched_ids"],
        "unmatched_ids": benchmark["unmatched_ids"],
        "elongated_witnesses": benchmark["elongated_witnesses"],
        "graphical_state_counts": state_counts,
        "review_panel_count": len(review_manifest),
        "replay_sha256": digest,
        "authority": _authority(),
    }
    print("CEW_COL01_EXACT_SOURCE_AUDIT=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
