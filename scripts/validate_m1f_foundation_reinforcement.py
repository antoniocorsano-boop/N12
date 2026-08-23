#!/usr/bin/env python3
from __future__ import annotations
import csv, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; C=ROOT/'data'/'canonical'
GROUPS=C/'M1F_TAV01A_GROUP_INDEX_v1.csv'; REINF=C/'M1F_TAV01A_GROUP_REINFORCEMENT_v1.csv'; PATCH=C/'M1F_TAV01A_REINFORCEMENT_CORRECTION_PATCH_v1.csv'; QUEUE=C/'M1F_REINFORCEMENT_EXTRACTION_QUEUE_v1.csv'; TOPOLOGY=C/'M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv'; CROSSCHECK=C/'M1F_TAV01A_TAV01S_CROSSCHECK_v1.csv'; GATE=C/'M1F_FOUNDATION_REINFORCEMENT_GATE_v1.csv'
EXPECTED_GROUPS={f'F1A-G0{i}' for i in range(1,8)}; EXPECTED_PATCH_IDS={f'M1F-REINF-P{i:03d}' for i in range(1,15)}
def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def apply_patch(base,patch,errors):
    rows=[dict(r) for r in base]; by={r['row_id'].strip():r for r in rows}
    if len(patch)!=14 or {r['patch_id'].strip() for r in patch}!=EXPECTED_PATCH_IDS: errors.append('HiRes correction/partition patch must contain exactly P001-P014'); return rows
    for p in patch:
        op=p['operation'].strip(); target=p['target_row_id'].strip(); new=p['new_row_id'].strip(); vals={'group_id':p['group_id'].strip(),'source_id':'TAV-01A','source_locator':p['source_locator'].strip(),'bar_role':p['bar_role'].strip(),'bar_quantity':p['bar_quantity'].strip(),'bar_diameter_mm':p['bar_diameter_mm'].strip(),'shape_or_length':p['shape_or_length'].strip(),'segment_dimensions_cm':p.get('segment_dimensions_cm','').strip(),'evidence_status':p['evidence_status'].strip(),'binding_state':p['binding_state'].strip(),'note':p['reason'].strip()}
        if op=='REPLACE':
            if target not in by or new!=target: errors.append(f'invalid REPLACE {p["patch_id"]}'); continue
            by[target].update(vals)
        elif op=='ADD':
            if not new or new in by: errors.append(f'invalid ADD {p["patch_id"]}'); continue
            r={k:'' for k in base[0].keys()}; r['row_id']=new; r.update(vals); rows.append(r); by[new]=r
        else: errors.append(f'unknown patch operation {op!r}')
    return rows
