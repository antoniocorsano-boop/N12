"""Generic ETW-2 controlled raster registration for adjacent floor pairs.

This module is a comparison aid only. It estimates a projective transform,
creates registered raster evidence and a review-only difference-candidate queue.
It never promotes structural identity or canonical properties.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium

from model.etwin.document_registry import load_registry

FIT_DPI = 100
EVIDENCE_DPI = 300
DIFF_THRESHOLD = 35
MIN_COMPONENT_AREA = 1200


def render_gray(path: str, dpi: int) -> np.ndarray:
    pdf = pdfium.PdfDocument(path)
    page = pdf[0]
    img = np.array(page.render(scale=dpi / 72.0).to_pil().convert("L"))
    pdf.close()
    return img


def estimate_homography(src: np.ndarray, dst: np.ndarray):
    sift = cv2.SIFT_create(nfeatures=12000, contrastThreshold=0.015, edgeThreshold=10)
    kp1, des1 = sift.detectAndCompute(src, None)
    kp2, des2 = sift.detectAndCompute(dst, None)
    if des1 is None or des2 is None:
        raise RuntimeError("SIFT descriptors unavailable")
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    raw = matcher.knnMatch(des1, des2, k=2)
    good = [m for m, n in raw if m.distance < 0.72 * n.distance]
    if len(good) < 20:
        raise RuntimeError(f"Insufficient feature matches: {len(good)}")
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 6.0, maxIters=10000, confidence=0.999)
    if H is None or mask is None:
        raise RuntimeError("Homography estimation failed")
    inliers = mask.ravel().astype(bool)
    inlier_count = int(inliers.sum())
    ratio = inlier_count / len(good)
    if inlier_count < 20 or ratio < 0.20:
        raise RuntimeError(f"Weak registration: inliers={inlier_count}, ratio={ratio:.3f}")
    pred = cv2.perspectiveTransform(src_pts[inliers], H)
    err = np.linalg.norm(pred - dst_pts[inliers], axis=2).ravel()
    rmse = float(np.sqrt(np.mean(err ** 2)))
    return H, len(kp1), len(kp2), len(good), inlier_count, ratio, rmse


def normalized_homography(H_px, src_shape, dst_shape):
    hs, ws = src_shape
    ht, wt = dst_shape
    Ds = np.array([[ws, 0, 0], [0, hs, 0], [0, 0, 1]], dtype=np.float64)
    Dt = np.array([[wt, 0, 0], [0, ht, 0], [0, 0, 1]], dtype=np.float64)
    Hn = np.linalg.inv(Dt) @ H_px @ Ds
    return Hn / Hn[2, 2]


def pixel_homography(Hn, src_shape, dst_shape):
    hs, ws = src_shape
    ht, wt = dst_shape
    Ds = np.array([[ws, 0, 0], [0, hs, 0], [0, 0, 1]], dtype=np.float64)
    Dt = np.array([[wt, 0, 0], [0, ht, 0], [0, 0, 1]], dtype=np.float64)
    H = Dt @ Hn @ np.linalg.inv(Ds)
    return H / H[2, 2]


def component_candidates(diff_bin: np.ndarray, target_shape, pair_code: str):
    n, labels, stats, _ = cv2.connectedComponentsWithStats(diff_bin, 8)
    h, w = target_shape
    rows = []
    for idx in range(1, n):
        x, y, ww, hh, area = [int(v) for v in stats[idx]]
        if area < MIN_COMPONENT_AREA:
            continue
        rows.append({
            "candidate_id": f"ETW2-{pair_code}-CAND-{idx:03d}",
            "area_px": area,
            "bbox_norm_target_frame": [round(x / w, 6), round(y / h, 6), round((x + ww) / w, 6), round((y + hh) / h, 6)],
            "review_status": "REVIEW_REQUIRED",
            "promotion_allowed": False,
        })
    rows.sort(key=lambda r: r["area_px"], reverse=True)
    return rows


def run(source_level: str, source_id: str, target_level: str, target_id: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = {d.document_id: d for d in load_registry()}
    src_doc = docs[source_id]
    dst_doc = docs[target_id]

    src_fit = render_gray(src_doc.file_path, FIT_DPI)
    dst_fit = render_gray(dst_doc.file_path, FIT_DPI)
    H_fit, kp_src, kp_dst, good, inliers, ratio, rmse = estimate_homography(src_fit, dst_fit)
    Hn = normalized_homography(H_fit, src_fit.shape, dst_fit.shape)

    src_hi = render_gray(src_doc.file_path, EVIDENCE_DPI)
    dst_hi = render_gray(dst_doc.file_path, EVIDENCE_DPI)
    H_hi = pixel_homography(Hn, src_hi.shape, dst_hi.shape)
    warped_src = cv2.warpPerspective(src_hi, H_hi, (dst_hi.shape[1], dst_hi.shape[0]), borderValue=255)

    diff = cv2.absdiff(dst_hi, warped_src)
    _, diff_bin = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)

    cv2.imwrite(str(out_dir / "TARGET.png"), dst_hi)
    cv2.imwrite(str(out_dir / "SOURCE_REGISTERED_TO_TARGET.png"), warped_src)
    cv2.imwrite(str(out_dir / "ABSDIFF.png"), diff)
    cv2.imwrite(str(out_dir / "DIFF_THRESHOLD.png"), diff_bin)

    pair_code = f"G{source_level[-1]}{target_level[-1]}" if source_level.startswith("G") and target_level.startswith("G") else f"{source_level}{target_level}"
    candidates = component_candidates(diff_bin, dst_hi.shape, pair_code)

    result = {
        "schema": "ETW2-FLOOR-PAIR-REGISTRATION-1",
        "status": "INF_CONTROLLED_REGISTRATION",
        "source": {"level": source_level, "document_id": source_id, "sha256": src_doc.sha256},
        "target": {"level": target_level, "document_id": target_id, "sha256": dst_doc.sha256},
        "method": "SIFT_RATIO_TEST_RANSAC_HOMOGRAPHY",
        "fit_dpi": FIT_DPI,
        "evidence_dpi": EVIDENCE_DPI,
        "good_matches": good,
        "inliers": inliers,
        "inlier_ratio": ratio,
        "inlier_rmse_px_at_fit_dpi": rmse,
        "homography_normalized_source_to_target": Hn.tolist(),
        "candidate_count": len(candidates),
        "identity_promotion": False,
        "property_promotion": False,
    }
    (out_dir / "registration_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "difference_candidates.json").write_text(json.dumps({
        "schema": "ETW2-FLOOR-PAIR-DIFFERENCE-CANDIDATES-1",
        "status": "REVIEW_REQUIRED",
        "count": len(candidates),
        "candidates": candidates,
        "interpretation": "Candidate locator only; visual/entity evidence required for structural classification.",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-level", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--target-level", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    run(a.source_level, a.source_id, a.target_level, a.target_id, Path(a.out))


if __name__ == "__main__":
    main()
