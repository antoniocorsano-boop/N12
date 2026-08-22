"""Directional ETW probe for local frame additions/removals between adjacent levels.

The probe operates only after controlled raster registration. It separates
source-only and target-only structural ink candidates so that local framed
extensions, terminations and topology overrides can be reviewed explicitly.

Directional raster evidence is a locator only. It must never establish
persistent structural identity, terrace identity, element addition/removal,
or node genealogy without direct source/topology review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

INK_THRESHOLD = 150
DILATION_KERNEL = 7
MIN_COMPONENT_AREA = 500


def directional_mask(subject: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Return dark subject ink not explained by nearby reference ink."""
    subject_ink = subject < INK_THRESHOLD
    reference_ink = reference < INK_THRESHOLD
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (DILATION_KERNEL, DILATION_KERNEL)
    )
    reference_dilated = cv2.dilate(reference_ink.astype(np.uint8), kernel) > 0
    return (subject_ink & ~reference_dilated).astype(np.uint8) * 255


def component_candidates(mask: np.ndarray, prefix: str) -> list[dict]:
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    h, w = mask.shape
    rows: list[dict] = []
    for idx in range(1, n):
        x, y, ww, hh, area = [int(v) for v in stats[idx]]
        if area < MIN_COMPONENT_AREA:
            continue
        rows.append({
            "candidate_id": f"{prefix}-{idx:04d}",
            "area_px": area,
            "bbox_norm_registered_frame": [
                round(x / w, 6), round(y / h, 6),
                round((x + ww) / w, 6), round((y + hh) / h, 6),
            ],
            "review_status": "REVIEW_REQUIRED",
            "structural_classification": "UNRESOLVED",
            "promotion_allowed": False,
        })
    rows.sort(key=lambda r: r["area_px"], reverse=True)
    return rows


def run(registration_dir: Path, pair_code: str) -> dict:
    source_path = registration_dir / "SOURCE_REGISTERED_TO_TARGET.png"
    target_path = registration_dir / "TARGET.png"
    registration_path = registration_dir / "registration_result.json"

    source = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
    target = cv2.imread(str(target_path), cv2.IMREAD_GRAYSCALE)
    if source is None or target is None:
        raise RuntimeError("Registered source/target rasters unavailable")
    if source.shape != target.shape:
        raise RuntimeError(f"Registered raster shape mismatch: {source.shape} vs {target.shape}")

    source_only = directional_mask(source, target)
    target_only = directional_mask(target, source)

    cv2.imwrite(str(registration_dir / "SOURCE_ONLY.png"), source_only)
    cv2.imwrite(str(registration_dir / "TARGET_ONLY.png"), target_only)

    source_candidates = component_candidates(
        source_only, f"ETW2-{pair_code}-SOURCE-ONLY"
    )
    target_candidates = component_candidates(
        target_only, f"ETW2-{pair_code}-TARGET-ONLY"
    )

    registration = {}
    if registration_path.exists():
        registration = json.loads(registration_path.read_text(encoding="utf-8"))

    result = {
        "schema": "ETW2-DIRECTIONAL-FRAME-EXTENSION-PROBE-1",
        "status": "REVIEW_REQUIRED",
        "pair_code": pair_code,
        "registration_status": registration.get("status", "UNKNOWN"),
        "source": registration.get("source"),
        "target": registration.get("target"),
        "method": {
            "ink_threshold": INK_THRESHOLD,
            "reference_dilation_kernel_px": DILATION_KERNEL,
            "minimum_component_area_px": MIN_COMPONENT_AREA,
        },
        "source_only_count": len(source_candidates),
        "target_only_count": len(target_candidates),
        "source_only_candidates": source_candidates,
        "target_only_candidates": target_candidates,
        "interpretation": (
            "Directional components are candidate locators only. A component may be "
            "scan contrast, annotation, section change, beam/column geometry change, "
            "true element addition/removal, or local framed extension. Structural "
            "classification requires direct source/topology review."
        ),
        "identity_promotion": False,
        "terrace_identity_promotion": False,
        "property_promotion": False,
    }
    (registration_dir / "directional_candidates.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "pair_code": pair_code,
        "source_only_count": len(source_candidates),
        "target_only_count": len(target_candidates),
        "identity_promotion": False,
    }, indent=2))
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--registration-dir", required=True)
    p.add_argument("--pair-code", required=True)
    a = p.parse_args()
    run(Path(a.registration_dir), a.pair_code)


if __name__ == "__main__":
    main()
