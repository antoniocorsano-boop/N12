#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

EXPECTED_IDS = {
    'L010','L012','L013','L014','L015','L016','L022','L023',
    'L040','L042','L043','L052','L053','L054','L055'
}
ALLOWED_CLASSES = {'BEAM_AXIS_OR_FACE_COMPATIBLE','NON_STRUCTURAL','AMBIGUOUS'}
ALLOWED_ROLES = {'AXIS_LIKE','FACE_OR_EDGE_LIKE','NOT_APPLICABLE','UNRESOLVED'}
ALLOWED_STRENGTH = {'STRONG','MODERATE','WEAK'}


def load(path: Path):
    with path.open(newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def validate(path: Path) -> None:
    rows = load(path)
    ids = [r['line_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit('duplicate line_id in visual review')
    if set(ids) != EXPECTED_IDS:
        raise SystemExit(f'candidate coverage mismatch: {sorted(set(ids)^EXPECTED_IDS)}')
    for r in rows:
        if r['visual_class'] not in ALLOWED_CLASSES:
            raise SystemExit(f"invalid visual_class for {r['line_id']}")
        if r['metric_role'] not in ALLOWED_ROLES:
            raise SystemExit(f"invalid metric_role for {r['line_id']}")
        if r['review_strength'] not in ALLOWED_STRENGTH:
            raise SystemExit(f"invalid review_strength for {r['line_id']}")
        if r['canonical_binding'] != 'PROHIBITED':
            raise SystemExit(f"canonical binding not prohibited for {r['line_id']}")
        if r['epistemic_effect'] != 'NONE':
            raise SystemExit(f"epistemic effect changed for {r['line_id']}")
        if not r['note'].strip():
            raise SystemExit(f"missing review note for {r['line_id']}")
    print('LINE_TOPOLOGY_VISUAL_REVIEW_VALIDATION_PASS')


if __name__ == '__main__':
    validate(Path('analysis/experimental_source_concordance/TAV06S_LINE_TOPOLOGY_VISUAL_REVIEW_v1.csv'))
