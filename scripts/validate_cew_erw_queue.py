#!/usr/bin/env python3
from __future__ import annotations

import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'automation'/'CEW_ERW_CONTRACT_v1.json'
EXPECTED={
 'ERW-N12-001':('M1E-B06-R08','UNREADABLE','ND_QTY_DIAMETER'),
 'ERW-N12-002':('M1E-B06-R09','UNREADABLE','ND_QTY_DIAMETER'),
 'ERW-N12-003':('M1E-B06-R10','UNREADABLE','DOC_DIRECT_PARTIAL+ND_REMAINDER'),
 'ERW-N12-004':('M1E-B06-R11','UNBOUND','ND_MEMBER_BINDING'),
}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--bundle',required=True); a=ap.parse_args()
 contract=json.loads(CONTRACT.read_text(encoding='utf-8')); b=json.loads(Path(a.bundle).read_text(encoding='utf-8'))
 if contract.get('milestone')!='CEW-F6' or contract.get('status')!='ACTIVE_IMPLEMENTATION_CONTRACT': raise AssertionError('F6 contract inactive')
 if b.get('authority')!='DERIVED_REVIEW_WORKSPACE_ONLY' or b.get('canonical_mutation')!='FORBIDDEN': raise AssertionError('authority drift')
 if b.get('task_count')!=4 or len(b.get('workspaces',[]))!=4: raise AssertionError('queue must contain exactly four tasks')
 inv=contract['authority_invariants']
 forbidden=('workspace_may_modify_canonical_ledgers','workspace_may_modify_f2_geometry','workspace_may_reopen_m0g','workspace_may_promote_without_direct_evidence','candidate_comparison_is_primary_evidence')
 if any(inv.get(k) is not False for k in forbidden): raise AssertionError('authority invariant weakened')
 seen=set(); outcomes=[]
 for w in b['workspaces']:
  t=w['task']; tid=t['task_id'].strip(); seen.add(tid)
  if tid not in EXPECTED: raise AssertionError('unexpected task')
  residual,outcome,requested=EXPECTED[tid]
  if t['residual_id'].strip()!=residual or w['residual']['residual_id'].strip()!=residual: raise AssertionError('residual mismatch')
  if w['authority']!='DERIVED_REVIEW_WORKSPACE_ONLY' or w['canonical_mutation']!='FORBIDDEN': raise AssertionError('workspace authority drift')
  obs=w['source']['observation']; viewer=w['source']['viewer_binding']; d=w['reference_disposition_receipt']
  if obs['structural_binding'].strip(): raise AssertionError('structural binding silently introduced')
  if viewer['binding_state'].strip()!='READY': raise AssertionError('viewer binding not READY')
  selectable=[c for c in w['candidates'] if c.get('selectable') is True]
  if len(selectable)!=1: raise AssertionError('must expose one supported reference disposition')
  if any(c.get('selectable') is True and c.get('status') in ('FORBIDDEN','REJECTED_BY_CURRENT_EVIDENCE') for c in w['candidates']): raise AssertionError('unsupported candidate selectable')
  if d['outcome']!=outcome or d['selected_candidate']!=selectable[0]['candidate_id'] or d['requested_epistemic_state']!=requested: raise AssertionError('decision drift')
  if d.get('canonical_write') is not False: raise AssertionError('canonical write attempted')
  if tid in ('ERW-N12-001','ERW-N12-002'):
   lit=obs['literal_or_value'];
   if 'quantity=UNREADABLE' not in lit or 'diameter=UNREADABLE' not in lit: raise AssertionError('unreadable qty/diameter not preserved')
  if tid=='ERW-N12-003' and 'UNREADABLE' not in obs['literal_or_value']: raise AssertionError('partial unreadable state not preserved')
  if tid=='ERW-N12-004':
   m=w['model']['candidate_member']
   if (m['source_member_id'],m['support_i'],m['support_j'])!=('G5-B017','12','19'): raise AssertionError('G5-B017 topology drift')
   if 'UNBOUND' not in obs['migration_note'] or 'UNBOUND' not in viewer['authority_note']: raise AssertionError('UNBOUND not preserved')
  outcomes.append(outcome)
 if seen!=set(EXPECTED): raise AssertionError('task coverage drift')
 if outcomes.count('UNREADABLE')!=3 or outcomes.count('UNBOUND')!=1: raise AssertionError('reference disposition counts drift')
 print('ERW_QUEUE_PASS'); print('TASKS=4/4'); print('UNREADABLE_DISPOSITIONS=3'); print('UNBOUND_DISPOSITIONS=1'); print('UNSUPPORTED_COMPLETION=FORBIDDEN'); print('F2_GEOMETRY_MUTATION=FORBIDDEN'); print('M0G_REOPEN=FORBIDDEN'); print('CANONICAL_WRITE=FORBIDDEN'); print('EPISTEMIC_PROMOTION=FORBIDDEN')
 return 0
if __name__=='__main__': raise SystemExit(main())
