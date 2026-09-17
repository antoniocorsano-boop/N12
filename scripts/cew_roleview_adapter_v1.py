from __future__ import annotations

import re
from typing import Any

ROLEVIEW_SCHEMA_VERSION = "roleview.v0"
PRODUCT_AUTHORITY = "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
ENGINEERING_AUTHORITY = "knowledge/CURRENT_STATE.json"
LIFECYCLE_AUTHORITY = "automation/CEW_PROJECT_LIFECYCLE_MODEL_v1.json"

VALID_ROLES = {"REVIEWER", "DEVELOPER"}
VALID_FOCI = {"PRODUCT_PROGRESS", "PRODUCT_PROMOTION"}

HARD_BLOCK_TOKENS = ("HUMAN_AUTHORITY_REQUIRED", "BLOCKED", "FAIL")


def build_cew_roleview(
    product_state: dict[str, Any],
    engineering_state: dict[str, Any],
    *,
    exact_revision: str,
    product_revision: str,
    engineering_revision: str,
    product_authority_path: str = PRODUCT_AUTHORITY,
    engineering_authority_path: str = ENGINEERING_AUTHORITY,
    focus: str = "PRODUCT_PROGRESS",
    role: str = "REVIEWER",
) -> dict[str, Any]:
    if focus not in VALID_FOCI:
        raise ValueError(f"Unsupported CEW RoleView focus: {focus}")
    if role not in VALID_ROLES:
        raise ValueError(f"Unsupported CEW RoleView role: {role}")

    exact_revision = exact_revision.strip()
    product_revision = product_revision.strip()
    engineering_revision = engineering_revision.strip()

    authority_errors = _authority_errors(
        product_state,
        engineering_state,
        product_authority_path,
        engineering_authority_path,
    )
    revision_errors = _revision_errors(
        exact_revision,
        product_revision,
        engineering_revision,
    )
    identity_errors = authority_errors + revision_errors

    product_item = product_state.get("current_product_work_item") or {}
    product_item_state = str(product_item.get("state") or "NOT_STARTED")
    promotion_blockers = _unique_strings(product_item.get("promotion_blockers") or [])

    projected_engineering = product_state.get("engineering_state") or {}
    engineering_automation = engineering_state.get("automation") or {}
    engineering_item_state = str(
        projected_engineering.get("current_work_item_state")
        or engineering_automation.get("last_result_decision")
        or engineering_state.get("status")
        or "NOT_STARTED"
    )

    evidence = [
        {
            "kind": "CEW_PRODUCT_STATE",
            "ref": product_authority_path,
            "label": "CEW product/runtime state authority",
        },
        {
            "kind": "N12_ENGINEERING_STATE",
            "ref": engineering_authority_path,
            "label": "N12 engineering state authority",
        },
        {
            "kind": "CEW_LIFECYCLE_MODEL",
            "ref": LIFECYCLE_AUTHORITY,
            "label": "CEW lifecycle semantics",
        },
    ]
    if exact_revision:
        evidence.append(
            {
                "kind": "GIT_EXACT_REVISION",
                "ref": exact_revision,
                "label": "Exact source revision",
            }
        )

    gates = _identity_gates(identity_errors, exact_revision)

    if focus == "PRODUCT_PROGRESS":
        gates.extend(
            _progress_gates(
                product_item_state=product_item_state,
                engineering_item_state=engineering_item_state,
                promotion_blockers=promotion_blockers,
            )
        )
        status = _progress_status(identity_errors, product_item_state)
    else:
        promotion_gates = _promotion_gates(
            product_state=product_state,
            product_item_state=product_item_state,
            promotion_blockers=promotion_blockers,
        )
        gates.extend(promotion_gates)
        status = _promotion_status(identity_errors, promotion_gates)

    blockers = _blocking_reasons(
        identity_errors=identity_errors,
        focus=focus,
        product_item_state=product_item_state,
        gates=gates,
    )

    capability_maturity = product_state.get("capability_maturity") or []
    provenance_watches = engineering_state.get("non_blocking_provenance_watches") or []

    snapshot = {
        "schemaVersion": ROLEVIEW_SCHEMA_VERSION,
        "product": "CEW",
        "scope": {
            "kind": "CEW_REFERENCE_PROJECT",
            "id": str(product_state.get("reference_project") or "N12"),
            "label": "CEW / N12",
        },
        "role": role,
        "focus": _focus_label(focus, role),
        "stage": focus,
        "status": status,
        "headline": _headline(focus, status),
        "maturity": _maturity_dimensions(
            identity_errors=identity_errors,
            focus=focus,
            product_item_state=product_item_state,
            engineering_item_state=engineering_item_state,
            promotion_blockers=promotion_blockers,
            product_state=product_state,
        ),
        "gates": gates,
        "kpis": [
            {
                "id": "exact_revision_present",
                "label": "Exact revision disponibile",
                "value": 1 if exact_revision else 0,
                "unit": "boolean",
                "target": 1,
                "source": "CEWRoleViewInput.exact_revision",
            },
            {
                "id": "authority_binding_errors",
                "label": "Errori di binding autoritativo",
                "value": len(authority_errors),
                "unit": "count",
                "target": 0,
                "source": f"{PRODUCT_AUTHORITY} + {ENGINEERING_AUTHORITY}",
            },
            {
                "id": "promotion_blocker_count",
                "label": "Blocker di promozione dichiarati",
                "value": len(promotion_blockers),
                "unit": "count",
                "target": 0,
                "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.promotion_blockers",
            },
            {
                "id": "capability_count",
                "label": "Capability dichiarate",
                "value": len(capability_maturity),
                "unit": "count",
                "source": f"{PRODUCT_AUTHORITY}:capability_maturity",
            },
            {
                "id": "production_ready_capabilities",
                "label": "Capability production-ready",
                "value": sum(
                    1
                    for capability in capability_maturity
                    if capability.get("production_ready") is True
                ),
                "unit": "count",
                "source": f"{PRODUCT_AUTHORITY}:capability_maturity[production_ready=true]",
            },
            {
                "id": "engineering_provenance_watches",
                "label": "Watch di provenienza ingegneristica",
                "value": len(provenance_watches),
                "unit": "count",
                "source": f"{ENGINEERING_AUTHORITY}:non_blocking_provenance_watches",
            },
        ],
        "blockers": blockers,
        "nextActions": [_next_action(focus, status)],
        "evidence": evidence,
        "provenance": [dict(item) for item in evidence],
    }
    return snapshot


