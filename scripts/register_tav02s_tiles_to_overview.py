#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "analysis" / "source_renders" / "TAV02S"
OUT = ROOT / "data" / "canonical" / "TAV02S_TILE_TO_NATIVE_REGISTRATION_v1.csv"
NATIVE_W, NATIVE_H = 4680, 8609


def project_corners(H, w, h):
    pts = np.float32([[[0, 0]], [[w, 0]], [[w, h]], [[0, h]]])
    return cv2.perspectiveTransform(pts, H).reshape(-1, 2)


def main():
    overview = cv2.imread(str(SRC / "overview.jpg"), cv2.IMREAD_GRAYSCALE)
    if overview is None:
        raise SystemExit("missing overview.jpg")
    oh, ow = overview.shape
    sx, sy = NATIVE_W / ow, NATIVE_H / oh

    sift = cv2.SIFT_create(nfeatures=5000)
    kp_o, des_o = sift.detectAndCompute(overview, None)
    matcher = cv2.BFMatcher()
    records = []

    for path in sorted(SRC.glob("r*_c*.jpg")):
        tile = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        h, w = tile.shape
        kp, des = sift.detectAndCompute(tile, None)
        H = None
        good_n = inlier_n = 0
        rmse = math.nan
        status = "UNREGISTERED"
        if des is not None and len(kp) >= 4:
            matches = matcher.knnMatch(des, des_o, k=2)
            good = [m for m, n in matches if m.distance < 0.72 * n.distance]
            good_n = len(good)
            if good_n >= 4:
                src = np.float32([kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                dst = np.float32([kp_o[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
                if H is not None and mask is not None:
                    inliers = mask.ravel().astype(bool)
                    inlier_n = int(inliers.sum())
                    pred = cv2.perspectiveTransform(src, H)
                    err = np.linalg.norm(pred - dst, axis=2).ravel()
                    if inlier_n:
                        rmse = float(np.sqrt(np.mean(err[inliers] ** 2)))
                    if inlier_n >= 10:
                        status = "DIRECT_SIFT_RANSAC"
        records.append({"tile_id": path.stem, "w": w, "h": h, "H": H, "status": status,
                        "good": good_n, "inliers": inlier_n, "rmse": rmse})

    extents = {}
    for r in records:
        if r["status"] == "DIRECT_SIFT_RANSAC":
            p = project_corners(r["H"], r["w"], r["h"])
            extents[r["tile_id"]] = (p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max())

    col_bounds = {}
    row_bounds = {}
    for c in (1, 2, 3):
        vals = [v for k, v in extents.items() if k.endswith(f"c{c}")]
        col_bounds[c] = (float(np.median([v[0] for v in vals])), float(np.median([v[1] for v in vals])))
    for rr in (1, 2, 3, 4):
        vals = [v for k, v in extents.items() if k.startswith(f"r{rr}_")]
        row_bounds[rr] = (float(np.median([v[2] for v in vals])), float(np.median([v[3] for v in vals])))

    for r in records:
        if r["status"] != "DIRECT_SIFT_RANSAC":
            rr, cc = int(r["tile_id"][1]), int(r["tile_id"][4])
            xmin, xmax = col_bounds[cc]
            ymin, ymax = row_bounds[rr]
            r["H"] = np.array([[(xmax-xmin)/r["w"], 0, xmin], [0, (ymax-ymin)/r["h"], ymin], [0, 0, 1]], dtype=float)
            r["status"] = "DERIVED_GRID_FROM_REGISTERED_NEIGHBORS"

    fields = ["tile_id","tile_w_px","tile_h_px","registration_status","good_matches","inliers","rmse_overview_px",
              "h00","h01","h02","h10","h11","h12","h20","h21","h22",
              "overview_xmin","overview_xmax","overview_ymin","overview_ymax",
              "native_u_min","native_u_max","native_v_min","native_v_max",
              "native_scale_x_per_overview_px","native_scale_y_per_overview_px","authority","note"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        for r in records:
            H = r["H"]
            p = project_corners(H, r["w"], r["h"])
            pn = np.column_stack([p[:,0]*sx, p[:,1]*sy])
            wr.writerow({
                "tile_id": r["tile_id"], "tile_w_px": r["w"], "tile_h_px": r["h"],
                "registration_status": r["status"], "good_matches": r["good"], "inliers": r["inliers"],
                "rmse_overview_px": "" if math.isnan(r["rmse"]) else f"{r['rmse']:.4f}",
                "h00": f"{H[0,0]:.10f}", "h01": f"{H[0,1]:.10f}", "h02": f"{H[0,2]:.10f}",
                "h10": f"{H[1,0]:.10f}", "h11": f"{H[1,1]:.10f}", "h12": f"{H[1,2]:.10f}",
                "h20": f"{H[2,0]:.12g}", "h21": f"{H[2,1]:.12g}", "h22": f"{H[2,2]:.10f}",
                "overview_xmin": f"{p[:,0].min():.3f}", "overview_xmax": f"{p[:,0].max():.3f}",
                "overview_ymin": f"{p[:,1].min():.3f}", "overview_ymax": f"{p[:,1].max():.3f}",
                "native_u_min": f"{pn[:,0].min():.2f}", "native_u_max": f"{pn[:,0].max():.2f}",
                "native_v_min": f"{pn[:,1].min():.2f}", "native_v_max": f"{pn[:,1].max():.2f}",
                "native_scale_x_per_overview_px": f"{sx:.10f}", "native_scale_y_per_overview_px": f"{sy:.10f}",
                "authority": "REGISTRATION_MEASURED" if r["status"] == "DIRECT_SIFT_RANSAC" else "REGISTRATION_DERIVED",
                "note": "tile-local -> overview homography; overview -> native by exact image-size scale"
            })
    print(OUT)

if __name__ == "__main__":
    main()
