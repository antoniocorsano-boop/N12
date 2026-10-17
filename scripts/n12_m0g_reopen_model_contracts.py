#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def p(path,repls):
 s=path.read_text(encoding='utf-8'); o=s
 for a,b in repls:
  if a in s:s=s.replace(a,b)
  elif b not in s:raise RuntimeError(f'missing token {a} in {path}')
 if s!=o:path.write_text(s,encoding='utf-8')

m=R/'scripts/n12_generate_m0g_member_connectivity.py'
p(m,[
('pt_patch = read_csv(CAN / "PT_VECTOR_BEAMS_G6_PATCH_v1.csv")','pt_patch = read_csv(CAN / "PT_VECTOR_BEAMS_G6_PATCH_v1.csv")\nreopen_rows = read_csv(CAN / "M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv")\nreopen_sections = {r["beam_id"]: r for r in reopen_rows}'),
('"section_hint": "",\n            "evidence_basis": "DOC_DIRECT_SOURCE_PATCH",','"section_hint": reopen_sections.get(p["beam_id"], {}).get("section_cm", ""),\n            "evidence_basis": "DOC_DIRECT_SOURCE_PATCH",'),
('if len(pt_effective) != 49:','if len(pt_effective) != 51:'),('PT effective beam count != 49','PT effective beam count != 51'),
('("TOTAL_MEMBER_ROWS", 356,','("TOTAL_MEMBER_ROWS", 358,'),('("ORDINARY_BEAM_ROWS", 229,','("ORDINARY_BEAM_ROWS", 231,'),('49 G1 + 180 G2-G5','51 G1 + 180 G2-G5'),('("G1_BEAMS", 49,','("G1_BEAMS", 51,'),('("UNIQUE_MEMBER_IDS", 356,','("UNIQUE_MEMBER_IDS", 358,')])

g=R/'scripts/n12_generate_m0g_global_topology_gate.py'
p(g,[
('"GT-001", "inventory", "HARD", 623, len(ns), len(ns) == 623','"GT-001", "inventory", "HARD", 627, len(ns), len(ns) == 627'),
('"GT-002", "inventory", "HARD", 458, len(ls), len(ls) == 458','"GT-002", "inventory", "HARD", 462, len(ls), len(ls) == 462'),
('"GT-003", "inventory", "HARD", 356, len(ms), len(ms) == 356','"GT-003", "inventory", "HARD", 358, len(ms), len(ms) == 358'),
('BEAM_FACE_INCIDENCE_NODE','BEAM_SUPPORT_FACE')])
print('M0G_REOPEN_MODEL_CONTRACTS=PASS')
