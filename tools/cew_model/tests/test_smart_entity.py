import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('smart_entity',ROOT/'smart_entity.py')
M=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(M)

class SmartEntityTests(unittest.TestCase):
    def entity(self):
        return M.SmartStructuralEntity(
            entity_id='BUILDING/TEST/G1/BEAM/B1',project_id='TEST',entity_type='BEAM',
            generation=M.EntityGeneration('GEN-1','RECONSTRUCTION'),
            properties={
                'section':M.SmartProperty('25x70','cm','DOC',('CLAIM-SEC',)),
                'current_fc':M.SmartProperty(None,'MPa','ND'),
                'scenario_fc':M.SmartProperty(22.0,'MPa','MOD',(),model_rule_id='RULE-CONS-1',scenario_id='SCN-1')
            },
            topology_bindings=({'target_entity_id':'BUILDING/TEST/G1/NODE/N1','authority':'EVIDENCE','claim_id':'CLAIM-TOP'},),
            residual_ids=('RES-FC',)
        )
    def test_valid_entity(self):
        self.assertEqual(self.entity().validate(),[])
    def test_doc_requires_evidence(self):
        e=self.entity(); bad=M.SmartStructuralEntity(entity_id=e.entity_id,project_id=e.project_id,entity_type=e.entity_type,generation=e.generation,properties={'section':M.SmartProperty('25x70','cm','DOC')})
        self.assertTrue(any('requires evidence' in x for x in bad.validate()))
    def test_mod_requires_rule_and_scenario(self):
        p=M.SmartProperty(20,'MPa','MOD')
        errors=p.validate(); self.assertTrue(any('model_rule_id' in x for x in errors)); self.assertTrue(any('scenario_id' in x for x in errors))
    def test_nd_must_remain_null(self):
        self.assertTrue(M.SmartProperty(20,'MPa','ND').validate())
    def test_topology_needs_explicit_authority(self):
        e=self.entity(); bad=M.SmartStructuralEntity(entity_id=e.entity_id,project_id=e.project_id,entity_type=e.entity_type,generation=e.generation,topology_bindings=({'target_entity_id':'N2','authority':'PROXIMITY'},))
        self.assertTrue(any('topology binding' in x for x in bad.validate()))
    def test_solver_readiness_exposes_nd(self):
        r=self.entity().solver_readiness(['section','current_fc']); self.assertFalse(r['ready']); self.assertEqual(r['missing_or_unresolved'],['current_fc'])
    def test_next_generation_preserves_identity(self):
        e=self.entity(); n=e.next_generation('GEN-2','SURVEY_UPDATE')
        self.assertEqual(n.entity_id,e.entity_id); self.assertEqual(n.generation.supersedes_generation_id,'GEN-1'); self.assertEqual(n.validate(),[])
    def test_trace_property_retains_epistemic_lineage(self):
        t=self.entity().trace_property('section'); self.assertEqual(t['epistemic_state'],'DOC'); self.assertEqual(t['evidence_claim_ids'],['CLAIM-SEC'])

if __name__=='__main__': unittest.main()
