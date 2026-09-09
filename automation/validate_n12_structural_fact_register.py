#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'recovery/knowledge/N12_STRUCTURAL_FACT_REGISTER_v1.json'
REGIONS = ROOT / 'recovery/knowledge/N12_EVIDENCE_REGIONS_RCP02_RCP10_RCP13_v1.json'

ALLOWED_STATES = {'DOC','MIS','RIF','INF','ND'}


def fail(msg):
    print(f'N12_STRUCTURAL_FACT_REGISTER_FAIL: {msg}')
    raise SystemExit(1)


def main():
    data = json.loads(REG.read_text(encoding='utf-8'))
    regions = json.loads(REGIONS.read_text(encoding='utf-8'))['regions']
    region_ids = {r['id'] for items in regions.values() for r in items}
    ids = set()
    for fact in data.get('facts', []):
        fid = fact.get('fact_id')
        if not fid or fid in ids:
            fail(f'duplicate or missing fact_id: {fid}')
        ids.add(fid)
        if fact.get('state') not in ALLOWED_STATES:
            fail(f'{fid}: invalid state')
        if not fact.get('source_identity') or not fact.get('source_file'):
            fail(f'{fid}: missing source binding')
        if fact.get('evidence_region') not in region_ids:
            fail(f'{fid}: unknown evidence region {fact.get("evidence_region")}')
        if fact.get('canonical_write') != 'NO':
            fail(f'{fid}: canonical write must remain forbidden')
        if fact['state'] == 'RIF' and not fact.get('independent_support'):
            fail(f'{fid}: RIF requires independent support')
        if fact['state'] == 'DOC' and not fact.get('observation'):
            fail(f'{fid}: DOC requires direct observation')
    if data.get('authority', {}).get('canonical_write_authorized') is not False:
        fail('canonical write authorization detected')
    if data.get('authority', {}).get('human_review_required') is not True:
        fail('human review must remain required')
    print(f'N12_STRUCTURAL_FACT_REGISTER_PASS facts={len(ids)}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
