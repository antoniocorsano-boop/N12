"""ETW-2 Task 2R/3: raster registration for G3 -> G4 comparison.

The registration is a controlled geometric inference used only to compare
homologous document regions. It never promotes structural identity or source
status. SIFT + RANSAC estimates a projective transform at low resolution;
the transform is normalized and reapplied at 300 DPI for evidence crops.

The binary raster difference is used only to build a review queue of geometric
candidates. Candidate extraction does not classify structural change.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium

from model.etwin.document_registry import load_registry

OUT = Path("docs") / "FOGLIO_LAVORO" / "etwin_crops" / "ETW-2" / "G4_G3_registered"
SOURCE_ID = "TAV-04S"  # G3
TARGET_ID = "TAV-05S"  # G4
FIT_DPI = 100
EVIDENCE_DPI = 300
OVERVIEW_BBOX_NORM = (0.45, 0.0, 1.0, 0.65)
DIFF_THRESHOLD = 35
MAX_CANDIDATES = 60


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


def crop_norm(img, bbox):
    x0, y0, x1, y1 = bbox
    h, w = img.shape[:2]
    p = (round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h))
    return img[p[1]:p[3], p[0]:p[2]], p


def extract_difference_candidates(diff_bin: np.ndarray) -> list[dict]:
    """Create a review queue from the binary difference image.

    The queue is intentionally epistemically weak: components are candidate
    locations only. Very small noise and page-edge/fold artifacts are filtered,
    while candidate bboxes remain in the registered G4 overview frame.
    """
    h, w = diff_bin.shape[:2]

    # Remove isolated scan noise and join short nearby strokes only enough to
    # make review regions stable. This is not a structural segmentation.
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    clean = cv2.morphologyEx(diff_bin, cv2.MORPH_OPEN, kernel_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel_close)

    n, labels, stats, centroids = cv2.connectedComponentsWithStats(clean, connectivity=8)
    candidates = []
    overview_x0, overview_y0, overview_x1, overview_y1 = OVERVIEW_BBOX_NORM

    for idx in range(1, n):
        x, y, cw, ch, area = [int(v) for v in stats[idx]]
        if area < 180 or cw < 12 or ch < 12:
            continue
        # Reject page edges / crop borders and long fold-like lines.
        if x <= 6 or y <= 6 or x + cw >= w - 6 or y + ch >= h - 6:
            continue
        if (cw > 0.85 * w and ch < 45) or (ch > 0.85 * h and cw < 45):
            continue

        cx, cy = centroids[idx]
        bbox_overview = [x / w, y / h, (x + cw) / w, (y + ch) / h]
        bbox_page = [
            overview_x0 + bbox_overview[0] * (overview_x1 - overview_x0),
            overview_y0 + bbox_overview[1] * (overview_y1 - overview_y0),
            overview_x0 + bbox_overview[2] * (overview_x1 - overview_x0),
            overview_y0 + bbox_overview[3] * (overview_y1 - overview_y0),
        ]
        candidates.append({
            "candidate_id": f"ETW2-G34-CAND-{idx:03d}",
            "status": "REVIEW_REQUIRED",
            "classification": "UNCLASSIFIED_RASTER_DIFFERENCE",
            "area_px": area,
            "bbox_px_overview": [x, y, x + cw, y + ch],
            "bbox_norm_overview": [round(v, 6) for v in bbox_overview],
            "bbox_norm_page_g4_frame": [round(v, 6) for v in bbox_page],
            "centroid_px_overview": [round(float(cx), 2), round(float(cy), 2)],
            "source": "OVERVIEW_DIFF_THRESHOLD.png",
            "promotion_allowed": False,
        })

    candidates.sort(key=lambda c: c["area_px"], reverse=True)
    return candidates[:MAX_CANDIDATES]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    docs = {d.document_id: d for d in load_registry()}
    src_doc = docs[SOURCE_ID]
    dst_doc = docs[TARGET_ID]

    src_fit = render_gray(src_doc.file_path, FIT_DPI)
    dst_fit = render_gray(dst_doc.file_path, FIT_DPI)
    H_fit, kp_src, kp_dst, good, inliers, ratio, rmse = estimate_homography(src_fit, dst_fit)
    Hn = normalized_homography(H_fit, src_fit.shape, dst_fit.shape)

    src_hi = render_gray(src_doc.file_path, EVIDENCE_DPI)
    dst_hi = render_gray(dst_doc.file_path, EVIDENCE_DPI)
    H_hi = pixel_homography(Hn, src_hi.shape, dst_hi.shape)
    warped_src = cv2.warpPerspective(src_hi, H_hi, (dst_hi.shape[1], dst_hi.shape[0]), borderValue=255)

    target_crop, target_px = crop_norm(dst_hi, OVERVIEW_BBOX_NORM)
    source_crop, source_px = crop_norm(warped_src, OVERVIEW_BBOX_NORM)
    diff = cv2.absdiff(target_crop, source_crop)
    _, diff_bin = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)

    cv2.imwrite(str(OUT / "OVERVIEW_G4_TARGET.png"), target_crop)
    cv2.imwrite(str(OUT / "OVERVIEW_G3_REGISTERED_TO_G4.png"), source_crop)
    cv2.imwrite(str(OUT / "OVERVIEW_ABSDIFF.png"), diff)
    cv2.imwrite(str(OUT / "OVERVIEW_DIFF_THRESHOLD.png"), diff_bin)

    candidates = extract_difference_candidates(diff_bin)
    (OUT / "difference_candidates.json").write_text(
        json.dumps({
            "schema": "ETW2-G3-G4-DIFFERENCE-CANDIDATES-1",
            "status": "REVIEW_REQUIRED",
            "source_registration_status": "INF_CONTROLLED_REGISTRATION",
            "count": len(candidates),
            "candidates": candidates,
            "interpretation": "Candidate locations only; no structural classification or evidence promotion.",
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    changed_fraction = float(np.count_nonzero(diff_bin) / diff_bin.size)
    mean_absdiff = float(diff.mean())

    result = {
        "schema": "ETW2-G3-G4-RASTER-REGISTRATION-2",
        "status": "INF_CONTROLLED_REGISTRATION",
        "source": {"level": "G3", "document_id": SOURCE_ID, "sha256": src_doc.sha256},
        "target": {"level": "G4", "document_id": TARGET_ID, "sha256": dst_doc.sha256},
        "method": "SIFT_RATIO_TEST_RANSAC_HOMOGRAPHY",
        "fit_dpi": FIT_DPI,
        "evidence_dpi": EVIDENCE_DPI,
        "keypoints_source": kp_src,
        "keypoints_target": kp_dst,
        "good_matches": good,
        "inliers": inliers,
        "inlier_ratio": ratio,
        "inlier_rmse_px_at_fit_dpi": rmse,
        "homography_normalized_g3_to_g4": Hn.tolist(),
        "overview_bbox_normalized_g4_frame": list(OVERVIEW_BBOX_NORM),
        "overview_pixel_bbox": list(target_px),
        "mean_absdiff": mean_absdiff,
        "changed_pixel_fraction_threshold35": changed_fraction,
        "difference_candidate_count": len(candidates),
        "difference_candidates_file": str((OUT / "difference_candidates.json").as_posix()),
        "interpretation": "Raster difference is a candidate locator only; structural changes require visual/entity evidence.",
        "identity_promotion": False,
        "property_promotion": False,
    }
    (OUT / "registration_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
