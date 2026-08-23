#!/usr/bin/env python3
import csv
from pathlib import Path

R=Path(__file__).resolve().parents[1]; C=R/'data/canonical'

def rc(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        x=csv.DictReader(f); return list(x.fieldnames or []),list(x)
def wc(p,flds,rows):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
def pt(p,repls):
    s=p.read_text(encoding='utf-8'); o=s
    for a,b in repls:
        if a in s: s=s.replace(a,b)
        elif b not in s: raise RuntimeError(f'missing patch token in {p}: {a}')
    if s!=o: p.write_text(s,encoding='utf-8')

# Beam patch.
p=C/'PT_VECTOR_BEAMS_G6_PATCH_v1.csv'; f,rows=rc(p); ids={r['beam_id'] for r in rows}
adds=[
{'patch_id':'G6VP-004','action':'ADD','beam_id':'B-053','support_i':'18','support_j':'19','orientation':'OBLIQUE_NEAR_VERTICAL','x_i_face_m':'7.2384','y_i_face_m':'4.8500','x_j_face_m':'7.6078','y_j_face_m':'8.7000','clear_vector_length_m':'3.8677','vector_status':'WORKING_VECTOR_DIRECT_SOURCE','source':'TAV-02S r2_c2 + TAV-02A','note':'Formal M0G local reopen: direct 18-19 carpenteria line; TAV-02A sequence 18-19-20 crosscheck.'},
{'patch_id':'G6VP-005','action':'ADD','beam_id':'B-054','support_i':'23','support_j':"22'",'orientation':'OBLIQUE_NEAR_VERTICAL','x_i_face_m':'5.2406','y_i_face_m':'23.2500','x_j_face_m':'5.5344','y_j_face_m':'19.4800','clear_vector_length_m':'3.7814','vector_status':'WORKING_VECTOR_DIRECT_SOURCE','source':'TAV-02S r3_c2 + TAV-02A','note':'Formal M0G local reopen: direct 23-22-prime carpenteria line; TAV-02A sequence 23-22-prime-22-21 crosscheck.'}]
for a in adds:
    if a['beam_id'] not in ids: rows.append(a)
wc(p,f,rows)

# Four distinct face incidences.
p=C/'PT_ANALYTICAL_NODES_v1.csv'; f,rows=rc(p); ids={r['node_id'] for r in rows}
new=[
{'node_id':'AN-099','support_id':'18','x_m':'7.2384','y_m':'4.8500','face_ref':'SOUTH','attached_beams':'B-053','beam_count':'1','support_metric_evidence':'MIS_AFFINE_EXTENDED','node_evidence_status':'WATCH','node_role':'BEAM_TO_SUPPORT_FACE'},
{'node_id':'AN-100','support_id':'19','x_m':'7.6078','y_m':'8.7000','face_ref':'NORTH','attached_beams':'B-053','beam_count':'1','support_metric_evidence':'MIS_AFFINE_WATCH','node_evidence_status':'WATCH','node_role':'BEAM_TO_SUPPORT_FACE'},
{'node_id':'AN-101','support_id':'23','x_m':'5.2406','y_m':'23.2500','face_ref':'NORTH','attached_beams':'B-054','beam_count':'1','support_metric_evidence':'MIS_AFFINE_EXTENDED','node_evidence_status':'WATCH','node_role':'BEAM_TO_SUPPORT_FACE'},
{'node_id':'AN-102','support_id':"22'",'x_m':'5.5344','y_m':'19.4800','face_ref':'SOUTH','attached_beams':'B-054','beam_count':'1','support_metric_evidence':'SUPPORTED_REFERENCE_PLUS_MIS','node_evidence_status':'WATCH','node_role':'BEAM_TO_SUPPORT_FACE'}]
for n in new:
    if n['node_id'] not in ids: rows.append(n)
wc(p,f,rows)

# Master references.
p=C/'PT_MASTER_CURRENT.csv'; f,rows=rc(p); m={r['entity_id']:r for r in rows}
refs={'18':'AN-099@SOUTH(7.2384,4.8500)[B-053]','19':'AN-100@NORTH(7.6078,8.7000)[B-053]','23':'AN-101@NORTH(5.2406,23.2500)[B-054]',"22'":'AN-102@SOUTH(5.5344,19.4800)[B-054]'}
for sid,ref in refs.items():
    a=[x for x in m[sid].get('analytical_nodes','').split(';') if x]
    if ref not in a: a.append(ref)
    m[sid]['analytical_nodes']=';'.join(a); m[sid]['analytical_node_count']=str(len(a))
wc(p,f,rows)

# Raster QA.
p=C/'PT_VECTOR_BEAMS_RASTER_QA_v1.csv'; f,rows=rc(p); ids={r['beam_id'] for r in rows}
for a in [
{'beam_id':'B-053','qa_scope':'M0G_REOPEN_18_19','source_tile':'r2_c2','topology_face_qa':'PASS','metric_overlay_qa':'PASS_WITH_MIS_WATCH','evidence_basis':'DIRECT_RASTER_PLUS_TAV02A_CROSSCHECK','note':'Direct 18-19 line; endpoint metrics retain P18/P19 watches.'},
{'beam_id':'B-054','qa_scope':'M0G_REOPEN_23_22PRIME','source_tile':'r3_c2','topology_face_qa':'PASS','metric_overlay_qa':'PASS_WITH_MIS_WATCH','evidence_basis':'DIRECT_RASTER_PLUS_TAV02A_CROSSCHECK','note':'Direct 23-22-prime line; P23 gets a distinct third face incidence.'}]:
    if a['beam_id'] not in ids: rows.append(a)
wc(p,f,rows)

# Validator/generator inventory contracts.
pt(R/'scripts/validate_pt_master_current.py',[
('if len(effective_beams) != 49:','if len(effective_beams) != 51:'),('effective physical beam count must be 49','effective physical beam count must be 51'),
('if len(nodes) != 98:','if len(nodes) != 102:'),('analytical node row count must be 98','analytical node row count must be 102'),
('if len(refs) != 98:','if len(refs) != 102:'),('Master must contain 98 analytical node references','Master must contain 102 analytical node references'),
('if len(set(refs)) != 98:','if len(set(refs)) != 102:'),('expected_extended_counts = {"18": 2, "23": 2, "30": 3}','expected_extended_counts = {"18": 3, "23": 3, "30": 3}')])
pt(R/'scripts/n12_generate_m0g_3d_nodes.py',[
('if len(pt_face_nodes) != 98:','if len(pt_face_nodes) != 102:'),('PT face-node count {len(pt_face_nodes)} != 98','PT face-node count {len(pt_face_nodes)} != 102'),
('if role_counts["BEAM_SUPPORT_FACE"] != 458:','if role_counts["BEAM_SUPPORT_FACE"] != 462:'),("beam-face count {role_counts['BEAM_SUPPORT_FACE']} != 458","beam-face count {role_counts['BEAM_SUPPORT_FACE']} != 462"),
('if len(rows) != 623:','if len(rows) != 627:'),('global node count {len(rows)} != 623','global node count {len(rows)} != 627'),
('expected_level_nodes = {"G1": 136, "G2": 130, "G3": 130, "G4": 130, "G5": 97}','expected_level_nodes = {"G1": 140, "G2": 130, "G3": 130, "G4": 130, "G5": 97}'),
('audit("TOTAL_3D_NODE_ROWS", 623, len(rows))','audit("TOTAL_3D_NODE_ROWS", 627, len(rows))'),('audit("G1_REUSED_PT_FACE_ROWS", 98, len(pt_face_nodes))','audit("G1_REUSED_PT_FACE_ROWS", 102, len(pt_face_nodes))'),('audit("UNIQUE_NODE_IDS", 623, len(set(ids)))','audit("UNIQUE_NODE_IDS", 627, len(set(ids)))')])
pt(R/'scripts/n12_generate_m0g_rigid_links.py',[
('("TOTAL_RIGID_LINK_ROWS", 458,','("TOTAL_RIGID_LINK_ROWS", 462,'),('("G1_RIGID_LINK_ROWS", 98,','("G1_RIGID_LINK_ROWS", 102,'),('("UNIQUE_LINK_IDS", 458,','("UNIQUE_LINK_IDS", 462,'),('("UNIQUE_FACE_NODE_TARGETS", 458,','("UNIQUE_FACE_NODE_TARGETS", 462,'),('("SAME_SUPPORT_LINKS", 458,','("SAME_SUPPORT_LINKS", 462,'),('("SAME_LEVEL_LINKS", 458,','("SAME_LEVEL_LINKS", 462,')])
print('M0G_REOPEN_PREPARE_INPUTS=PASS')
