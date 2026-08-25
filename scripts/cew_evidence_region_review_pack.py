#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def bbox_for_cell(w: int, h: int, r: int, c: int, rows: int, cols: int, overlap: float):
    cw, ch = w / cols, h / rows
    x0 = max(0, int(c * cw - overlap * cw))
    y0 = max(0, int(r * ch - overlap * ch))
    x1 = min(w, int((c + 1) * cw + overlap * cw))
    y1 = min(h, int((r + 1) * ch + overlap * ch))
    return x0, y0, x1, y1


def build_issue_pack(registry: dict, issue_id: str, image_dir: Path, out: Path, source_meta: dict):
    review = next((x for x in registry['issue_review_sets'] if x['issue_id'] == issue_id), None)
    if not review:
        raise SystemExit(f'Unknown issue: {issue_id}')
    policy = registry['render_policy']
    rows = int(policy['tile_grid']['rows'])
    cols = int(policy['tile_grid']['cols'])
    overlap = float(policy['tile_grid']['overlap_fraction'])
    source_index = {x['source_id']: x for x in registry['sources']}

    issue_dir = out / issue_id
    issue_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        'schema_version': '1.0',
        'issue_id': issue_id,
        'purpose': review['purpose'],
        'authority_state': 'REVIEW_CONTEXT_ONLY',
        'promotion_rule': review['promotion_rule'],
        'grid': {'rows': rows, 'cols': cols, 'overlap_fraction': overlap},
        'sources': [],
        'guards': [
            'Tile bbox is deterministic image context, not engineering geometry.',
            'No tile is an EvidenceSnippet until explicit human/source binding is recorded.',
            'No issue or claim is changed by generation of this review pack.'
        ]
    }

    html_parts = [f'<h1>{issue_id} — Evidence Region Review Pack</h1>',
                  '<p>Derivative review context only. Primary archived PDFs remain authoritative.</p>']

    for sid in review['source_ids']:
        src = source_index[sid]
        img_path = image_dir / f'{sid}_300dpi.jpg'
        if not img_path.exists():
            raise SystemExit(f'Missing rendered image: {img_path}')
        im = Image.open(img_path).convert('RGB')
        w, h = im.size
        src_dir = issue_dir / sid
        src_dir.mkdir(parents=True, exist_ok=True)
        overview = im.copy()
        overview.thumbnail((1800, 1800))
        overview_path = src_dir / 'overview.jpg'
        overview.save(overview_path, quality=90)

        source_entry = {
            'source_id': sid,
            'archive_path': src['archive_path'],
            'archive_commit': source_meta[sid]['archive_commit'],
            'archive_blob_sha': source_meta[sid]['archive_blob_sha'],
            'pdf_page_count': source_meta[sid]['pdf_page_count'],
            'render_dpi': policy['dpi'],
            'render_size_px': [w, h],
            'render_sha256': sha256(img_path),
            'tiles': []
        }
        html_parts.append(f'<h2>{sid}</h2><img src="{sid}/overview.jpg" style="max-width:900px"><div>')
        for r in range(rows):
            for c in range(cols):
                x0, y0, x1, y1 = bbox_for_cell(w, h, r, c, rows, cols, overlap)
                tile_id = f'{sid}-R{r+1}C{c+1}'
                tile_path = src_dir / f'R{r+1}C{c+1}.jpg'
                tile = im.crop((x0, y0, x1, y1))
                # Visible deterministic label; does not alter source authority.
                draw = ImageDraw.Draw(tile)
                draw.rectangle((0, 0, 170, 30), fill='white')
                draw.text((8, 8), tile_id, fill='black')
                tile.save(tile_path, quality=92)
                source_entry['tiles'].append({
                    'tile_id': tile_id,
                    'bbox_px': [x0, y0, x1, y1],
                    'bbox_normalized': [x0 / w, y0 / h, x1 / w, y1 / h],
                    'file': f'{sid}/R{r+1}C{c+1}.jpg',
                    'authority_state': 'CONTEXT_ONLY'
                })
                html_parts.append(f'<figure style="display:inline-block;width:23%;vertical-align:top"><img src="{sid}/R{r+1}C{c+1}.jpg" style="width:100%"><figcaption>{tile_id} [{x0},{y0},{x1},{y1}]</figcaption></figure>')
        html_parts.append('</div>')
        manifest['sources'].append(source_entry)

    (issue_dir / 'review_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (issue_dir / 'index.html').write_text('<html><body>' + ''.join(html_parts) + '</body></html>', encoding='utf-8')
    print(f'{issue_id}: sources={len(manifest["sources"])} tiles={sum(len(x["tiles"]) for x in manifest["sources"])}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--registry', default='automation/CEW_SOURCE_RENDER_REGISTRY_v1.json')
    ap.add_argument('--source-meta', required=True)
    ap.add_argument('--image-dir', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--issue', action='append', required=True)
    args = ap.parse_args()
    registry = json.loads(Path(args.registry).read_text(encoding='utf-8'))
    source_meta = json.loads(Path(args.source_meta).read_text(encoding='utf-8'))
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    for issue in args.issue:
        build_issue_pack(registry, issue, Path(args.image_dir), out, source_meta)


if __name__ == '__main__':
    main()
