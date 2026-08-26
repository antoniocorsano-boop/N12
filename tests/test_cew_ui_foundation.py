import json
import unittest
from pathlib import Path

from scripts import validate_cew_ui_foundation as ux

ROOT = Path(__file__).resolve().parents[1]


class CEWUIFoundationTests(unittest.TestCase):
    def test_repository_contract_passes(self):
        self.assertEqual(ux.validate(ROOT), [])

    def test_raw_ids_cannot_be_primary(self):
        data = json.loads((ROOT / 'automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json').read_text())
        self.assertFalse(data['internal_ids']['primary_ui_label'])

    def test_state_taxonomies_disjoint(self):
        data = json.loads((ROOT / 'automation/CEW_ENGINEERING_DESIGN_SYSTEM_CONTRACT_v1.json').read_text())
        groups = [set(value) for value in data['state_taxonomies'].values()]
        self.assertFalse(any(a & b for i, a in enumerate(groups) for b in groups[i + 1:]))

    def test_decision_not_prefilled_or_direct_write(self):
        data = json.loads((ROOT / 'automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json').read_text())
        self.assertFalse(data['human_authority']['engineering_decision_may_be_prefilled'])
        self.assertFalse(data['human_authority']['ui_may_write_canonical_directly'])

    def test_reference_shell_preserves_f2_boundary(self):
        text = (ROOT / 'ui/foundation/reference/engineering-workspace.html').read_text()
        self.assertIn('EvidenceRegion congelata da CEW-F2', text)
        self.assertIn('Nessuna associazione preconfermata', text)

    def test_ux1_is_work_item_in_f2_context_not_f7_milestone(self):
        queue = json.loads((ROOT / 'automation/CEW_UX_FOUNDATION_WORK_QUEUE_v1.json').read_text())
        ux1 = next(item for item in queue['items'] if item['id'] == 'UX1-001')
        self.assertEqual(ux1['canonical_context'], 'CEW-F2')
        self.assertEqual(ux1['authority'], 'EXPERIMENTAL_NON_PROMOTIVE')

        ia = json.loads((ROOT / 'ui/foundation/contracts/information-architecture.json').read_text())
        self.assertNotIn('f7_vertical_slice', ia)
        self.assertEqual(ia['ux1_vertical_slice']['canonical_context'], 'CEW-F2')
        self.assertEqual(ia['ux1_vertical_slice']['authority'], 'EXPERIMENTAL_NON_PROMOTIVE')

        doc = (ROOT / 'docs/UX/CEW_ENGINEERING_INFORMATION_ARCHITECTURE_v1.md').read_text()
        self.assertNotIn('F7', doc)


if __name__ == '__main__':
    unittest.main()
