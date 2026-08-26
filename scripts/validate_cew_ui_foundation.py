#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED_EPISTEMIC = {"DOC", "MIS", "RIF", "INF", "ND"}
EXPECTED_WORKFLOW = {"READY", "RUNNING", "IN_REVIEW", "BLOCKED", "COMPLETE", "FAILED"}
EXPECTED_SEVERITY = {"OK", "ATTENTION", "CRITICAL", "NOT_ASSESSED"}
REQUIRED_COMPONENTS = {
    "ProjectContextBar",
    "EngineeringEvidenceCard",
    "EpistemicStateMark",
    "EngineeringInspector",
    "EvidenceDecisionTrail",
    "HumanDecisionPanel",
    "TechnicalDataTable",
    "SourceModelSplitView",
    "ProvenanceDrawer",
    "EngineeringStateBanner",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(root: Path):
    errors = []
    paths = [
        "docs/UX/CEW_HUMAN_ENGINEERING_EXPERIENCE_MODEL_v1.md",
        "docs/UX/CEW_ENGINEERING_DESIGN_SYSTEM_v1.md",
        "docs/UX/CEW_ENGINEERING_INFORMATION_ARCHITECTURE_v1.md",
        "docs/UX/CEW_UI_OPEN_SOURCE_ADOPTION_MATRIX_v1.md",
        "automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json",
        "automation/CEW_ENGINEERING_DESIGN_SYSTEM_CONTRACT_v1.json",
        "automation/CEW_UX_FOUNDATION_WORK_QUEUE_v1.json",
        "ui/foundation/tokens/cew.tokens.json",
        "ui/foundation/contracts/component-catalog.json",
        "ui/foundation/contracts/information-architecture.json",
        "ui/foundation/cew-engineering.css",
        "ui/foundation/reference/engineering-workspace.html",
    ]
    for rel in paths:
        if not (root / rel).exists():
            errors.append(f"missing {rel}")
    if errors:
        return errors

    human = load(root / "automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json")
    design = load(root / "automation/CEW_ENGINEERING_DESIGN_SYSTEM_CONTRACT_v1.json")
    tokens = load(root / "ui/foundation/tokens/cew.tokens.json")
    catalog = load(root / "ui/foundation/contracts/component-catalog.json")
    queue = load(root / "automation/CEW_UX_FOUNDATION_WORK_QUEUE_v1.json")
    ia = load(root / "ui/foundation/contracts/information-architecture.json")

    if human.get("primary_professional_role") != "CIVIL_STRUCTURAL_ENGINEER_EXISTING_BUILDINGS":
        errors.append("primary professional role drift")
    if human["internal_ids"].get("primary_ui_label") is not False:
        errors.append("raw IDs may not be primary UI labels")
    if human["human_authority"].get("ui_may_write_canonical_directly") is not False:
        errors.append("UI canonical write boundary violated")
    if human["human_authority"].get("engineering_decision_may_be_prefilled") is not False:
        errors.append("engineering decision prefill forbidden")

    states = design.get("state_taxonomies", {})
    state_sets = [
        set(states.get("EPISTEMIC", [])),
        set(states.get("WORKFLOW", [])),
        set(states.get("ENGINEERING_SEVERITY", [])),
    ]
    if state_sets[0] != EXPECTED_EPISTEMIC or state_sets[1] != EXPECTED_WORKFLOW or state_sets[2] != EXPECTED_SEVERITY:
        errors.append("state taxonomy drift")
    if any(a & b for i, a in enumerate(state_sets) for b in state_sets[i + 1:]):
        errors.append("state taxonomies must be disjoint")
    if design["state_rules"].get("color_only_encoding_allowed") is not False:
        errors.append("color-only state encoding forbidden")
    if design["third_party_boundary"].get("viewer_geometry_is_evidence_authority") is not False:
        errors.append("viewer may not become evidence authority")

    names = {item["name"] for item in catalog.get("components", [])}
    if not REQUIRED_COMPONENTS <= names:
        errors.append("required engineering component missing")
    for item in catalog.get("components", []):
        if item.get("raw_ids_primary") is not False:
            errors.append(f"{item.get('name')}: raw ID primary label")
        accessibility = item.get("accessibility", {})
        if not all(accessibility.get(key) is True for key in ("keyboard_operable", "visible_focus", "state_not_color_only")):
            errors.append(f"{item.get('name')}: accessibility contract incomplete")

    for taxonomy in ("epistemic", "workflow", "severity"):
        for name, spec in tokens.get(taxonomy, {}).items():
            if not spec.get("label") or not spec.get("icon"):
                errors.append(f"{taxonomy}.{name}: text/icon missing")

    items = {item["id"]: item for item in queue.get("items", [])}
    if set(items) != {"UX0-001", "UX1-001"}:
        errors.append("UX work queue mismatch")
    if queue.get("canonical_promotion") != "DISABLED":
        errors.append("UX queue may not promote canonically")
    ux1 = items.get("UX1-001", {})
    if ux1.get("canonical_context") != "CEW-F2":
        errors.append("UX1 queue must read the CEW-F2 canonical context")
    if ux1.get("authority") != "EXPERIMENTAL_NON_PROMOTIVE":
        errors.append("UX1 queue must remain experimental and non-promotive")

    slice_spec = ia.get("ux1_vertical_slice", {})
    if "f7_vertical_slice" in ia:
        errors.append("UX foundation must not model an unauthorized F7 vertical slice")
    if slice_spec.get("canonical_context") != "CEW-F2":
        errors.append("UX1 IA must read CEW-F2")
    if slice_spec.get("authority") != "EXPERIMENTAL_NON_PROMOTIVE":
        errors.append("UX1 IA authority drift")

    reference = (root / "ui/foundation/reference/engineering-workspace.html").read_text(encoding="utf-8")
    if "EvidenceRegion congelata da CEW-F2" not in reference:
        errors.append("reference shell must declare frozen F2 region")
    if "Nessuna associazione preconfermata" not in reference:
        errors.append("reference shell may not preconfirm binding")

    governance_surface = "\n".join([
        (root / "docs/UX/CEW_ENGINEERING_INFORMATION_ARCHITECTURE_v1.md").read_text(encoding="utf-8"),
        (root / "automation/CEW_UX_FOUNDATION_WORK_QUEUE_v1.json").read_text(encoding="utf-8"),
        (root / "ui/foundation/contracts/information-architecture.json").read_text(encoding="utf-8"),
    ])
    if re.search(r"\b(?:CEW-)?F7\b", governance_surface):
        errors.append("UX foundation must not claim CEW-F7 authority")

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print("CEW UX FOUNDATION = FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(
        "CEW UX FOUNDATION = PASS\n"
        "Primary role = CIVIL_STRUCTURAL_ENGINEER_EXISTING_BUILDINGS\n"
        "STATE_TAXONOMIES = DISJOINT\n"
        "COLOR_ONLY_STATE = FORBIDDEN\n"
        "DIRECT_CANONICAL_UI_WRITE = FORBIDDEN\n"
        "UX1_CANONICAL_CONTEXT = CEW-F2\n"
        "UX1_AUTHORITY = EXPERIMENTAL_NON_PROMOTIVE\n"
        "UX0-001 = READY_FOR_RECEIPT"
    )


if __name__ == "__main__":
    main()
