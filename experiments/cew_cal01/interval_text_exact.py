from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from experiments.cew_cal01.interval_text_review import build_interval_text_review_manifest


_VALID_SIDES = {"TOP", "RIGHT", "BOTTOM", "LEFT"}


def select_local_carrier_axis(
    profile: Sequence[float],
    *,
    governed_axis_px: float,
    profile_origin_px: float,
) -> dict[str, Any]:
    if not profile:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_PROFILE_EMPTY")
    scores = [float(value) for value in profile]
    max_score = max(scores)
    candidates = [
        float(profile_origin_px) + float(index)
        for index, score in enumerate(scores)
        if score == max_score
    ]
    selected = min(candidates, key=lambda value: (abs(value - float(governed_axis_px)), value))
    return {
        "governed_axis_px": float(governed_axis_px),
        "realigned_axis_px": float(selected),
        "realignment_offset_px": float(selected - float(governed_axis_px)),
        "profile_peak_score": float(max_score),
        "governed_geometry_changed": False,
    }


def build_review_crop_bbox(
    request: dict[str, Any],
    *,
    realigned_axis_px: float,
    image_width: int,
    image_height: int,
) -> list[int]:
    side = str(request.get("side") or "").upper()
    orientation = str(request.get("orientation") or "")
    if side not in _VALID_SIDES:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_SIDE_INVALID")
    expected_orientation = "HORIZONTAL" if side in {"TOP", "BOTTOM"} else "VERTICAL"
    if orientation != expected_orientation:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_ORIENTATION_INVALID")
    if image_width <= 0 or image_height <= 0:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_IMAGE_FRAME_INVALID")

    start = float(request.get("interval_start_px"))
    end = float(request.get("interval_end_px"))
    if end <= start:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_INTERVAL_INVALID")

    policy = dict(request.get("crop_policy") or {})
    inset = int(round(float(policy.get("longitudinal_inset_px", 15))))
    outward = int(round(float(policy.get("outward_depth_px", 220))))
    inward = int(round(float(policy.get("inward_guard_px", 40))))
    if inset < 0 or outward <= 0 or inward < 0:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_CROP_POLICY_INVALID")

    along_start = int(round(start)) + inset
    along_end = int(round(end)) - inset
    if along_end <= along_start:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_INTERVAL_TOO_SHORT")
    axis = int(round(float(realigned_axis_px)))

    if side == "TOP":
        raw = [along_start, axis - outward, along_end, axis + inward]
    elif side == "BOTTOM":
        raw = [along_start, axis - inward, along_end, axis + outward]
    elif side == "LEFT":
        raw = [axis - outward, along_start, axis + inward, along_end]
    else:
        raw = [axis - inward, along_start, axis + outward, along_end]

    left = max(0, min(int(image_width), raw[0]))
    top = max(0, min(int(image_height), raw[1]))
    right = max(0, min(int(image_width), raw[2]))
    bottom = max(0, min(int(image_height), raw[3]))
    if right <= left or bottom <= top:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_CROP_EMPTY")
    return [left, top, right, bottom]


def _carrier_profile(
    *,
    binary: Any,
    request: dict[str, Any],
) -> tuple[list[float], float]:
    import numpy as np

    axis = float(request["carrier_axis_px"])
    radius = int(round(float(request["crop_policy"]["carrier_realign_radius_px"])))
    start = int(round(float(request["interval_start_px"])))
    end = int(round(float(request["interval_end_px"])))
    inset = int(round(float(request["crop_policy"]["longitudinal_inset_px"])))
    along_start = start + inset
    along_end = end - inset
    if along_end <= along_start:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_PROFILE_INTERVAL_EMPTY")

    if request["orientation"] == "HORIZONTAL":
        origin = max(0, int(round(axis)) - radius)
        limit = min(int(binary.shape[0]), int(round(axis)) + radius + 1)
        x0 = max(0, along_start)
        x1 = min(int(binary.shape[1]), along_end)
        slab = binary[origin:limit, x0:x1]
        if slab.size == 0:
            raise ValueError("CAL01_INTERVAL_TEXT_EXACT_PROFILE_EMPTY")
        profile = np.count_nonzero(slab, axis=1).astype(float).tolist()
    else:
        origin = max(0, int(round(axis)) - radius)
        limit = min(int(binary.shape[1]), int(round(axis)) + radius + 1)
        y0 = max(0, along_start)
        y1 = min(int(binary.shape[0]), along_end)
        slab = binary[y0:y1, origin:limit]
        if slab.size == 0:
            raise ValueError("CAL01_INTERVAL_TEXT_EXACT_PROFILE_EMPTY")
        profile = np.count_nonzero(slab, axis=0).astype(float).tolist()
    return profile, float(origin)


def _safe_filename(review_id: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in review_id)


def materialize_interval_text_review_assets(
    *,
    refined: dict[str, Any],
    normalized_gray: Any,
    output_dir: Path,
) -> dict[str, Any]:
    import cv2

    if normalized_gray is None or len(getattr(normalized_gray, "shape", ())) != 2:
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_GRAYSCALE_REQUIRED")

    manifest = build_interval_text_review_manifest(refined)
    _, binary = cv2.threshold(normalized_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    crop_dir = output_dir / "review-crops"
    crop_dir.mkdir(parents=True, exist_ok=True)

    for request in manifest["review_requests"]:
        profile, origin = _carrier_profile(binary=binary, request=request)
        alignment = select_local_carrier_axis(
            profile,
            governed_axis_px=float(request["carrier_axis_px"]),
            profile_origin_px=origin,
        )
        bbox = build_review_crop_bbox(
            request,
            realigned_axis_px=float(alignment["realigned_axis_px"]),
            image_width=int(normalized_gray.shape[1]),
            image_height=int(normalized_gray.shape[0]),
        )
        left, top, right, bottom = bbox
        crop = normalized_gray[top:bottom, left:right]
        rotation = int(request["crop_policy"]["review_rotation_degrees"])
        if rotation == 90:
            crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rotation not in {0}:
            raise ValueError("CAL01_INTERVAL_TEXT_EXACT_ROTATION_UNSUPPORTED")

        filename = _safe_filename(str(request["review_id"])) + ".png"
        path = crop_dir / filename
        if not cv2.imwrite(str(path), crop):
            raise RuntimeError("CAL01_INTERVAL_TEXT_EXACT_CROP_WRITE_FAILED")
        crop_digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        request["local_alignment"] = alignment
        request["crop_bbox_normalized_px"] = bbox
        request["crop_file"] = f"review-crops/{filename}"
        request["crop_sha256"] = crop_digest

    payload = {key: value for key, value in manifest.items() if key != "review_digest"}
    manifest["review_digest"] = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "interval-text-review-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
