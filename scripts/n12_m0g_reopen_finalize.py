#!/usr/bin/env python3
import csv,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; C=R/'data/canonical'
def rc(p):
 with p.open(encoding='utf-8-sig',newline='') as f:x=csv.DictReader(f);return list(x.fieldnames or []),list(x)
def wc(p,flds,rows):
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore');w.writeheader();w.writerows(rows)
def blob(p):return subprocess.check_output(['git','hash-object',str(p.relative_to(R))],cwd=R,text=True).strip()

# Require a green global topology gate before promotion.
f,gr=rc(C/'M0G_GLOBAL_TOPOLOGY_GATE_v1.csv'); ov=next((x for x in gr if x['check_id']=='GT-999'),None)
if not ov or ov.get('status')!='PASS' or any(x.get('severity')=='HARD' and x.get('status')=='FAIL' for x in gr):raise SystemExit('global topology gate not promotable')

# PT audits and QA summaries.
p=C/'PT_ANALYTICAL_NODES_AUDIT_v1.csv'; f,rows=rc(p)
u={'G7-NODE-002':('51','51 raster-QA-passed physical beams after local reopen'),'G7-NODE-003':('102','Two face endpoints per effective beam'),'G7-NODE-004':('102','Four new incidences retained for B-053/B-054'),'G7-NODE-005':('36','Four new incidences retain provenance WATCH'),'G7-NODE-006':('3','P18 now has three distinct face incidences'),'G7-NODE-007':('3','P23 now has three distinct face incidences')}
for r in rows:
 if r['audit_id'] in u:r['value'],r['note']=u[r['audit_id']]
wc(p,f,rows)

p=C/'PT_OVERLAY_QA_v1.csv'; f,rows=rc(p)
for r in rows:
 q=r['qa_id']
 if q=='G9-003':r['count']='51';r['metric_or_check']='51/51 topology-face QA PASS';r['note']='B-053/B-054 added by formal local reopen; zero topology rejects.'
 elif q=='G9-004':r['count']='51';r['metric_or_check']='34 plain PASS; 17 provenance/MIS WATCH';r['watch_items']='17'
 elif q=='G9-005':r['count']='102';r['metric_or_check']='102/102 points lie on support boundaries; 36 inherit MIS/WATCH provenance';r['watch_items']='36'
 elif q=='G9-006':r['count']='3';r['metric_or_check']='three distinct P18 face incidences including B-053'
 elif q=='G9-007':r['count']='3';r['metric_or_check']='three distinct P23 face incidences including B-054'
 elif q=='G9-010':r['watch_items']='20';r['metric_or_check']='zero topology rejects after B-053/B-054 local reopen';r['note']='Formal smallest-claim reopen revalidated; provenance preserved.'
wc(p,f,rows)

p=C/'PT_MASTER_REGENERATION_AUDIT_v1.csv'; f,rows=rc(p)
for r in rows:
 if r['audit_id']=='MASTER-REGEN-008':r['value']='102';r['note']='PT face-node inventory after formal B-053/B-054 reopen.'
 elif r['audit_id']=='MASTER-REGEN-009':r['value']='51';r['note']='Effective PT beams including B-052/B-053/B-054; revocations preserved.'
if not any(r['audit_id']=='MASTER-REGEN-015' for r in rows):rows.append({'audit_id':'MASTER-REGEN-015','metric':'local_m0g_reopen','value':'B-053 18-19; B-054 23-22-prime','status':'PASS','note':'Direct TAV-02S topology plus independent TAV-02A crosscheck.'})
wc(p,f,rows)

