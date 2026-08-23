#!/usr/bin/env python3
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]; C=R/'data/canonical'
def rc(p):
 with p.open(encoding='utf-8-sig',newline='') as f:x=csv.DictReader(f);return list(x.fieldnames or []),list(x)
def wc(p,flds,rows):
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore');w.writeheader();w.writerows(rows)
def pt(p,repls):
 s=p.read_text(encoding='utf-8');o=s
 for a,b in repls:
  if a in s:s=s.replace(a,b)
  elif b not in s:raise RuntimeError(f'missing token {a} in {p}')
 if s!=o:p.write_text(s,encoding='utf-8')

# Evidence ledger: third smallest-claim reopen.
p=C/'M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv';f,rows=rc(p)
if not any(r['beam_id']=='B-055' for r in rows):
 rows.append({'reopen_id':'M0G-REOPEN-003','beam_id':'B-055','support_i':'17','support_j':'18','primary_geometry_source':'TAV-02S','primary_source_tile':'r2_c2','crosscheck_source':'TAV-02A','source_interpretation':'Direct continuous carpenteria line between registered supports 17 and 18; TAV-02A paired reinforcement scheme labels 17-18-19-20.','section_cm':'50x20','section_evidence':'DOC_TAV02A','topology_evidence':'DOC_TAV02S','native_i_u_px':'2345.57','native_i_v_px':'2819.68','native_j_u_px':'2400.06','native_j_v_px':'3560.21','face_i':'SOUTH','face_i_x_m':'6.9138','face_i_y_m':'0.2000','face_j':'NORTH','face_j_x_m':'7.2137','face_j_y_m':'4.5500','clear_length_m':'4.3603','reopen_state':'APPROVED_LOCAL_REOPEN','note':'New beam only; exact face coordinates are analytical derivations and retain support provenance.'})
wc(p,f,rows)

p=C/'PT_VECTOR_BEAMS_G6_PATCH_v1.csv';f,rows=rc(p)
if not any(r['beam_id']=='B-055' for r in rows):
 rows.append({'patch_id':'G6VP-006','action':'ADD','beam_id':'B-055','support_i':'17','support_j':'18','orientation':'OBLIQUE_NEAR_VERTICAL','x_i_face_m':'6.9138','y_i_face_m':'0.2000','x_j_face_m':'7.2137','y_j_face_m':'4.5500','clear_vector_length_m':'4.3603','vector_status':'WORKING_VECTOR_DIRECT_SOURCE','source':'TAV-02S r2_c2 + TAV-02A','note':'Formal local reopen: direct 17-18 carpenteria line; TAV-02A sequence 17-18-19-20 crosscheck.'})
wc(p,f,rows)

p=C/'PT_ANALYTICAL_NODES_v1.csv';f,rows=rc(p);ids={r['node_id'] for r in rows}
for n in [
{'node_id':'AN-103','support_id':'17','x_m':'6.9138','y_m':'0.2000','face_ref':'SOUTH','attached_beams':'B-055','beam_count':'1','support_metric_evidence':'DOC_METRIC_OR_AXIS','node_evidence_status':'PASS','node_role':'BEAM_TO_SUPPORT_FACE'},
{'node_id':'AN-104','support_id':'18','x_m':'7.2137','y_m':'4.5500','face_ref':'NORTH','attached_beams':'B-055','beam_count':'1','support_metric_evidence':'MIS_AFFINE_EXTENDED','node_evidence_status':'WATCH','node_role':'BEAM_TO_SUPPORT_FACE'}]:
 if n['node_id'] not in ids:rows.append(n)
wc(p,f,rows)

p=C/'PT_MASTER_CURRENT.csv';f,rows=rc(p);m={r['entity_id']:r for r in rows}
for sid,ref in {'17':'AN-103@SOUTH(6.9138,0.2000)[B-055]','18':'AN-104@NORTH(7.2137,4.5500)[B-055]'}.items():
 a=[x for x in m[sid].get('analytical_nodes','').split(';') if x]
 if ref not in a:a.append(ref)
 m[sid]['analytical_nodes']=';'.join(a);m[sid]['analytical_node_count']=str(len(a))
wc(p,f,rows)

p=C/'PT_VECTOR_BEAMS_RASTER_QA_v1.csv';f,rows=rc(p)
if not any(r['beam_id']=='B-055' for r in rows):rows.append({'beam_id':'B-055','qa_scope':'M0G_REOPEN_17_18','source_tile':'r2_c2','topology_face_qa':'PASS','metric_overlay_qa':'PASS_WITH_MIS_WATCH','evidence_basis':'DIRECT_RASTER_PLUS_TAV02A_CROSSCHECK','note':'Direct 17-18 line; P17 endpoint DOC, P18 endpoint retains MIS provenance.'})
wc(p,f,rows)