def _authority_errors(
    product_state: dict[str, Any],
    engineering_state: dict[str, Any],
    product_authority_path: str,
    engineering_authority_path: str,
) -> list[str]:
    errors: list[str] = []
    if product_authority_path != PRODUCT_AUTHORITY:
        errors.append("PRODUCT_AUTHORITY_PATH_MISMATCH")
    if engineering_authority_path != ENGINEERING_AUTHORITY:
        errors.append("ENGINEERING_AUTHORITY_PATH_MISMATCH")
    if product_state.get("product") != "CEW":
        errors.append("PRODUCT_IDENTITY_MISMATCH")
    if product_state.get("state_role") != "CEW_PRODUCT_RUNTIME_STATE":
        errors.append("PRODUCT_STATE_ROLE_MISMATCH")

    projected = product_state.get("engineering_state") or {}
    if projected.get("authority_path") != ENGINEERING_AUTHORITY:
        errors.append("ENGINEERING_AUTHORITY_PROJECTION_MISMATCH")
    if projected.get("projection_policy") != "REFERENCE_ONLY_DO_NOT_DUPLICATE_ENGINEERING_FACTS_IN_CEW_PRODUCT_STATE":
        errors.append("ENGINEERING_PROJECTION_POLICY_MISMATCH")

    projected_item = projected.get("current_work_item")
    actual_item = (engineering_state.get("automation") or {}).get("current_work_item")
    if not projected_item or not actual_item or projected_item != actual_item:
        errors.append("ENGINEERING_CURRENT_WORK_ITEM_MISMATCH")

    product_reference = product_state.get("reference_project")
    projected_reference = projected.get("reference_project")
    if not product_reference or product_reference != projected_reference:
        errors.append("REFERENCE_PROJECT_MISMATCH")
    return _unique_strings(errors)