# PT handoff.
p=C/'PT_GEOMETRY_HANDOFF_v1.json'; d=json.loads(p.read_text(encoding='utf-8')); d['status']='CURRENT_HANDOFF_REVALIDATED_B053_B054';d['analytical_nodes']['count']=102;d['analytical_nodes']['extended_support_node_counts']['P18']=3;d['analytical_nodes']['extended_support_node_counts']['P23']=3;d['beams']['effective_physical_member_count']=51;d['beams']['added_after_source_closure']=['B-052','B-053','B-054'];d['validation']['effective_beams']=51;d['validation']['analytical_nodes']=102;d['validation']['topology_rejects']=0;d['local_reopen']={'id':'M0G-REOPEN-B053-B054','state':'CLOSED_REVALIDATED','evidence':'data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

# Assembly contract.
p=C/'M0G_ASSEMBLY_CONTRACT_v1.json'; d=json.loads(p.read_text(encoding='utf-8')); inv=d['frozen_inventory'];inv['g1_existing_beam_face_analytical_nodes']=102;inv['g1_effective_beams']=51;inv['ordinary_beams_all_storeys']=231;inv['ordinary_structural_member_segments']=358;d['member_assembly_rules']['pt_beams']='Use 51 effective PT beams; B-053 18-19 and B-054 23-22-prime are formal local-reopen additions from TAV-02S with TAV-02A crosscheck; prior revocations and duplicate suppression remain in force.';d['local_reopen_revision']={'id':'M0G-REOPEN-B053-B054','state':'CLOSED_REVALIDATED','evidence':'data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

# Global handoff with current blob identities.
p=C/'M0G_GEOMETRY_HANDOFF_v1.json'; d=json.loads(p.read_text(encoding='utf-8'));d['status']='CURRENT_WITH_WATCHES_REVALIDATED_B053_B054';d['promotion_decision']='PASS_WITH_WATCH';r=d['canonical_references'];r['assembly_contract']['git_blob_sha']=blob(C/'M0G_ASSEMBLY_CONTRACT_v1.json');r['analytical_nodes_3d']['git_blob_sha']=blob(C/'M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv');r['rigid_joint_links']['git_blob_sha']=blob(C/'M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv');r['member_connectivity']['git_blob_sha']=blob(C/'M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv');r['global_topology_gate']['git_blob_sha']=blob(C/'M0G_GLOBAL_TOPOLOGY_GATE_v1.csv');inv=d['frozen_inventory'];inv['analytical_nodes_total']=627;inv['beam_face_nodes']=462;inv['rigid_joint_links']=462;inv['ordinary_structural_members']=358;inv['ordinary_beams']=231;d['local_reopen_revision']={'id':'M0G-REOPEN-B053-B054','state':'CLOSED_REVALIDATED','new_g1_beams':['B-053','B-054'],'evidence':'data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

# M1-S gate recognizes the two DOC 50x20 reopened beams.
p=C/'M1S_SECTION_GATE_v1.csv'; f,rows=rc(p)
for r in rows:
 if r['gate_id']=='M1S-OTHER-BEAMS':r['total_items']='195';r['usable_section_items']='195';r['nd_section_items']='0';r['gate_status']='PASS';r['section_assignment_complete']='true';r['note']='Includes B-053 and B-054, each 50x20 DOC from TAV-02A.'
 elif r['gate_id']=='M1S-OVERALL':r['total_items']='358';r['usable_section_items']='358';r['nd_section_items']='0';r['gate_status']='PASS_WITH_WATCH';r['section_assignment_complete']='true';r['note']='All 358 ordinary members have usable sections; five pre-existing evidence watches remain.'
wc(p,f,rows)

# Close reopen ledger + decision.
p=C/'M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'; f,rows=rc(p)
for r in rows:r['reopen_state']='CLOSED_REVALIDATED'
wc(p,f,rows)
p=R/'docs/DECISIONI/M0G_REOPEN_PT_B053_B054_v1.md';s=p.read_text(encoding='utf-8').replace('Esito attuale: **M0G-REOPEN APPROVED — REVALIDATION REQUIRED**.','Esito finale: **M0G-REOPEN CLOSED — PASS_WITH_WATCH**. B-053/B-054 e le quattro incidenze sono stati rigenerati e revalidati deterministicamente.');p.write_text(s,encoding='utf-8')

# Machine checkpoint.
p=R/'knowledge/CURRENT_STATE.json';d=json.loads(p.read_text(encoding='utf-8'));d['m0g_geometry_status']='FROZEN_PASS_WITH_WATCH_REVALIDATED_B053_B054'
for x in d.get('stable_checkpoints',[]):
 if x.get('phase')=='M0-G-GLOBAL-GEOMETRY':x.update({'status':'FROZEN_PASS_WITH_WATCH_REVALIDATED_B053_B054','analytical_nodes':627,'rigid_joint_links':462,'ordinary_members':358,'ordinary_beams':231,'local_reopen':'B-053/B-054 CLOSED_REVALIDATED'})
 if x.get('phase')=='M1-S-SECTIONS':x['ordinary_members_with_usable_sections']=358
d['geometry_reopen_checkpoint']={'id':'M0G-REOPEN-B053-B054','state':'CLOSED_REVALIDATED','delta':{'g1_beams':2,'g1_face_nodes':4,'global_members':2,'global_nodes':4,'rigid_links':4}};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('M0G_REOPEN_FINALIZE=PASS_WITH_WATCH')