pt(R/'scripts/validate_pt_master_current.py',[
('if len(effective_beams) != 51:','if len(effective_beams) != 52:'),('effective physical beam count must be 51','effective physical beam count must be 52'),('if len(nodes) != 102:','if len(nodes) != 104:'),('analytical node row count must be 102','analytical node row count must be 104'),('if len(refs) != 102:','if len(refs) != 104:'),('Master must contain 102 analytical node references','Master must contain 104 analytical node references'),('if len(set(refs)) != 102:','if len(set(refs)) != 104:'),('expected_extended_counts = {"18": 3, "23": 3, "30": 3}','expected_extended_counts = {"18": 4, "23": 3, "30": 3}')])
pt(R/'scripts/n12_generate_m0g_3d_nodes.py',[
('if len(pt_face_nodes) != 102:','if len(pt_face_nodes) != 104:'),('PT face-node count {len(pt_face_nodes)} != 102','PT face-node count {len(pt_face_nodes)} != 104'),('if role_counts["BEAM_SUPPORT_FACE"] != 462:','if role_counts["BEAM_SUPPORT_FACE"] != 464:'),("beam-face count {role_counts['BEAM_SUPPORT_FACE']} != 462","beam-face count {role_counts['BEAM_SUPPORT_FACE']} != 464"),('if len(rows) != 627:','if len(rows) != 629:'),('global node count {len(rows)} != 627','global node count {len(rows)} != 629'),('expected_level_nodes = {"G1": 140, "G2": 130, "G3": 130, "G4": 130, "G5": 97}','expected_level_nodes = {"G1": 142, "G2": 130, "G3": 130, "G4": 130, "G5": 97}'),('audit("TOTAL_3D_NODE_ROWS", 627, len(rows))','audit("TOTAL_3D_NODE_ROWS", 629, len(rows))'),('audit("G1_REUSED_PT_FACE_ROWS", 102, len(pt_face_nodes))','audit("G1_REUSED_PT_FACE_ROWS", 104, len(pt_face_nodes))'),('audit("UNIQUE_NODE_IDS", 627, len(set(ids)))','audit("UNIQUE_NODE_IDS", 629, len(set(ids)))')])
pt(R/'scripts/n12_generate_m0g_rigid_links.py',[
('("TOTAL_RIGID_LINK_ROWS", 462,','("TOTAL_RIGID_LINK_ROWS", 464,'),('("G1_RIGID_LINK_ROWS", 102,','("G1_RIGID_LINK_ROWS", 104,'),('("UNIQUE_LINK_IDS", 462,','("UNIQUE_LINK_IDS", 464,'),('("UNIQUE_FACE_NODE_TARGETS", 462,','("UNIQUE_FACE_NODE_TARGETS", 464,'),('("SAME_SUPPORT_LINKS", 462,','("SAME_SUPPORT_LINKS", 464,'),('("SAME_LEVEL_LINKS", 462,','("SAME_LEVEL_LINKS", 464,')])
pt(R/'scripts/n12_generate_m0g_member_connectivity.py',[
('if len(pt_effective) != 51:','if len(pt_effective) != 52:'),('PT effective beam count != 51','PT effective beam count != 52'),('("TOTAL_MEMBER_ROWS", 358,','("TOTAL_MEMBER_ROWS", 359,'),('("ORDINARY_BEAM_ROWS", 231,','("ORDINARY_BEAM_ROWS", 232,'),('51 G1 + 180 G2-G5','52 G1 + 180 G2-G5'),('("G1_BEAMS", 51,','("G1_BEAMS", 52,'),('("UNIQUE_MEMBER_IDS", 358,','("UNIQUE_MEMBER_IDS", 359,')])
pt(R/'scripts/n12_generate_m0g_global_topology_gate.py',[
('"GT-001", "inventory", "HARD", 627, len(ns), len(ns) == 627','"GT-001", "inventory", "HARD", 629, len(ns), len(ns) == 629'),('"GT-002", "inventory", "HARD", 462, len(ls), len(ls) == 462','"GT-002", "inventory", "HARD", 464, len(ls), len(ls) == 464'),('"GT-003", "inventory", "HARD", 358, len(ms), len(ms) == 358','"GT-003", "inventory", "HARD", 359, len(ms), len(ms) == 359')])
print('M0G_REOPEN_B055_PREPARE=PASS')