def _revision_errors(
    exact_revision: str,
    product_revision: str,
    engineering_revision: str,
) -> list[str]:
    errors: list[str] = []
    if not exact_revision:
        errors.append("EXACT_REVISION_MISSING")
    elif not re.fullmatch(r"[0-9a-fA-F]{40}", exact_revision):
        errors.append("EXACT_REVISION_INVALID")
    if not product_revision or product_revision != exact_revision:
        errors.append("PRODUCT_REVISION_MISMATCH")
    if not engineering_revision or engineering_revision != exact_revision:
        errors.append("ENGINEERING_REVISION_MISMATCH")
    return errors


def _identity_gates(identity_errors: list[str], exact_revision: str) -> list[dict[str, Any]]:
    authority_errors = [
        error for error in identity_errors if "REVISION" not in error
    ]
    revision_errors = [
        error for error in identity_errors if "REVISION" in error
    ]
    return [
        {
            "id": "SOURCE_AUTHORITY_BINDING",
            "label": "Binding delle autorità sorgente",
            "status": "BLOCKED" if authority_errors else "PASS",
            "reason": "; ".join(authority_errors) or None,
            "source": f"{PRODUCT_AUTHORITY} + {ENGINEERING_AUTHORITY}",
        },
        {
            "id": "EXACT_SOURCE_REVISION",
            "label": "Exact revision comune alle autorità",
            "status": "BLOCKED" if revision_errors else "PASS",
            "reason": "; ".join(revision_errors) or None,
            "source": "CEWRoleViewInput exact/product/engineering revision",
        },
    ]


def _progress_gates(
    *,
    product_item_state: str,
    engineering_item_state: str,
    promotion_blockers: list[str],
) -> list[dict[str, Any]]:
    if _is_hard_block(product_item_state):
        product_gate = "BLOCKED"
    elif _is_complete(product_item_state):
        product_gate = "PASS"
    else:
        product_gate = "WARN"

    engineering_gate = "PASS" if _is_complete(engineering_item_state) else "WARN"
    promotion_gate = "PASS" if not promotion_blockers else "WARN"

    return [
        {
            "id": "CURRENT_PRODUCT_WORK_ITEM",
            "label": "Work item prodotto corrente",
            "status": product_gate,
            "reason": None if product_gate == "PASS" else product_item_state,
            "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.state",
        },
        {
            "id": "ENGINEERING_REFERENCE_STATE",
            "label": "Stato ingegneristico di riferimento",
            "status": engineering_gate,
            "reason": None if engineering_gate == "PASS" else f"{engineering_item_state}: reference-only, nonblocking for product progress",
            "source": f"{ENGINEERING_AUTHORITY}:automation.last_result_decision",
        },
        {
            "id": "PRODUCT_PROMOTION_EVIDENCE",
            "label": "Evidenze di promozione prodotto",
            "status": promotion_gate,
            "reason": None if promotion_gate == "PASS" else f"{len(promotion_blockers)} blocker di promozione dichiarati",
            "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.promotion_blockers",
        },
    ]


def _promotion_gates(
    *,
    product_state: dict[str, Any],
    product_item_state: str,
    promotion_blockers: list[str],
) -> list[dict[str, Any]]:
    preview = (product_state.get("runtime") or {}).get("preview") or {}
    production = (product_state.get("runtime") or {}).get("production") or {}

    human_acceptance = str(preview.get("human_acceptance_status") or "NOT_EVALUATED")
    accessibility = str(preview.get("accessibility_status") or "NOT_EVALUATED")
    smoke_status = str(production.get("smoke_status") or "NOT_EVALUATED")
    promotion_authorized = preview.get("production_promotion_authorized") is True

    item_gate = (
        "BLOCKED"
        if _is_hard_block(product_item_state)
        else "PASS"
        if _is_complete(product_item_state)
        else "WARN"
    )

    return [
        {
            "id": "CURRENT_PRODUCT_WORK_ITEM",
            "label": "Work item prodotto corrente",
            "status": item_gate,
            "reason": None if item_gate == "PASS" else product_item_state,
            "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.state",
        },
        {
            "id": "PROMOTION_BLOCKERS",
            "label": "Blocker di promozione",
            "status": "PASS" if not promotion_blockers else "BLOCKED",
            "reason": None if not promotion_blockers else "; ".join(promotion_blockers),
            "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.promotion_blockers",
        },
        {
            "id": "HUMAN_ACCEPTANCE",
            "label": "Human Acceptance",
            "status": "PASS" if _is_pass(human_acceptance) else "BLOCKED",
            "reason": None if _is_pass(human_acceptance) else human_acceptance,
            "source": f"{PRODUCT_AUTHORITY}:runtime.preview.human_acceptance_status",
        },
        {
            "id": "ACCESSIBILITY",
            "label": "Accessibility gate",
            "status": "PASS" if _is_pass(accessibility) else "BLOCKED",
            "reason": None if _is_pass(accessibility) else accessibility,
            "source": f"{PRODUCT_AUTHORITY}:runtime.preview.accessibility_status",
        },
        {
            "id": "SAME_REVISION_PRODUCTION_SMOKE",
            "label": "Production smoke sulla stessa revisione",
            "status": "PASS" if _same_revision_smoke_pass(smoke_status) else "BLOCKED",
            "reason": None if _same_revision_smoke_pass(smoke_status) else smoke_status,
            "source": f"{PRODUCT_AUTHORITY}:runtime.production.smoke_status",
        },
        {
            "id": "PRODUCTION_PROMOTION_AUTHORIZED",
            "label": "Promozione production autorizzata",
            "status": "PASS" if promotion_authorized else "BLOCKED",
            "reason": None if promotion_authorized else "production_promotion_authorized=false",
            "source": f"{PRODUCT_AUTHORITY}:runtime.preview.production_promotion_authorized",
        },
    ]


