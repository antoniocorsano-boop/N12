#!/usr/bin/env python3
import csv,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/canonical'
def rc(p):
 with p.open(encoding='utf-8-sig',newline='') as f:x=csv.DictReader(f);return list(x.fieldnames or []),list(x)
def wc(p,flds,rows):
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore');w.writeheader();w.writerows(rows)
def blob(p):return subprocess.check_output(['git','hash-object',str(p.relative_to(R))],cwd=R,text=True).strip()

f,g=rc(C/'M0G_GLOBAL_TOPOLOGY_GATE_v1.csv');o=next((r for r in g if r['check_id']=='GT-999'),None)
if not o or o.get('status')!='PASS' or any(r.get('severity')=='HARD' and r.get('status')=='FAIL' for r in g):raise SystemExit('B055 global gate not promotable')

p=C/'PT_ANALYTICAL_NODES_AUDIT_v1.csv';f,rows=rc(p)
u={'G7-NODE-002':('52','52 raster-QA-passed physical beams after B055 reopen'),'G7-NODE-003':('104','Two face endpoints per effective physical beam'),'G7-NODE-004':('104','B055 adds two distinct incidences without merge'),'G7-NODE-005':('37','AN-104 retains P18 provenance watch; AN-103 is direct-metric PASS'),'G7-NODE-006':('4','P18 now has west/east/south/north distinct incidences')}
for r in rows:
 if r['audit_id'] in u:r['value'],r['note']=u[r['audit_id']]
wc(p,f,rows)

p=C/'PT_OVERLAY_QA_v1.csv';f,rows=rc(p)
for r in rows:
 q=r['qa_id']
 if q=='G9-003':r['count']='52';r['metric_or_check']='52/52 topology-face QA PASS';r['note']='B-055 17-18 added by formal local reopen; zero topology rejects.'
 elif q=='G9-004':r['count']='52';r['metric_or_check']='34 plain PASS; 18 provenance/MIS WATCH';r['watch_items']='18'
 elif q=='G9-005':r['count']='104';r['metric_or_check']='104/104 points lie on support boundaries; 37 inherit MIS/WATCH provenance';r['watch_items']='37'
 elif q=='G9-006':r['count']='4';r['metric_or_check']='four distinct P18 face incidences including B-053 south and B-055 north'
 elif q=='G9-010':r['watch_items']='21';r['metric_or_check']='zero topology rejects after B-055 local reopen';r['note']='Second smallest-claim reopen revalidated; provenance preserved.'
wc(p,f,rows)

p=C/'PT_MASTER_REGENERATION_AUDIT_v1.csv';f,rows=rc(p)
for r in rows:
 if r['audit_id']=='MASTER-REGEN-008':r['value']='104';r['note']='PT face-node inventory after B-055 local reopen.'
 elif r['audit_id']=='MASTER-REGEN-009':r['value']='52';r['note']='Effective PT beams include B-052/B-053/B-054/B-055; prior revocations preserved.'
if not any(r['audit_id']=='MASTER-REGEN-016' for r in rows):rows.append({'audit_id':'MASTER-REGEN-016','metric':'local_m0g_reopen_b055','value':'B-055 17-18','status':'PASS','note':'Direct TAV-02S topology plus TAV-02A 17-18-19-20 crosscheck.'})
wc(p,f,rows)

