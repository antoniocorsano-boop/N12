#!/usr/bin/env python3
import argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'automation/CEW_HUMAN_DECISION_RECEIPT_SCHEMA_v1.json'
TASKS = ROOT / 'data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv'
VIEWER = ROOT / 'data/canonical/CEW_SOURCE_VIEWER_BINDINGS_v1.csv'
TARGETS = ROOT / 'data/canonical/CEW_PROMOTION_TARGET_REGISTRY_v1.csv'

ORDER = {'ND': 0, 'INF': 1, 'RIF': 2, 'MIS': 3, 'DOC': 4}
CEILING = {'DOC_DIRECT_ONLY': 'DOC', 'INF_STRONG_DRAFTING_RULE': 'INF'}


def rows(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def fail(msg):
    raise SystemExit(f'HUMAN_DECISION_RECEIPT_FAIL: {msg}')


def validate(receipt):
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    missing = [k for k in schema['required_fields'] if k not in receipt]
    if missing: fail('missing fields: ' + ','.join(missing))
    for k, v in schema['fixed_values'].items():
        if receipt[k] != v: fail(f'{k} must equal {v}')
    if receipt['outcome'] not in schema['allowed_outcomes']: fail('outcome not allowed')
    if receipt['requested_epistemic_state'] not in schema['allowed_requested_states']: fail('requested state not allowed')
    if not str(receipt['decision_id']).strip(): fail('decision_id empty')
    if not str(receipt['reviewer']).strip(): fail('reviewer empty')
    if not str(receipt['timestamp']).strip(): fail('timestamp empty')
    if receipt['authority_acknowledgement'] != schema['authority_acknowledgement_exact']:
        fail('authority acknowledgement mismatch')

    task_map = {r['task_id']: r for r in rows(TASKS)}
    viewer_map = {r['task_id']: r for r in rows(VIEWER)}
    target_map = {r['target_id']: r for r in rows(TARGETS) if r['status'] == 'ACTIVE'}
    task_id = receipt['task_id']
    if task_id not in task_map or task_id not in viewer_map: fail('unknown task_id')
    task, binding = task_map[task_id], viewer_map[task_id]
    if receipt['residual_id'] != task['residual_id']: fail('task/residual mismatch')
    if receipt['evidence_regions'] != [binding['evidence_region_id']]: fail('evidence region mismatch')
    if receipt['source_versions'] != [binding['source_version_id']]: fail('source version mismatch')

    current_ceiling = CEILING.get(task['epistemic_ceiling'])
    if not current_ceiling: fail('unsupported task ceiling')
    requested = receipt['requested_epistemic_state']
    if ORDER[requested] > ORDER[current_ceiling]: fail('requested state exceeds task ceiling')

    outcome = receipt['outcome']
    target_id = str(receipt['target_id']).strip()
    if outcome == 'CONFIRMED':
        if not str(receipt['human_observation']).strip(): fail('confirmed requires human observation')
        if receipt['direct_primary_evidence_observed'] is not True: fail('confirmed requires direct primary evidence')
        if not target_id: fail('confirmed requires target_id')
        if target_id not in target_map: fail('target not active/registered')
        target = target_map[target_id]
        if ORDER[requested] > ORDER[target['max_epistemic_state']]: fail('requested state exceeds target ceiling')
        if target['geometry_sensitive'] == 'YES' and not str(receipt['reopen_approval_id']).strip():
            fail('geometry-sensitive target requires reopen approval')
    else:
        if target_id: fail('non-confirmed outcome cannot select target')
        if receipt['direct_primary_evidence_observed'] not in (True, False): fail('direct_primary flag must be boolean')

    print('HUMAN_DECISION_RECEIPT_VALID')
    print(f"TASK={task_id}")
    print(f"RESIDUAL={receipt['residual_id']}")
    print(f"OUTCOME={outcome}")
    print(f"REQUESTED_STATE={requested}")
    print(f"TARGET={target_id or 'NONE'}")
    print('CANONICAL_WRITE_EXECUTED=0')
    return 0


def negative_self_test():
    base = {
      'schema_version':'1.0','decision_id':'NEG-TEST','task_id':'ERW-N12-001','residual_id':'M1E-B06-R08',
      'review_mode':'HUMAN_REVIEW','reviewer':'synthetic-negative-test','timestamp':'2000-01-01T00:00:00Z',
      'outcome':'UNREADABLE','human_observation':'','evidence_regions':['CEW-N12-REG-G01-R06'],
      'source_versions':['CEW-N12-SRC-TAV05A-V17DEC414'],'direct_primary_evidence_observed':False,
      'requested_epistemic_state':'ND','target_id':'','reopen_approval_id':'',
      'authority_acknowledgement':'I reviewed the cited immutable primary-source evidence and understand this receipt is not itself a canonical write.'
    }
    cases = []
    x = dict(base); x['residual_id']='WRONG'; cases.append(x)
    x = dict(base); x['evidence_regions']=['WRONG']; cases.append(x)
    x = dict(base); x['source_versions']=['WRONG']; cases.append(x)
    x = dict(base); x['target_id']='CEW-TARGET-REINFORCEMENT-OBSERVATION'; cases.append(x)
    x = dict(base); x['outcome']='CONFIRMED'; x['human_observation']=''; x['direct_primary_evidence_observed']=True; x['target_id']='CEW-TARGET-REINFORCEMENT-OBSERVATION'; x['requested_epistemic_state']='DOC'; cases.append(x)
    x = dict(base); x['task_id']='ERW-N12-004'; x['residual_id']='M1E-B06-R11'; x['evidence_regions']=['CEW-N12-REG-T6A-G03']; x['source_versions']=['CEW-N12-SRC-TAV06A-V3F2D557F']; x['outcome']='CONFIRMED'; x['human_observation']='shape-only negative test'; x['direct_primary_evidence_observed']=True; x['target_id']='CEW-TARGET-STRUCTURAL-BINDING'; x['requested_epistemic_state']='INF'; x['reopen_approval_id']=''; cases.append(x)
    rejected = 0
    for c in cases:
        try:
            validate(c)
        except SystemExit:
            rejected += 1
    if rejected != len(cases): fail('negative self-test did not reject every case')
    print('HUMAN_DECISION_RECEIPT_VALIDATOR_PASS')
    print(f'NEGATIVE_CASES_REJECTED={rejected}/{len(cases)}')
    print('SYNTHETIC_HUMAN_DECISION_CREATED=0')
    print('CANONICAL_WRITE_EXECUTED=0')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--receipt')
    ap.add_argument('--negative-self-test', action='store_true')
    args = ap.parse_args()
    if args.negative_self_test:
        negative_self_test(); return
    if not args.receipt: fail('provide --receipt or --negative-self-test')
    validate(json.loads(Path(args.receipt).read_text(encoding='utf-8')))

if __name__ == '__main__':
    main()
