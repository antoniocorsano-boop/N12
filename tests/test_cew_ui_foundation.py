import unittest,json
from pathlib import Path
from scripts import validate_cew_ui_foundation as ux
ROOT=Path(__file__).resolve().parents[1]
class CEWUIFoundationTests(unittest.TestCase):
 def test_repository_contract_passes(self):self.assertEqual(ux.validate(ROOT),[])
 def test_raw_ids_cannot_be_primary(self):
  d=json.loads((ROOT/'automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json').read_text());self.assertFalse(d['internal_ids']['primary_ui_label'])
 def test_state_taxonomies_disjoint(self):
  d=json.loads((ROOT/'automation/CEW_ENGINEERING_DESIGN_SYSTEM_CONTRACT_v1.json').read_text());g=[set(v) for v in d['state_taxonomies'].values()];self.assertFalse(any(a&b for i,a in enumerate(g) for b in g[i+1:]))
 def test_decision_not_prefilled_or_direct_write(self):
  d=json.loads((ROOT/'automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json').read_text());self.assertFalse(d['human_authority']['engineering_decision_may_be_prefilled']);self.assertFalse(d['human_authority']['ui_may_write_canonical_directly'])
 def test_reference_shell_preserves_f2_boundary(self):
  t=(ROOT/'ui/foundation/reference/engineering-workspace.html').read_text();self.assertIn('EvidenceRegion congelata da CEW-F2',t);self.assertIn('Nessuna associazione preconfermata',t)
if __name__=='__main__':unittest.main()
