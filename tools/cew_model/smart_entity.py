from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "CEW_SMART_STRUCTURAL_ENTITY_v0.json"


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class SmartProperty:
    value: Any
    unit: str | None
    epistemic_state: str
    evidence_claim_ids: tuple[str, ...] = ()
    model_rule_id: str | None = None
    scenario_id: str | None = None
    note: str | None = None

    def validate(self, contract: dict[str, Any] | None = None) -> list[str]:
        contract = contract or load_contract()
        errors: list[str] = []
        rules = contract["property_rules"]
        if self.epistemic_state not in rules:
            return [f"unknown epistemic_state: {self.epistemic_state}"]
        rule = rules[self.epistemic_state]
        if rule.get("requires_null_value") and self.value is not None:
            errors.append("ND property must have null value")
        if rule.get("requires_evidence") and not self.evidence_claim_ids:
            errors.append(f"{self.epistemic_state} property requires evidence")
        if len(self.evidence_claim_ids) < rule.get("minimum_evidence", 0):
            errors.append(f"{self.epistemic_state} property requires at least {rule['minimum_evidence']} evidence claims")
        if rule.get("requires_model_rule") and not self.model_rule_id:
            errors.append(f"{self.epistemic_state} property requires model_rule_id")
        if rule.get("requires_scenario") and not self.scenario_id:
            errors.append(f"{self.epistemic_state} property requires scenario_id")
        if self.epistemic_state in {"DOC", "MIS", "RIF", "INF", "INC", "ND"} and self.scenario_id:
            errors.append(f"{self.epistemic_state} property cannot be scenario-owned")
        return errors


@dataclass(frozen=True)
class EntityGeneration:
    generation_id: str
    change_kind: str
    supersedes_generation_id: str | None = None
    source_model_generation_id: str | None = None

    def validate(self, contract: dict[str, Any] | None = None) -> list[str]:
        contract = contract or load_contract()
        errors: list[str] = []
        if not self.generation_id:
            errors.append("generation_id is required")
        if self.change_kind not in contract["generation_change_kinds"]:
            errors.append(f"unknown change_kind: {self.change_kind}")
        if self.supersedes_generation_id == self.generation_id:
            errors.append("generation cannot supersede itself")
        return errors


@dataclass(frozen=True)
class SmartStructuralEntity:
    entity_id: str
    project_id: str
    entity_type: str
    generation: EntityGeneration
    label: str | None = None
    properties: dict[str, SmartProperty] = field(default_factory=dict)
    evidence_claim_ids: tuple[str, ...] = ()
    geometry_bindings: tuple[dict[str, Any], ...] = ()
    topology_bindings: tuple[dict[str, Any], ...] = ()
    scenario_bindings: tuple[dict[str, Any], ...] = ()
    degradation_bindings: tuple[dict[str, Any], ...] = ()
    solver_mappings: tuple[dict[str, Any], ...] = ()
    intervention_bindings: tuple[dict[str, Any], ...] = ()
    quantity_cost_bindings: tuple[dict[str, Any], ...] = ()
    residual_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self, contract: dict[str, Any] | None = None) -> list[str]:
        contract = contract or load_contract()
        errors: list[str] = []
        if not self.entity_id or not self.project_id:
            errors.append("entity_id and project_id are required")
        if self.entity_type not in contract["entity_types"]:
            errors.append(f"unknown entity_type: {self.entity_type}")
        errors.extend(self.generation.validate(contract))
        for name, prop in self.properties.items():
            for error in prop.validate(contract):
                errors.append(f"property {name}: {error}")
        for binding in self.topology_bindings:
            if binding.get("authority") not in {"EVIDENCE", "ADMITTED_RULE"}:
                errors.append("topology binding requires explicit EVIDENCE or ADMITTED_RULE authority")
        for mapping in self.solver_mappings:
            for required in ("adapter_id", "scenario_id", "solver_entity_id", "export_receipt_id"):
                if not mapping.get(required):
                    errors.append(f"solver mapping missing {required}")
        for binding in self.quantity_cost_bindings:
            if not binding.get("entity_generation_id"):
                errors.append("quantity/cost binding missing entity_generation_id")
            if not (binding.get("model_generation_id") or binding.get("price_generation_id")):
                errors.append("quantity/cost binding requires model_generation_id or price_generation_id")
        return errors

    def trace_property(self, name: str) -> dict[str, Any]:
        prop = self.properties[name]
        return {
            "entity_id": self.entity_id,
            "entity_generation_id": self.generation.generation_id,
            "property": name,
            "value": prop.value,
            "unit": prop.unit,
            "epistemic_state": prop.epistemic_state,
            "evidence_claim_ids": list(prop.evidence_claim_ids),
            "model_rule_id": prop.model_rule_id,
            "scenario_id": prop.scenario_id,
        }

    def solver_readiness(self, required_properties: list[str]) -> dict[str, Any]:
        missing: list[str] = []
        invalid: dict[str, list[str]] = {}
        for name in required_properties:
            prop = self.properties.get(name)
            if prop is None or prop.epistemic_state in {"ND", "INC"}:
                missing.append(name)
            elif errors := prop.validate():
                invalid[name] = errors
        return {
            "entity_id": self.entity_id,
            "ready": not missing and not invalid,
            "missing_or_unresolved": missing,
            "invalid": invalid,
        }

    def next_generation(self, generation_id: str, change_kind: str, **changes: Any) -> "SmartStructuralEntity":
        payload = asdict(self)
        payload.update(copy.deepcopy(changes))
        payload["generation"] = EntityGeneration(
            generation_id=generation_id,
            change_kind=change_kind,
            supersedes_generation_id=self.generation.generation_id,
            source_model_generation_id=self.generation.source_model_generation_id,
        )
        # Restore nested SmartProperty objects after asdict conversion when unchanged.
        if "properties" not in changes:
            payload["properties"] = dict(self.properties)
        return SmartStructuralEntity(**payload)

    def to_dict(self) -> dict[str, Any]:
        def prop_dict(prop: SmartProperty) -> dict[str, Any]:
            data = asdict(prop)
            data["evidence_claim_ids"] = list(prop.evidence_claim_ids)
            return data

        return {
            "entity_id": self.entity_id,
            "project_id": self.project_id,
            "entity_type": self.entity_type,
            "generation": asdict(self.generation),
            "label": self.label,
            "properties": {k: prop_dict(v) for k, v in self.properties.items()},
            "evidence_claim_ids": list(self.evidence_claim_ids),
            "geometry_bindings": list(self.geometry_bindings),
            "topology_bindings": list(self.topology_bindings),
            "scenario_bindings": list(self.scenario_bindings),
            "degradation_bindings": list(self.degradation_bindings),
            "solver_mappings": list(self.solver_mappings),
            "intervention_bindings": list(self.intervention_bindings),
            "quantity_cost_bindings": list(self.quantity_cost_bindings),
            "residual_ids": list(self.residual_ids),
            "metadata": copy.deepcopy(self.metadata),
        }
