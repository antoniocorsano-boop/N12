from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Deficiency:
    deficiency_id: str
    entity_id: str
    property_key: str
    statement: str
    epistemic_state: str
    evidence_refs: tuple[str, ...]
    source_generation_ids: tuple[str, ...]
    uncertainty: str | None = None

    def validate(self) -> None:
        if not self.deficiency_id or not self.entity_id or not self.property_key or not self.statement:
            raise ValueError('deficiency identity, entity, property and statement are required')
        if self.epistemic_state == 'ND':
            raise ValueError('ND cannot be promoted into an engineering deficiency')
        if self.epistemic_state in {'DOC', 'MIS'} and not self.evidence_refs:
            raise ValueError('DOC/MIS deficiency requires evidence refs')
        if not self.source_generation_ids:
            raise ValueError('deficiency must bind to at least one source/model generation')


@dataclass(frozen=True)
class Objective:
    objective_id: str
    deficiency_ids: tuple[str, ...]
    statement: str
    acceptance_criteria: tuple[str, ...]

    def validate(self) -> None:
        if not self.objective_id or not self.statement:
            raise ValueError('objective identity and statement are required')
        if not self.deficiency_ids:
            raise ValueError('objective must address at least one deficiency')
        if not self.acceptance_criteria:
            raise ValueError('objective requires explicit acceptance criteria')


@dataclass(frozen=True)
class SystemReference:
    reference_id: str
    source_type: str
    locator: str
    version_label: str
    captured_at: str
    fingerprint: str

    def validate(self) -> None:
        for value in (self.reference_id, self.source_type, self.locator, self.version_label, self.captured_at, self.fingerprint):
            if not str(value).strip():
                raise ValueError('versioned intervention reference fields are all required')


@dataclass(frozen=True)
class InterventionCandidate:
    candidate_id: str
    title: str
    deficiency_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    reference_ids: tuple[str, ...]
    applicability_constraints: tuple[str, ...]
    expected_effects: dict[str, Any]
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    state: str = 'CANDIDATE'

    def validate(self) -> None:
        if self.state != 'CANDIDATE':
            raise ValueError('new intervention candidates must start as CANDIDATE')
        if not self.candidate_id or not self.title:
            raise ValueError('candidate identity and title are required')
        if not self.deficiency_ids or not self.objective_ids:
            raise ValueError('candidate must bind deficiency and objective')
        if not self.reference_ids:
            raise ValueError('candidate requires at least one versioned system/market/reference source')
        if not self.applicability_constraints:
            raise ValueError('candidate applicability constraints must be explicit')
        if not self.expected_effects:
            raise ValueError('candidate expected effects must be explicit proposals')


@dataclass(frozen=True)
class InterventionSelectionPackage:
    package_id: str
    deficiencies: tuple[Deficiency, ...]
    objectives: tuple[Objective, ...]
    references: tuple[SystemReference, ...]
    candidates: tuple[InterventionCandidate, ...]
    source_fingerprint: str
    canonical_promotion: str = 'DISABLED'

    def validate(self) -> None:
        if not self.candidates:
            raise ValueError('selection package requires candidates')
        for item in self.deficiencies:
            item.validate()
        for item in self.objectives:
            item.validate()
        for item in self.references:
            item.validate()
        for item in self.candidates:
            item.validate()
        deficiencies = {x.deficiency_id for x in self.deficiencies}
        objectives = {x.objective_id for x in self.objectives}
        references = {x.reference_id for x in self.references}
        for obj in self.objectives:
            if not set(obj.deficiency_ids).issubset(deficiencies):
                raise ValueError('objective references unknown deficiency')
        for candidate in self.candidates:
            if not set(candidate.deficiency_ids).issubset(deficiencies):
                raise ValueError('candidate references unknown deficiency')
            if not set(candidate.objective_ids).issubset(objectives):
                raise ValueError('candidate references unknown objective')
            if not set(candidate.reference_ids).issubset(references):
                raise ValueError('candidate references unknown versioned source')