def main():
    errors=[]; warnings=[]
    req=[GROUPS,REINF,PATCH,QUEUE,TOPOLOGY,CROSSCHECK,GATE]
    for p in req:
        if not p.exists(): errors.append(f'missing required artifact: {p.relative_to(ROOT)}')
    if errors:return report(errors,warnings,{})
    groups,base,patch,queue,topology,cross,gate=map(read_csv,req); reinf=apply_patch(base,patch,errors)
    gids=[r['group_id'].strip() for r in groups]
    if len(groups)!=7 or set(gids)!=EXPECTED_GROUPS or len(set(gids))!=7: errors.append('group index must contain exactly unique G01-G07')
    if len(base)!=47: errors.append(f'base rows must remain 47, got {len(base)}')
    if len(reinf)!=54: errors.append(f'effective rows must be 54, got {len(reinf)}')
    ids=[r['row_id'].strip() for r in reinf]
    if len(ids)!=len(set(ids)): errors.append('duplicate effective reinforcement row_id')
    qby={r['group_id'].strip():r for r in queue}; complete=sum(r['reinforcement_transcription_state'].strip()=='COMPLETE_DIRECT' for r in queue); partial=sum(r['reinforcement_transcription_state'].strip()=='PARTIAL_DIRECT' for r in queue); pending=sum(r['reinforcement_transcription_state'].strip()=='PENDING' for r in queue)
    if set(qby)!=EXPECTED_GROUPS or len(queue)!=7: errors.append('queue must contain G01-G07 exactly once')
    if (complete,partial,pending)!=(5,2,0): errors.append(f'queue partition expected 5/2/0, got {(complete,partial,pending)}')
    open_rows=[r for r in reinf if r['binding_state'].strip().startswith('OPEN_')]
    if len(open_rows)!=2: errors.append(f'open rows expected 2, got {len(open_rows)}')
    for g in ['F1A-G05','F1A-G06']:
        states={r['binding_state'].strip() for r in reinf if r['group_id'].strip()==g}
        if not any(s.endswith('B_SIDE') for s in states) or not any(s.endswith('A_SIDE') for s in states): errors.append(f'{g}: B/A regimes must remain explicit')
    g05_transition=[r for r in reinf if r['group_id'].strip()=='F1A-G05' and r['binding_state'].strip()=='GROUP_BOUND_TRANSITION_17_18']
    if len(g05_transition)!=2: errors.append(f'G05 must preserve exactly two direct transition-spanning bars, got {len(g05_transition)}')
    by={r['row_id'].strip():r for r in reinf}
    exact={
      'F1A-G07-R04':('2','12','BENT_PARTIAL','70+70=140;right_diag122;left_inclined_segment_unlabelled','GROUP_BOUND'),
      'F1A-G07-R04B':('2','12','BENT_PARTIAL','left_diag122;70+30=100;right_diag_unlabelled','GROUP_BOUND'),
      'F1A-G07-R04C':('2','14','BENT_PARTIAL','left_diag122;30+70=100;right_end_segment_unlabelled','GROUP_BOUND'),
      'F1A-G04-R04':('2','18','BENT_PARTIAL','left_end_segment_unlabelled;70+100=170;right_diag122;continuation_unlabelled','GROUP_BOUND'),
      'F1A-G04-R04B':('2','14','BENT_PARTIAL','left_diag122;100+40=140;ascending_diag_unlabelled;top210;right_diag122;40+70=110','GROUP_BOUND'),
      'F1A-G06-R09A':('2','14','BENT','left_diag122;100+45=145;ascending_diag122;top200;right_diag122;45+105=150','GROUP_BOUND_A_SIDE'),
      'F1A-G05-R04B':('2','12','BENT','60+70=130;right_diag93','GROUP_BOUND_B_SIDE'),
      'F1A-G05-R04C':('2','14','BENT','left_diag93;70+35=105;ascending_diag93;top140;descending_diag93;35+95=130;right_diag122','GROUP_BOUND_TRANSITION_17_18'),
      'F1A-G05-R09A':('2','18','BENT','left_diag93;70+50=120;ascending_diag122;top280;descending_diag122;50+95=145;right_diag122','GROUP_BOUND_TRANSITION_17_18'),
      'F1A-G05-R09B':('2','14','BENT_PARTIAL','left_diag122;95+70=165','GROUP_BOUND_A_SIDE')}
    for rid,exp in exact.items():
        r=by.get(rid,{}); act=(r.get('bar_quantity','').strip(),r.get('bar_diameter_mm','').strip(),r.get('shape_or_length','').strip(),r.get('segment_dimensions_cm','').strip(),r.get('binding_state','').strip())
        if act!=exp: errors.append(f'{rid}: direct partition mismatch expected {exp}, got {act}')
    g03=[r for r in reinf if r['group_id'].strip()=='F1A-G03']; expected_g03={('UPPER_STRAIGHT_BAR','3','16','L=880'),('UPPER_STRAIGHT_BAR','2','14','L=910'),('LOWER_STRAIGHT_BAR','3','18','L=920'),('LOWER_STRAIGHT_BAR','3','14','L=960')}; actual_g03={(r['bar_role'].strip(),r['bar_quantity'].strip(),r['bar_diameter_mm'].strip(),r['shape_or_length'].strip()) for r in g03 if r['bar_role'].strip() in {'UPPER_STRAIGHT_BAR','LOWER_STRAIGHT_BAR'}}
    if actual_g03!=expected_g03: errors.append('G03 direct straight-bar mismatch')
    if not any(r['binding_state'].strip()=='GROUP_BOUND_WITH_22_PRIME_CORRECTION' for r in g03): errors.append('G03 22-prime correction missing')
    for rid,exp in {'F1A-G02-R02':('2','14','L=1080|L=990'),'F1A-G02-R02B':('3','16','L=1100'),'F1A-G02-R03':('3','14','L=1120|L=1010'),'F1A-G02-R03B':('3','16','L=1120')}.items():
        r=by.get(rid,{}); act=(r.get('bar_quantity','').strip(),r.get('bar_diameter_mm','').strip(),r.get('shape_or_length','').strip())
        if act!=exp: errors.append(f'{rid}: G02 correction mismatch')
    cc={r['candidate_id'].strip():r for r in cross}
    if cc.get('FND-C015',{}).get('promotion_state','').strip()!='REJECTED_AS_PHYSICAL_EDGE': errors.append('FND-C015 must remain rejected')
    if cc.get('FND-C016',{}).get('promotion_state','').strip()!='TRANSFORMED_TO_PHYSICAL_PATH': errors.append('FND-C016 must remain transformed through 22-prime')
    if len(topology)!=58: errors.append(f'topology expected 58, got {len(topology)}')
    direct=sum(r['reinforcement_binding_state'].strip()=='DIRECT_GROUP_BOUND' for r in topology); supported=sum(r['reinforcement_binding_state'].strip()=='SCHEMATIC_22_27_SPLIT_AT_22_PRIME' for r in topology); noauto=len(topology)-direct-supported
    if (direct,supported,noauto)!=(42,1,15): errors.append(f'member binding partition mismatch {(direct,supported,noauto)}')
    gb={r['check_id'].strip():r for r in gate}; expected={'M1F-REINF-001':'7','M1F-REINF-002':'7','M1F-REINF-003':'54','M1F-REINF-004':'5','M1F-REINF-005':'2','M1F-REINF-006':'0','M1F-REINF-007':'2','M1F-REINF-008':'2','M1F-REINF-009':'1','M1F-REINF-010':'42','M1F-REINF-011':'1','M1F-REINF-012':'15','M1F-REINF-013':'4','M1F-REINF-014':'3','M1F-REINF-015':'2','M1F-REINF-016':'1','M1F-REINF-017':'4','M1F-REINF-GATE':'PASS_GROUP_COVERAGE_WITH_TRANSCRIPTION_WATCHES'}
    for cid,exp in expected.items():
        act=gb.get(cid,{}).get('actual','').strip()
        if act!=exp: errors.append(f'{cid}: expected {exp}, got {act}')
    return report(errors,warnings,{'groups':len(groups),'base_reinforcement_rows':len(base),'effective_reinforcement_rows':len(reinf),'correction_patch_rows':len(patch),'groups_complete':complete,'groups_partial':partial,'groups_pending':pending,'open_transcription_rows':len(open_rows),'members_direct_group_bound':direct,'members_supported_group_bound':supported,'members_without_autonomous_group':noauto})
def report(errors,warnings,summary):
    state='PASS' if not errors else 'FAIL'; print(f'M1F_FOUNDATION_REINFORCEMENT_VALIDATION={state}')
    for k,v in summary.items(): print(f'{k}={v}')
    for w in warnings: print(f'WARNING: {w}')
    for e in errors: print(f'ERROR: {e}')
    return 0 if not errors else 1
if __name__=='__main__': sys.exit(main())
