#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "analysis" / "source_renders" / "TAV02S"
OUT = ROOT / "analysis" / "pt_raster_candidates"
OUT.mkdir(parents=True, exist_ok=True)

# Mapping derived from the persistent 4x3 tiling used by TAV-02S.
# Global offsets follow the crop register: columns start at 0, 2100, 2280;
# rows start at 0, 2100, 4200, 6209 for the native 4680x8609 raster.
# For each tile we prefer its actual image size; offsets are only used to
# express global pixel coordinates and never metric coordinates.
OFFSETS = {
    "r1_c1": (0, 0), "r1_c2": (2100, 0), "r1_c3": (2280, 0),
    "r2_c1": (0, 2100), "r2_c2": (2100, 2100), "r2_c3": (2280, 2100),
    "r3_c1": (0, 4200), "r3_c2": (2100, 4200), "r3_c3": (2280, 4200),
    "r4_c1": (0, 6209), "r4_c2": (2100, 6209), "r4_c3": (2280, 6209),
}

HEADER = [
    "candidate_id", "tile_id", "u_local_px", "v_local_px", "u_global_px", "v_global_px",
    "bbox_x", "bbox_y", "bbox_w", "bbox_h", "area_px2", "contour_area_px2",
    "aspect_ratio", "rectangularity", "solidity", "source_path", "candidate_status", "note"
]


def score_contour(cnt):
    x, y, w, h = cv2.boundingRect(cnt)
    if w < 10 or h < 10 or w > 220 or h > 220:
        return None
    area = w * h
    if area < 180 or area > 32000:
        return None
    c_area = float(cv2.contourArea(cnt))
    if c_area <= 0:
        return None
    rect = c_area / area
    hull = cv2.convexHull(cnt)
    h_area = float(cv2.contourArea(hull)) or 1.0
    solidity = c_area / h_area
    ar = max(w, h) / max(1.0, min(w, h))
    # Broad filter: retain ordinary columns, elongated piers and possible
    # rectangular support symbols. Semantic classification is deliberately
    # deferred; section callouts may remain among the candidates.
    if ar > 6.0 or rect < 0.18 or solidity < 0.35:
        return None
    return x, y, w, h, area, c_area, ar, rect, solidity


def main():
    rows = []
    tile_files = sorted(SRC.glob("r*_c*.jpg"))
    if len(tile_files) != 12:
        raise SystemExit(f"Expected 12 TAV02S tiles, found {len(tile_files)}")

    for path in tile_files:
        tile_id = path.stem
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"Cannot read {path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Mild denoise followed by adaptive threshold handles uneven scan tone.
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        bw = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 41, 9
        )
        # Close small breaks in scanned rectangle outlines without merging long beams.
        closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
        contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        ox, oy = OFFSETS[tile_id]
        annotated = img.copy()
        accepted = []
        for cnt in contours:
            scored = score_contour(cnt)
            if scored is None:
                continue
            x, y, w, h, area, c_area, ar, rect, solidity = scored
            cx = x + w / 2.0
            cy = y + h / 2.0
            accepted.append((cx, cy, x, y, w, h, area, c_area, ar, rect, solidity))

        # Deduplicate nested contours with nearly identical centers/bboxes.
        accepted.sort(key=lambda z: z[6], reverse=True)
        kept = []
        for a in accepted:
            cx, cy, x, y, w, h, *_ = a
            duplicate = False
            for b in kept:
                bcx, bcy, bx, by, bw_, bh_, *_ = b
                if abs(cx-bcx) <= 4 and abs(cy-bcy) <= 4 and abs(w-bw_) <= 8 and abs(h-bh_) <= 8:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(a)

        kept.sort(key=lambda z: (z[1], z[0]))
        for idx, a in enumerate(kept, start=1):
            cx, cy, x, y, w, h, area, c_area, ar, rect, solidity = a
            cid = f"{tile_id.upper()}-C{idx:04d}"
            rows.append({
                "candidate_id": cid,
                "tile_id": tile_id,
                "u_local_px": f"{cx:.1f}", "v_local_px": f"{cy:.1f}",
                "u_global_px": f"{ox+cx:.1f}", "v_global_px": f"{oy+cy:.1f}",
                "bbox_x": x, "bbox_y": y, "bbox_w": w, "bbox_h": h,
                "area_px2": area, "contour_area_px2": f"{c_area:.1f}",
                "aspect_ratio": f"{ar:.3f}", "rectangularity": f"{rect:.3f}",
                "solidity": f"{solidity:.3f}", "source_path": str(path.relative_to(ROOT)),
                "candidate_status": "AUTO_CANDIDATE_NON_AUTHORITATIVE",
                "note": "Requires semantic binding to support_id; never promote from shape alone",
            })
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 0, 255), 1)
            cv2.circle(annotated, (int(round(cx)), int(round(cy))), 3, (255, 0, 0), -1)
            cv2.putText(annotated, str(idx), (x, max(10, y-3)), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1, cv2.LINE_AA)

        cv2.imwrite(str(OUT / f"{tile_id}_candidates.jpg"), annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])

    with (OUT / "PT_RASTER_GEOMETRIC_CANDIDATES_v1.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)

    with (OUT / "README.txt").open("w", encoding="utf-8") as f:
        f.write(
            "G1-A automatic candidate extraction only.\n"
            "Candidates are NON-AUTHORITATIVE and may include beam-section callouts, text boxes or other rectangles.\n"
            "They must be visually and semantically bound to support IDs before entering PT_PIXEL_SUPPORT_REGISTRY_v1.csv.\n"
            f"candidate_count={len(rows)}\n"
        )
    print(f"candidate_count={len(rows)}")
    print(OUT / "PT_RASTER_GEOMETRIC_CANDIDATES_v1.csv")


if __name__ == "__main__":
    main()