def _progress_status(identity_errors: list[str], product_item_state: str) -> str:
    if identity_errors or _is_hard_block(product_item_state):
        return "BLOCKED"
    if _is_complete(product_item_state):
        return "READY"
    return "ATTENTION"


def _promotion_status(
    identity_errors: list[str],
    promotion_gates: list[dict[str, Any]],
) -> str:
    if identity_errors or any(gate["status"] == "BLOCKED" for gate in promotion_gates):
        return "BLOCKED"
    if any(gate["status"] == "WARN" for gate in promotion_gates):
        return "ATTENTION"
    return "READY"


def _blocking_reasons(
    *,
    identity_errors: list[str],
    focus: str,
    product_item_state: str,
    gates: list[dict[str, Any]],
) -> list[dict[str, str]]:
    blockers = [
        {
            "code": error,
            "label": error,
            "source": "CEW RoleView authority/revision binding",
        }
        for error in identity_errors
    ]
    if _is_hard_block(product_item_state):
        blockers.append(
            {
                "code": f"PRODUCT_WORK_ITEM:{product_item_state}",
                "label": f"Work item prodotto: {product_item_state}",
                "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.state",
            }
        )

    if focus == "PRODUCT_PROMOTION":
        for gate in gates:
            if gate["status"] != "BLOCKED":
                continue
            if gate["id"] in {"SOURCE_AUTHORITY_BINDING", "EXACT_SOURCE_REVISION", "CURRENT_PRODUCT_WORK_ITEM"}:
                continue
            blockers.append(
                {
                    "code": f"PROMOTION_GATE:{gate['id']}",
                    "label": gate.get("reason") or gate["label"],
                    "source": gate["source"],
                }
            )
    return _dedupe_blockers(blockers)


def _maturity_dimensions(
    *,
    identity_errors: list[str],
    focus: str,
    product_item_state: str,
    engineering_item_state: str,
    promotion_blockers: list[str],
    product_state: dict[str, Any],
) -> list[dict[str, str]]:
    source_state = "BLOCKED" if identity_errors else "READY"
    product_state_maturity = (
        "BLOCKED"
        if _is_hard_block(product_item_state)
        else "READY"
        if _is_complete(product_item_state)
        else "IN_PROGRESS"
    )
    engineering_state_maturity = (
        "READY" if _is_complete(engineering_item_state) else "IN_PROGRESS"
    )

    preview = (product_state.get("runtime") or {}).get("preview") or {}
    production = (product_state.get("runtime") or {}).get("production") or {}
    promotion_ready = (
        not promotion_blockers
        and _is_pass(str(preview.get("human_acceptance_status") or ""))
        and _is_pass(str(preview.get("accessibility_status") or ""))
        and _same_revision_smoke_pass(str(production.get("smoke_status") or ""))
        and preview.get("production_promotion_authorized") is True
    )
    promotion_state = "READY" if promotion_ready else "IN_PROGRESS"
    if focus == "PRODUCT_PROMOTION" and not identity_errors and not promotion_ready:
        promotion_state = "BLOCKED"

    return [
        {
            "id": "SOURCE_IDENTITY",
            "label": "Identità delle sorgenti",
            "state": source_state,
            "source": f"{PRODUCT_AUTHORITY} + {ENGINEERING_AUTHORITY}",
        },
        {
            "id": "PRODUCT_WORKFLOW",
            "label": "Workflow prodotto",
            "state": product_state_maturity,
            "source": f"{PRODUCT_AUTHORITY}:current_product_work_item.state",
        },
        {
            "id": "ENGINEERING_REFERENCE",
            "label": "Riferimento ingegneristico",
            "state": engineering_state_maturity,
            "source": f"{ENGINEERING_AUTHORITY}:automation.last_result_decision",
        },
        {
            "id": "PROMOTION_READINESS",
            "label": "Readiness di promozione",
            "state": promotion_state,
            "source": f"{PRODUCT_AUTHORITY}:runtime + current_product_work_item",
        },
        {
            "id": "EVIDENCE_PROVENANCE",
            "label": "Evidenze e provenienza",
            "state": source_state,
            "source": "CEW RoleView provenance",
        },
    ]


