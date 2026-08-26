import unittest

from tools.cew_intervention.contract import (
    Deficiency,
    Objective,
    SystemReference,
    InterventionCandidate,
    HumanDecisionReceipt,
    build_selection_package,
    decision_receipt,
    proposed_intervention_generation,
    human_first_package,
)


class InterventionContractTests(unittest.TestCase):
    def deficiency(self, state='DOC', evidence=('EV-1',)):
        return Deficiency(
            deficiency_id='DEF-1',
            entity_id='BEAM-1',
            property_key='section_capacity',
            statement='Capacity verification requires an intervention option.',
            epistemic_state=state,
            evidence_refs=evidence,
            source_generation_ids=('MODEL-GEN-1',),
            uncertainty='material parameters still under review',
        )

    def objective(self):
        return Objective(
            objective_id='OBJ-1',
            deficiency_ids=('DEF-1',),
            statement='Restore the required verification margin without losing provenance.',
            acceptance_criteria=('verification margin documented', 'constructability reviewed'),
        )

    def reference(self):
        return SystemReference(
            reference_id='REF-1',
            source_type='TECHNICAL_SYSTEM_REFERENCE',
            locator='manufacturer-or-standard-record',
            version_label='v2026-08',
            captured_at='2026-08-26T11:00:00+00:00',
            fingerprint='sha256:' + 'a' * 64,
        )

    def candidate(self):
        return InterventionCandidate(
            candidate_id='INT-CAND-1',
            title='Candidate strengthening system',
            deficiency_ids=('DEF-1',),
            objective_ids=('OBJ-1',),
            reference_ids=('REF-1',),
            applicability_constraints=('substrate condition must be verified', 'anchorage detail requires design'),
            expected_effects={'capacity_modifier': 'PROPOSED_NOT_VERIFIED'},
            assumptions=('final dimensions not selected',),
        )

    def package(self):
        return build_selection_package(
            [self.deficiency()], [self.objective()], [self.reference()], [self.candidate()]
        )

    def test_nd_cannot_become_deficiency(self):
        with self.assertRaises(ValueError):
            self.deficiency(state='ND', evidence=()).validate()

    def test_doc_deficiency_requires_evidence(self):
        with self.assertRaises(ValueError):
            self.deficiency(state='DOC', evidence=()).validate()

    def test_reference_must_be_versioned_and_fingerprinted(self):
        bad = SystemReference('REF-X', 'SYSTEM', 'locator', '', '2026-08-26', '')
        with self.assertRaises(ValueError):
            bad.validate()

    def test_candidate_requires_applicability_constraints(self):
        c = self.candidate()
        bad = InterventionCandidate(
            candidate_id=c.candidate_id,
            title=c.title,
            deficiency_ids=c.deficiency_ids,
            objective_ids=c.objective_ids,
            reference_ids=c.reference_ids,
            applicability_constraints=(),
            expected_effects=c.expected_effects,
        )
        with self.assertRaises(ValueError):
            bad.validate()

    def test_package_rejects_unknown_reference(self):
        c = self.candidate()
        bad = InterventionCandidate(
            candidate_id=c.candidate_id,
            title=c.title,
            deficiency_ids=c.deficiency_ids,
            objective_ids=c.objective_ids,
            reference_ids=('MISSING-REF',),
            applicability_constraints=c.applicability_constraints,
            expected_effects=c.expected_effects,
        )
        with self.assertRaises(ValueError):
            build_selection_package([self.deficiency()], [self.objective()], [self.reference()], [bad])

    def test_no_proposed_generation_without_human_approve(self):
        package = self.package()
        decision = decision_receipt(package, 'DEFER', 'engineer', 'Need more evidence.')
        with self.assertRaises(ValueError):
            proposed_intervention_generation(package, decision, {'entity_id': 'BEAM-1', 'properties': {}})

    def test_source_drift_invalidates_decision(self):
        package = self.package()
        decision = HumanDecisionReceipt(
            decision_id='INTDEC-X',
            package_id=package.package_id,
            decision='APPROVE',
            selected_candidate_id='INT-CAND-1',
            reviewer='engineer',
            rationale='Selected for proposal only.',
            source_fingerprint='sha256:drifted',
            decided_at='2026-08-26T11:00:00+00:00',
        )
        with self.assertRaises(ValueError):
            decision.validate_for(package)

    def test_approve_creates_only_proposed_noncanonical_generation(self):
        package = self.package()
        decision = decision_receipt(
            package, 'APPROVE', 'engineer', 'Candidate selected for detailed verification.', 'INT-CAND-1'
        )
        base = {'entity_id': 'BEAM-1', 'properties': {'section': 'existing'}}
        generation = proposed_intervention_generation(package, decision, base)
        self.assertEqual(generation['state'], 'PROPOSED_NOT_CANONICAL')
        self.assertEqual(generation['canonical_promotion'], 'DISABLED')
        self.assertTrue(generation['requires_engineering_validation'])
        self.assertEqual(base, {'entity_id': 'BEAM-1', 'properties': {'section': 'existing'}})
        self.assertEqual(generation['base_entity_snapshot'], base)
        self.assertEqual(generation['overlay']['intervention_candidate_id'], 'INT-CAND-1')

    def test_human_package_is_decision_oriented_and_provenanced(self):
        package = self.package()
        view = human_first_package(package)
        self.assertEqual(view['state'], 'PENDING_HUMAN_DECISION')
        self.assertEqual(view['allowed_decisions'], ['APPROVE', 'REJECT', 'DEFER'])
        self.assertEqual(view['provenance']['source_fingerprint'], package.source_fingerprint)
        self.assertEqual(view['provenance']['canonical_promotion'], 'DISABLED')


if __name__ == '__main__':
    unittest.main()