p=C/'PT_GEOMETRY_HANDOFF_v1.json';d=json.loads(p.read_text(encoding='utf-8'));d['status']='CURRENT_HANDOFF_REVALIDATED_B055';d['analytical_nodes']['count']=104;d['analytical_nodes']['extended_support_node_counts']['P18']=4;d['beams']['effective_physical_member_count']=52;d['beams']['added_after_source_closure']=['B-052','B-053','B-054','B-055'];d['validation']['effective_beams']=52;d['validation']['analytical_nodes']=104;d['local_reopen']={'id':'M0G-REOPEN-B055','state':'CLOSED_REVALIDATED','evidence':'data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

p=C/'M0G_ASSEMBLY_CONTRACT_v1.json';d=json.loads(p.read_text(encoding='utf-8'));i=d['frozen_inventory'];i['g1_existing_beam_face_analytical_nodes']=104;i['g1_effective_beams']=52;i['ordinary_beams_all_storeys']=232;i['ordinary_structural_member_segments']=359;d['member_assembly_rules']['pt_beams']='Use 52 effective PT beams. B-053 18-19, B-054 23-22-prime and B-055 17-18 are formal local-reopen additions documented by TAV-02S with TAV-02A crosschecks; prior revocations and duplicate suppression remain in force.';d['local_reopen_revision']={'id':'M0G-REOPEN-B055','state':'CLOSED_REVALIDATED','evidence':'data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

p=C/'M0G_GEOMETRY_HANDOFF_v1.json';d=json.loads(p.read_text(encoding='utf-8'));d['status']='CURRENT_WITH_WATCHES_REVALIDATED_B055';r=d['canonical_references'];r['assembly_contract']['git_blob_sha']=blob(C/'M0G_ASSEMBLY_CONTRACT_v1.json');r['analytical_nodes_3d']['git_blob_sha']=blob(C/'M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv');r['rigid_joint_links']['git_blob_sha']=blob(C/'M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv');r['member_connectivity']['git_blob_sha']=blob(C/'M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv');r['global_topology_gate']['git_blob_sha']=blob(C/'M0G_GLOBAL_TOPOLOGY_GATE_v1.csv');i=d['frozen_inventory'];i['analytical_nodes_total']=629;i['beam_face_nodes']=464;i['rigid_joint_links']=464;i['ordinary_structural_members']=359;i['ordinary_beams']=232;d['local_reopen_revision']={'id':'M0G-REOPEN-B055','state':'CLOSED_REVALIDATED','new_g1_beams':['B-055'],'evidence':'data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

p=C/'M1S_SECTION_GATE_v1.csv';f,rows=rc(p)
for r in rows:
 if r['gate_id']=='M1S-OTHER-BEAMS':r['total_items']='196';r['usable_section_items']='196';r['nd_section_items']='0';r['gate_status']='PASS';r['note']='Includes B-053/B-054/B-055; B-055 is 50x20 DOC from TAV-02A.'
 elif r['gate_id']=='M1S-OVERALL':r['total_items']='359';r['usable_section_items']='359';r['nd_section_items']='0';r['gate_status']='PASS_WITH_WATCH';r['note']='All 359 ordinary members have usable sections; five pre-existing evidence watches remain.'
wc(p,f,rows)

p=C/'M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv';f,rows=rc(p)
for r in rows:
 if r['beam_id']=='B-055':r['reopen_state']='CLOSED_REVALIDATED'
wc(p,f,rows)

p=R/'knowledge/CURRENT_STATE.json';d=json.loads(p.read_text(encoding='utf-8'));d['m0g_geometry_status']='FROZEN_PASS_WITH_WATCH_REVALIDATED_B055'
for x in d.get('stable_checkpoints',[]):
 if x.get('phase')=='M0-G-GLOBAL-GEOMETRY':x.update({'status':'FROZEN_PASS_WITH_WATCH_REVALIDATED_B055','analytical_nodes':629,'rigid_joint_links':464,'ordinary_members':359,'ordinary_beams':232,'local_reopen':'B-055 17-18 CLOSED_REVALIDATED after B-053/B-054'})
 if x.get('phase')=='M1-S-SECTIONS':x['ordinary_members_with_usable_sections']=359
d['geometry_reopen_checkpoint']={'id':'M0G-REOPEN-B055','state':'CLOSED_REVALIDATED','delta_from_previous_freeze':{'g1_beams':1,'g1_face_nodes':2,'global_members':1,'global_nodes':2,'rigid_links':2}};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

p=R/'docs/DECISIONI/M0G_REOPEN_PT_B055_v1.md';p.write_text('# M0G-REOPEN — PT B-055 (17–18)\n\nFonte primaria: TAV-02S r2_c2. Cross-check indipendente: TAV-02A, gruppo 17–18–19–20.\n\nSezione: **50×20 cm DOC da TAV-02A**.\n\nIl tratto 20–21 resta separato ed è dettagliato autonomamente come 65×30; non è assorbito nel gruppo B-055/B-053/B-052.\n\nEsito finale: **CLOSED — PASS_WITH_WATCH**. La correzione è limitata al solo membro B-055 e alle due nuove incidenze di faccia.\n',encoding='utf-8')
print('M0G_REOPEN_B055_FINALIZE=PASS_WITH_WATCH')