def _focus_label(focus: str, role: str) -> str:
    if focus == "PRODUCT_PROMOTION":
        return (
            "Gate, evidenze e provenienza per la promozione CEW"
            if role == "REVIEWER"
            else "Readiness tecnica della promozione CEW sulla stessa revisione"
        )
    return (
        "Avanzamento prodotto, residui locali ed evidenze CEW"
        if role == "REVIEWER"
        else "Coerenza del read model CEW e cause dello stato"
    )


def _headline(focus: str, status: str) -> str:
    if focus == "PRODUCT_PROMOTION":
        return {
            "READY": "CEW pronta alla promozione sulla revisione osservata",
            "ATTENTION": "Evidenze di promozione CEW in completamento",
            "BLOCKED": "Promozione CEW bloccata dai gate richiesti",
        }[status]
    return {
        "READY": "Avanzamento CEW pronto sul work item osservato",
        "ATTENTION": "Avanzamento CEW in corso con residui espliciti",
        "BLOCKED": "Avanzamento CEW bloccato da un vincolo rilevante",
    }[status]


def _next_action(focus: str, status: str) -> dict[str, str]:
    if focus == "PRODUCT_PROMOTION":
        actions = {
            "READY": ("PROMOTE_ON_EXACT_REVISION", "Promuovi CEW solo sulla stessa revisione"),
            "ATTENTION": ("COMPLETE_PROMOTION_EVIDENCE", "Completa le evidenze richieste per la promozione"),
            "BLOCKED": ("RESOLVE_PROMOTION_BLOCKERS", "Risolvi i blocker di promozione"),
        }
    else:
        actions = {
            "READY": ("REVIEW_NEXT_PRODUCT_SLICE", "Verifica il prossimo incremento prodotto"),
            "ATTENTION": ("CONTINUE_CURRENT_PRODUCT_SLICE", "Prosegui il work item prodotto corrente"),
            "BLOCKED": ("RESOLVE_PRODUCT_PROGRESS_BLOCKER", "Risolvi il vincolo che blocca l'avanzamento"),
        }
    action_id, label = actions[status]
    return {
        "id": action_id,
        "label": label,
        "priority": "PRIMARY",
        "source": "CEW RoleView derived status",
    }


def _is_complete(state: str) -> bool:
    value = state.upper()
    return value == "COMPLETE" or value.startswith("COMPLETE_") or value.endswith("_COMPLETE")


def _is_hard_block(state: str) -> bool:
    value = state.upper()
    return any(token in value for token in HARD_BLOCK_TOKENS)


def _is_pass(state: str) -> bool:
    value = state.strip().upper()
    return value in {"PASS", "PASSED", "SATISFIED", "ACCEPTED", "COMPLETE", "COMPLETED"}


def _same_revision_smoke_pass(state: str) -> bool:
    value = state.strip().upper()
    return "SAME_REVISION" in value and "PASS" in value and "REQUIRES" not in value and "NOT_" not in value


def _unique_strings(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


def _dedupe_blockers(blockers: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for blocker in blockers:
        if blocker["code"] in seen:
            continue
        seen.add(blocker["code"])
        result.append(blocker)
    return result
