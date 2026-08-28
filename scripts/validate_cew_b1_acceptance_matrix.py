#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/'automation/CEW_B1_ACCEPTANCE_MATRIX_v1.json'
METRICS=ROOT/'automation/CEW_USABILITY_METRICS_MODEL_v1.json'
QUEUE=ROOT/'automation/CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json'


def load(p): return json.loads(p.read_text(encoding='utf-8'))


def main():
    errors=[]
    matrix=load(MATRIX); metrics=load(METRICS); queue=load(QUEUE)
    if matrix.get('b1_release_authorized') is not False: errors.append('B1 must remain blocked')
    if matrix.get('b2_release_authorized') is not False: errors.append('B2 must remain blocked')
    if matrix.get('canonical_write_authorized') is not False: errors.append('canonical write must remain false')

    slices={s['id']:s for s in matrix.get('slices',[])}
    expected={f'B1.{i}' for i in range(1,7)}
    if set(slices)!=expected: errors.append(f'acceptance slices mismatch: {sorted(slices)}')
    for sid,row in slices.items():
        if row.get('automated_gates')!='PASS': errors.append(f'{sid}: automated gates not PASS')
        if row.get('promotion')!='BLOCKED': errors.append(f'{sid}: preparation must remain promotion BLOCKED')
        receipt=row.get('receipt')
        if receipt and not (ROOT/receipt).exists(): errors.append(f'{sid}: missing receipt {receipt}')

    if slices.get('B1.4',{}).get('private_byte_storage')!='NOT_CONFIGURED': errors.append('B1.4 storage truth drift')
    if slices.get('B1.6',{}).get('candidate_append_only_store')!='NOT_APPLIED': errors.append('B1.6 candidate store truth drift')

    critical=matrix.get('critical_release_gates',{})
    if critical.get('HVA')!='PENDING': errors.append('HVA must remain pending')
    if critical.get('EXTENDED_B1_PRODUCTION_SMOKE')!='NOT_PERFORMED': errors.append('extended B1 Production smoke must not be fabricated')
    if critical.get('AUTHORITY_MISUNDERSTANDING_CRITICAL_ERRORS')!='MUST_BE_ZERO': errors.append('critical authority false-success policy drift')

    metric_ids={t['task_id'] for t in metrics.get('initial_cew_b11_tasks',[])} | {t['task_id'] for t in metrics.get('extended_b1_tasks',[])}
    matrix_ids={t['task_id'] for t in matrix.get('usability_tasks',[])}
    if metric_ids != matrix_ids: errors.append(f'usability task mismatch metrics={sorted(metric_ids)} matrix={sorted(matrix_ids)}')
    if metrics.get('benchmark_policy',{}).get('critical_authority_false_success_tolerance') != 0: errors.append('critical authority false-success tolerance must be zero')

    items={i['id']:i for i in queue.get('items',[])}
    if items.get('CEW-B1-SOURCE-EVIDENCE-JOURNEY',{}).get('state')!='IN_PROGRESS': errors.append('main product queue must keep B1 IN_PROGRESS')
    if items.get('CEW-B2-RECONSTRUCTION-PROPERTIES',{}).get('state')!='WAITING': errors.append('main product queue must keep B2 WAITING')

    if errors:
        print('CEW_B1_ACCEPTANCE_MATRIX = FAIL')
        for e in errors: print('ERROR:',e)
        return 1
    print('CEW_B1_ACCEPTANCE_MATRIX = PASS')
    print('PREPARATION_SLICES_AUTOMATED = PASS')
    print('HVA = PENDING')
    print('PRIVATE_DOCUMENT_BYTE_STORAGE = NOT_CONFIGURED')
    print('CANDIDATE_APPEND_ONLY_STORE = NOT_APPLIED')
    print('EXTENDED_B1_PRODUCTION_SMOKE = NOT_PERFORMED')
    print('B1_RELEASE_AUTHORIZED = false')
    print('B2_RELEASE_AUTHORIZED = false')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
