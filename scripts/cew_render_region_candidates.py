#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import fitz


def clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--candidates', required=True)
    p.add_argument('--tav05a', required=True)
    p.add_argument('--tav06a', required=True)
    p.add_argument('--dpi', type=int, default=300)
    p.add_argument('--out-dir', required=True)
    args = p.parse_args()

    source_paths = {
        'TAV-05A': Path(args.tav05a),
        'TAV-06A': Path(args.tav06a),
    }
    docs = {k: fitz.open(v) for k, v in source_paths.items()}
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = []

    with Path(args.candidates).open('r', encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))

    matrix = fitz.Matrix(args.dpi / 72.0, args.dpi / 72.0)
    for row in rows:
        ref = row['reference_item'].strip()
        src = row['source_code'].strip()
        if src not in docs:
            raise AssertionError(f'unsupported source {src}')
        if row['coordinate_space'].strip() != 'NORMALIZED_0_1':
            raise AssertionError(f'{ref}: candidate must use NORMALIZED_0_1')
        if row['state'].strip() != 'CANDIDATE_REVIEW':
            raise AssertionError(f'{ref}: unexpected candidate state')

        x = float(row['x']); y = float(row['y']); w = float(row['width']); h = float(row['height'])
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1 and x + w <= 1.000001 and y + h <= 1.000001):
            raise AssertionError(f'{ref}: invalid normalized bbox')

        page = docs[src][0]
        rect = page.rect
        clip = fitz.Rect(
            clamp(x) * rect.width,
            clamp(y) * rect.height,
            clamp(x + w) * rect.width,
            clamp(y + h) * rect.height,
        )
        pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
        safe = ref.replace('/', '__')
        file_name = f'{safe}_{args.dpi}dpi.png'
        pix.save(out / file_name)
        manifest.append({
            'reference_item': ref,
            'source_code': src,
            'page_id': row['page_id'].strip(),
            'normalized_bbox': [x, y, w, h],
            'source_native_bbox_pt': [clip.x0, clip.y0, clip.x1, clip.y1],
            'render_file': file_name,
            'render_width_px': pix.width,
            'render_height_px': pix.height,
            'candidate_basis': row['candidate_basis'].strip(),
        })

    (out / 'candidate_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('CEW_F2_REGION_CANDIDATE_RENDER_PASS')
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
