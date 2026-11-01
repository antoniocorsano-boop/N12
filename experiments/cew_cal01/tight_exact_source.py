from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from experiments.cew_cal01.exact_source import SOURCE_SHA256
from experiments.cew_cal01.oriented_discovery import (
    _map_oriented_bbox_to_page,
    _prepare_for_numeric_ocr,
    _rotate_image,
    _run_numeric_tesseract,
)
from experiments.cew_cal01.semantic_exact_source import select_confirmation_token
from experiments.cew_cal01.tight_confirmation import (
    build_tight_confirmation_plan,
    select_diverse_tight_consensus,
)


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "primary_anchor_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def select_tight_replay_cluster_indices(semantic_replay: Mapping[str, Any]) -> list[int]:
    """Select only clusters unresolved because OCR consensus is insufficient."""

    results = semantic_replay.get("results")
    if not isinstance(results, list):
        raise ValueError("CAL01_TIGHT_SEMANTIC_RESULTS_REQUIRED")

    seen: set[int] = set()
    selected: list[int] = []
    for row in results:
        if not isinstance(row, Mapping):
            raise ValueError("CAL01_TIGHT_SEMANTIC_ROW_INVALID")
        try:
            index = int(row["cluster_index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("CAL01_TIGHT_SEMANTIC_CLUSTER_INDEX_REQUIRED") from exc
        if index < 0:
            raise ValueError("CAL01_TIGHT_SEMANTIC_CLUSTER_INDEX_INVALID")
        if index in seen:
            raise ValueError("CAL01_TIGHT_SEMANTIC_CLUSTER_DUPLICATE")
        seen.add(index)
        if str(row.get("reason") or "") == "OCR_CONSENSUS_INSUFFICIENT":
            selected.append(index)

    selected.sort()
    return selected


def build_tight_replay_manifest(
    *,
    source: Mapping[str, Any],
    rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Freeze tight-local OCR replay evidence without creating metric authority."""

    source_sha = str(source.get("sha256") or "").strip()
    if source_sha != SOURCE_SHA256:
        raise ValueError("CAL01_TIGHT_SOURCE_DIGEST_DRIFT")
    page_index = source.get("page_index")
    if isinstance(page_index, bool) or int(page_index) != 0:
        raise ValueError("CAL01_TIGHT_SOURCE_PAGE_DRIFT")

    ordered: list[dict[str, Any]] = []
    seen_indices: set[int] = set()
    for raw in rows:
        row = dict(raw)
        try:
            index = int(row["cluster_index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("CAL01_TIGHT_CLUSTER_INDEX_REQUIRED") from exc
        if index < 0 or index in seen_indices:
            raise ValueError("CAL01_TIGHT_CLUSTER_INDEX_INVALID")
        seen_indices.add(index)
        row["cluster_index"] = index

        bbox = row.get("target_bbox_px")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("CAL01_TIGHT_TARGET_BBOX_REQUIRED")
        left, top, right, bottom = (float(value) for value in bbox)
        if left < 0 or top < 0 or right <= left or bottom <= top:
            raise ValueError("CAL01_TIGHT_TARGET_BBOX_INVALID")
        row["target_bbox_px"] = [left, top, right, bottom]

        rotation = int(row.get("ocr_rotation_degrees")) % 360
        if rotation not in {0, 90, 180, 270}:
            raise ValueError("CAL01_TIGHT_ROTATION_INVALID")
        row["ocr_rotation_degrees"] = rotation

        pass_count = int(row.get("pass_count", 0))
        observation_count = int(row.get("observation_count", 0))
        if pass_count < 0 or observation_count < 0 or observation_count > pass_count:
            raise ValueError("CAL01_TIGHT_REPLAY_COUNTS_INVALID")
        row["pass_count"] = pass_count
        row["observation_count"] = observation_count

        consensus = row.get("consensus")
        if not isinstance(consensus, dict) or not isinstance(consensus.get("confirmed"), bool):
            raise ValueError("CAL01_TIGHT_CONSENSUS_REQUIRED")
        if consensus["confirmed"] and not str(consensus.get("text") or "").strip():
            raise ValueError("CAL01_TIGHT_CONFIRMED_TEXT_REQUIRED")

        row["primary_anchor_authorized"] = False
        row["canonical_geometry_authorized"] = False
        row["canonical_write_authorized"] = False
        row["engineering_authority_effect"] = "NONE"
        ordered.append(row)

    ordered.sort(key=lambda item: item["cluster_index"])
    confirmed_texts = [
        str(row["consensus"]["text"])
        for row in ordered
        if row["consensus"].get("confirmed") is True
    ]
    confirmed_counts = dict(sorted(Counter(confirmed_texts).items()))

    result = {
        "schema": "CEW_CAL01_TIGHT_EXACT_SOURCE_REPLAY_v1",
        "program": "CEW-CAL-01",
        "source": {
            "sha256": SOURCE_SHA256,
            "page_index": 0,
        },
        "cluster_count": len(ordered),
        "tight_consensus_confirmed_count": len(confirmed_texts),
        "confirmed_text_counts": confirmed_counts,
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "rows": ordered,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["tight_replay_digest"] = _canonical_digest(result)
    return result


def _prepare_tight_image(gray: Any, preprocess_mode: str) -> Any:
    import cv2

    if preprocess_mode == "RAW_GRAYSCALE":
        return gray
    if preprocess_mode == "LINE_SUPPRESSED":
        return _prepare_for_numeric_ocr(gray)
    if preprocess_mode == "BINARY_OTSU":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    raise ValueError("CAL01_TIGHT_PREPROCESS_MODE_UNSUPPORTED")


def _run_tight_cluster(gray: Any, cluster_index: int, cluster: Mapping[str, Any]) -> dict[str, Any]:
    import cv2

    height, width = gray.shape[:2]
    plan = build_tight_confirmation_plan(dict(cluster), page_width=width, page_height=height)
    representative = cluster.get("representative") or {}
    target_bbox = representative.get("bbox_px")
    rotation = representative.get("ocr_rotation_degrees")
    if not isinstance(target_bbox, (list, tuple)) or len(target_bbox) != 4:
        raise RuntimeError("CAL01_TIGHT_TARGET_BBOX_REQUIRED")
    if rotation is None:
        raise RuntimeError("CAL01_TIGHT_ROTATION_REQUIRED")

    observations: list[dict[str, Any]] = []
    for pass_index, item in enumerate(plan):
        raw_crop = item["crop_bbox_px"]
        left = max(0, int(round(float(raw_crop[0]))))
        top = max(0, int(round(float(raw_crop[1]))))
        right = min(width, int(round(float(raw_crop[2]))))
        bottom = min(height, int(round(float(raw_crop[3]))))
        if right <= left or bottom <= top:
            raise RuntimeError("CAL01_TIGHT_CROP_INVALID")
        crop = gray[top:bottom, left:right]
        prepared = _prepare_tight_image(crop, str(item["preprocess_mode"]))
        oriented = _rotate_image(prepared, int(item["rotation_degrees"]))
        scale = float(item["ocr_scale"])
        oriented = cv2.resize(
            oriented,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )

        mapped_tokens: list[dict[str, Any]] = []
        for token in _run_numeric_tesseract(oriented, psm=int(item["psm"])):
            page_bbox = _map_oriented_bbox_to_page(
                token["bbox_px"],
                tile_bounds=(left, top, right, bottom),
                rotation_degrees=int(item["rotation_degrees"]),
                ocr_scale=scale,
            )
            mapped_tokens.append(
                {
                    "text": str(token["text"]),
                    "confidence": float(token.get("confidence", 0.0)),
                    "bbox_px": page_bbox,
                }
            )
        selected = select_confirmation_token(mapped_tokens, target_bbox_px=list(target_bbox))
        if selected is None:
            continue
        observations.append(
            {
                "text": str(selected["text"]),
                "confidence": float(selected.get("confidence", 0.0)),
                "bbox_px": [float(value) for value in selected["bbox_px"]],
                "preprocess_mode": str(item["preprocess_mode"]),
                "psm": int(item["psm"]),
                "rotation_degrees": int(item["rotation_degrees"]),
                "ocr_scale": scale,
                "pass_index": pass_index,
                "scope": "TIGHT_LOCAL_SAME_SOURCE_LOCATION",
            }
        )

    consensus = select_diverse_tight_consensus(
        observations,
        minimum_families=3,
        minimum_margin=1,
    )
    return {
        "cluster_index": int(cluster_index),
        "target_bbox_px": [float(value) for value in target_bbox],
        "ocr_rotation_degrees": int(rotation) % 360,
        "pass_count": len(plan),
        "observation_count": len(observations),
        "consensus": consensus,
        "observations": observations,
    }


def run_tight_exact_source_replay(
    *,
    image_path: Path,
    oriented_discovery_path: Path,
    semantic_replay_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    import cv2

    oriented = json.loads(oriented_discovery_path.read_text(encoding="utf-8"))
    semantic = json.loads(semantic_replay_path.read_text(encoding="utf-8"))
    if oriented.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_TIGHT_ORIENTED_SOURCE_DIGEST_DRIFT")
    if semantic.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_TIGHT_SEMANTIC_SOURCE_DIGEST_DRIFT")
    for payload in (oriented, semantic):
        if payload.get("historical_comparator_loaded") is not False:
            raise RuntimeError("CAL01_TIGHT_HISTORICAL_COMPARATOR_FORBIDDEN")
        if payload.get("historical_affine_loaded") is not False:
            raise RuntimeError("CAL01_TIGHT_HISTORICAL_AFFINE_FORBIDDEN")
        if payload.get("tav02s_evidence_loaded") is not False:
            raise RuntimeError("CAL01_TIGHT_TAV02S_FORBIDDEN")

    clusters = oriented.get("location_clusters")
    if not isinstance(clusters, list) or not clusters:
        raise RuntimeError("CAL01_TIGHT_LOCATION_CLUSTERS_REQUIRED")
    selected_indices = select_tight_replay_cluster_indices(semantic)

    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError("CAL01_TIGHT_RASTER_UNREADABLE")

    rows: list[dict[str, Any]] = []
    for index in selected_indices:
        if index >= len(clusters):
            raise RuntimeError("CAL01_TIGHT_CLUSTER_INDEX_OUT_OF_RANGE")
        rows.append(_run_tight_cluster(gray, index, clusters[index]))

    manifest = build_tight_replay_manifest(source=oriented["source"], rows=rows)
    manifest["selection_reason"] = "SEMANTIC_REASON_OCR_CONSENSUS_INSUFFICIENT_ONLY"
    manifest["semantic_replay_digest"] = semantic.get("semantic_replay_digest")
    manifest["oriented_discovery_digest"] = oriented.get("oriented_discovery_digest")
    manifest["tight_replay_digest"] = _canonical_digest({
        key: value for key, value in manifest.items() if key != "tight_replay_digest"
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tight-exact-source-replay.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--oriented-discovery", required=True)
    parser.add_argument("--semantic-replay", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_tight_exact_source_replay(
        image_path=Path(args.image),
        oriented_discovery_path=Path(args.oriented_discovery),
        semantic_replay_path=Path(args.semantic_replay),
        output_dir=Path(args.output_dir),
    )
    print(json.dumps({
        "cluster_count": result["cluster_count"],
        "tight_consensus_confirmed_count": result["tight_consensus_confirmed_count"],
        "confirmed_text_counts": result["confirmed_text_counts"],
        "tight_replay_digest": result["tight_replay_digest"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
