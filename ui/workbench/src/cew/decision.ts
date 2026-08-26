import type { DecisionOutcome } from './model';
import { snapshot } from './model';

export type DecisionProposal = {
  schema_version: '1.0';
  proposal_type: 'NON_PROMOTIVE_HUMAN_DECISION_PROPOSAL';
  review_mode: 'HUMAN_REVIEW';
  task_context: {
    work_item: 'UX1-001';
    canonical_context: 'CEW-F2';
    authority: 'EXPERIMENTAL_NON_PROMOTIVE';
    evidence_region_id: string;
    source_version_id: string;
    canonical_snapshot_id: string;
    canonical_commit: string;
  };
  reviewer: string;
  outcome: DecisionOutcome;
  human_observation: string;
  target_id: '';
  direct_primary_evidence_observed: true;
  authority_acknowledgement: string;
  canonical_write: false;
};

export function buildDecisionProposal(
  reviewer: string,
  outcome: DecisionOutcome,
  humanObservation: string
): DecisionProposal {
  const reviewerValue = reviewer.trim();
  const observationValue = humanObservation.trim();
  if (!reviewerValue) throw new Error('Il revisore è obbligatorio.');
  if (!observationValue) throw new Error('L’osservazione tecnica è obbligatoria.');

  return {
    schema_version: '1.0',
    proposal_type: 'NON_PROMOTIVE_HUMAN_DECISION_PROPOSAL',
    review_mode: 'HUMAN_REVIEW',
    task_context: {
      work_item: 'UX1-001',
      canonical_context: 'CEW-F2',
      authority: 'EXPERIMENTAL_NON_PROMOTIVE',
      evidence_region_id: snapshot.evidence_region.id,
      source_version_id: snapshot.source.source_version_id,
      canonical_snapshot_id: snapshot.snapshot_id,
      canonical_commit: snapshot.canonical_commit
    },
    reviewer: reviewerValue,
    outcome,
    human_observation: observationValue,
    target_id: '',
    direct_primary_evidence_observed: true,
    authority_acknowledgement: snapshot.decision.authority_acknowledgement,
    canonical_write: false
  };
}
