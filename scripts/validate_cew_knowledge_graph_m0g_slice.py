#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'automation/CEW_KNOWLEDGE_GRAPH_CONTRACT_v1.json'; MEMBERS=ROOT/'data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv'; HANDOFF=ROOT/'data/canonical/M0G_GEOMETRY_HANDOFF_v1.json'; MILESTONES=ROOT/'data/canonical/CEW_SYSTEM_MILESTONES_v1.csv'
def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def epi(raw):
    u=(raw or '').strip().upper()
    for s in ('DOC','MIS','RIF','INF','ND'):
        if u.startswith(s):return s
    return 'ND'
def valid_f5_governance(ms):
    return ms.get('CEW-F5') in {'IN_PROGRESS','COMPLETE'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--projection',required=True);a=ap.parse_args();p=json.loads(Path(a.projection).read_text(encoding='utf-8'));c=json.loads(CONTRACT.read_text(encoding='utf-8'))
    if c.get('contract_id')!='CEW-KNOWLEDGE-GRAPH-v1':raise AssertionError('unexpected knowledge graph contract')
    if any(c['authority_invariants'][k] is not False for k in ('projection_may_modify_source_ledger','projection_may_reopen_m0g','projection_may_raise_epistemic_state','projection_may_invent_missing_property','projection_may_collapse_distinct_evidence_states','graph_is_primary_evidence')):raise AssertionError('knowledge graph authority boundary weakened')
    ms={r['milestone_id'].strip():r['status'].strip() for r in rows(MILESTONES)}
    if not valid_f5_governance(ms) or any(ms.get(x)!='COMPLETE' for x in ('CEW-F0','CEW-F1','CEW-F2','CEW-F3','CEW-F4')):raise AssertionError('F5 milestone governance invalid')
    source={r['member_id'].strip():r for r in rows(MEMBERS)}; expected=int(json.loads(HANDOFF.read_text(encoding='utf-8'))['frozen_inventory']['ordinary_structural_members'])
    if len(source)!=expected:raise AssertionError('source member count differs from frozen handoff')
    ents=p['entities']; binds=p['bindings']; ass=p['assertions']
    if p.get('authority')!='DERIVED_GRAPH_PROJECTION_ONLY':raise AssertionError('graph projection authority drift')
    if len(ents)!=expected or len({e['entity_id'] for e in ents})!=expected:raise AssertionError('entity projection count/identity mismatch')
    if len(binds)!=expected*2:raise AssertionError('each member must preserve exactly two endpoint bindings')
    for e in ents:
        r=source[e['entity_id']]
        if e['entity_class']!=r['member_class'].strip() or e['storey_id']!=r['storey_id'].strip() or e['validation_state']!=r['validation_state'].strip() or e['temporal_state']!='CURRENT':raise AssertionError(f"entity semantics/state changed: {e['entity_id']}")
    by={}
    for b in binds:by.setdefault(b['from_entity_id'],[]).append(b)
    for mid,r in source.items():
        bs=by.get(mid,[]); actual={(b['relation'],b['to_entity_id']) for b in bs}; wanted={('STARTS_AT_NODE',r['node_i'].strip()),('ENDS_AT_NODE',r['node_j'].strip())}
        if actual!=wanted:raise AssertionError(f'endpoint binding changed: {mid}')
        if any(b['epistemic_state']!=epi(r['connectivity_evidence']) for b in bs):raise AssertionError(f'connectivity evidence promoted/collapsed: {mid}')
    sec={mid:r for mid,r in source.items() if r['section_cm'].strip()}
    if len(ass)!=len(sec):raise AssertionError('section assertion count mismatch')
    for x in ass:
        r=sec[x['entity_id']]
        if x['property_name']!='section_cm' or x['value']!=r['section_cm'].strip() or x['epistemic_state']!=epi(r['section_evidence']) or x['validation_state']!=r['validation_state'].strip():raise AssertionError(f"section assertion changed: {x['entity_id']}")
    missing=[mid for mid,r in source.items() if not r['section_cm'].strip()]; asserted={x['entity_id'] for x in ass}
    if any(mid in asserted for mid in missing):raise AssertionError('graph invented missing section property')
    print('KNOWLEDGE_GRAPH_M0G_SLICE_PASS');print(f'STRUCTURAL_ENTITIES={len(ents)}');print(f'ENDPOINT_BINDINGS={len(binds)}');print(f'SECTION_ASSERTIONS={len(ass)}');print(f'MISSING_SECTION_PROPERTIES_NOT_INVENTED={len(missing)}');print('AUTHORITY=DERIVED_GRAPH_PROJECTION_ONLY');print('M0G_REOPEN=FORBIDDEN');print('POST_CLOSURE_STATE=F5_PHASE_MONOTONIC');return 0
if __name__=='__main__':raise SystemExit(main())