@dataclass(frozen=True)
class HumanDecisionReceipt:
    decision_id: str
    package_id: str
    decision: str
    selected_candidate_id: str | None
    reviewer: str
    rationale: str
    source_fingerprint: str
    decided_at: str

    def validate_for(self, package: InterventionSelectionPackage) -> None:
        if self.package_id != package.package_id:
            raise ValueError('decision package mismatch')
        if self.source_fingerprint != package.source_fingerprint:
            raise ValueError('source fingerprint drift: decision invalid')
        if self.decision not in {'APPROVE', 'REJECT', 'DEFER'}:
            raise ValueError('invalid intervention decision')
        if not self.reviewer.strip() or not self.rationale.strip():
            raise ValueError('reviewer and rationale are required')
        if self.decision == 'APPROVE' and not self.selected_candidate_id:
            raise ValueError('APPROVE requires selected_candidate_id')
        if self.selected_candidate_id and self.selected_candidate_id not in {x.candidate_id for x in package.candidates}:
            raise ValueError('selected candidate is not in package')


def build_selection_package(
    deficiencies: list[Deficiency],
    objectives: list[Objective],
    references: list[SystemReference],
    candidates: list[InterventionCandidate],
) -> InterventionSelectionPackage:
    body = {
        'deficiencies': [asdict(x) for x in deficiencies],
        'objectives': [asdict(x) for x in objectives],
        'references': [asdict(x) for x in references],
        'candidates': [asdict(x) for x in candidates],
    }
    package = InterventionSelectionPackage(
        package_id='INTPKG-' + uuid.uuid4().hex[:12],
        deficiencies=tuple(deficiencies),
        objectives=tuple(objectives),
        references=tuple(references),
        candidates=tuple(candidates),
        source_fingerprint=stable_hash(body),
    )
    package.validate()
    return package


def decision_receipt(
    package: InterventionSelectionPackage,
    decision: str,
    reviewer: str,
    rationale: str,
    selected_candidate_id: str | None = None,
) -> HumanDecisionReceipt:
    receipt = HumanDecisionReceipt(
        decision_id='INTDEC-' + uuid.uuid4().hex[:12],
        package_id=package.package_id,
        decision=decision,
        selected_candidate_id=selected_candidate_id,
        reviewer=reviewer,
        rationale=rationale,
        source_fingerprint=package.source_fingerprint,
        decided_at=now(),
    )
    receipt.validate_for(package)
    return receipt


def proposed_intervention_generation(
    package: InterventionSelectionPackage,
    decision: HumanDecisionReceipt,
    base_entity_snapshot: dict[str, Any],
) -> dict[str, Any]:
    decision.validate_for(package)
    if decision.decision != 'APPROVE':
        raise ValueError('only an APPROVE human decision can create a proposed intervention generation')
    candidate = next(x for x in package.candidates if x.candidate_id == decision.selected_candidate_id)
    untouched = deepcopy(base_entity_snapshot)
    return {
        'generation_id': 'INTGEN-' + uuid.uuid4().hex[:12],
        'state': 'PROPOSED_NOT_CANONICAL',
        'selected_candidate': asdict(candidate),
        'selection_decision_id': decision.decision_id,
        'selection_source_fingerprint': decision.source_fingerprint,
        'base_entity_fingerprint': stable_hash(base_entity_snapshot),
        'base_entity_snapshot': untouched,
        'overlay': {
            'intervention_candidate_id': candidate.candidate_id,
            'expected_effects': deepcopy(candidate.expected_effects),
            'applicability_constraints': list(candidate.applicability_constraints),
            'assumptions': list(candidate.assumptions),
        },
        'canonical_promotion': 'DISABLED',
        'requires_engineering_validation': True,
    }


def human_first_package(package: InterventionSelectionPackage) -> dict[str, Any]:
    package.validate()
    return {
        'title': 'Scelta intervento proposta',
        'question': 'Quale candidato, se presente, è tecnicamente appropriato da portare alla generazione proposta?',
        'state': 'PENDING_HUMAN_DECISION',
        'deficiencies': [
            {'id': d.deficiency_id, 'element': d.entity_id, 'issue': d.statement, 'uncertainty': d.uncertainty}
            for d in package.deficiencies
        ],
        'objectives': [
            {'id': o.objective_id, 'objective': o.statement, 'acceptance': list(o.acceptance_criteria)}
            for o in package.objectives
        ],
        'candidates': [
            {
                'id': c.candidate_id,
                'title': c.title,
                'constraints': list(c.applicability_constraints),
                'expected_effects_are_proposals': c.expected_effects,
                'references': list(c.reference_ids),
            }
            for c in package.candidates
        ],
        'provenance': {
            'package_id': package.package_id,
            'source_fingerprint': package.source_fingerprint,
            'canonical_promotion': package.canonical_promotion,
        },
        'allowed_decisions': ['APPROVE', 'REJECT', 'DEFER'],
    }
