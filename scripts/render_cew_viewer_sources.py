#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import fitz


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--source", nargs=3, action="append", metavar=("CODE","PDF","SHA256"), required=True)
    args = ap.parse_args()
    if args.dpi < 300:
        raise AssertionError("CEW F3 technical source render must be >=300 dpi")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for code, pdf_path, expected_sha in args.source:
        path = Path(pdf_path)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected_sha:
            raise AssertionError(f"immutable source digest mismatch for {code}: {actual}")
        doc = fitz.open(path)
        if doc.page_count != 1:
            raise AssertionError(f"reference viewer source must resolve to exactly one measured page: {code}")
        page = doc[0]
        pix = page.get_pixmap(dpi=args.dpi, alpha=False)
        target = out / code
        target.mkdir(parents=True, exist_ok=True)
        png = target / f"{code}_p001_{args.dpi}dpi.png"
        pix.save(png)
        print(f"SOURCE_RENDER={code};sha256={actual};page=0;points={page.rect.width:.6f}x{page.rect.height:.6f};pixels={pix.width}x{pix.height};dpi={args.dpi}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
