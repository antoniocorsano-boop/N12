#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_cew_canonical_patch_candidates as patch_builder
import cew_project_home as project_home
import cew_source_evidence_workspace as workspace

SOURCE_CONTRACT = ROOT / "docs/PRODUCT/CEW_SOURCE_HUB_V1_CONTRACT.md"
EVIDENCE_CONTRACT = ROOT / "docs/PRODUCT/CEW_EVIDENCE_WORKSPACE_V1_CONTRACT.md"
APP = ROOT / "app.py"
PAYLOAD_CONTRACT = ROOT / "automation/CEW_F7_PATCH_PAYLOAD_CONTRACT_v1.json"
STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
ISSUES = ROOT / "data/canonical/N12_ISSUES_CURRENT_v1.json"
TERMINOLOGY = ROOT / "automation/CEW_TERMINOLOGY_LAYER_v1.json"
LIFECYCLE = ROOT / "automation/CEW_PROJECT_LIFECYCLE_MODEL_v1.json"


def fail(errors: list[str]) -> int:
    print("CEW_SOURCE_EVIDENCE_JOURNEY = FAIL")
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def main() -> int:
    errors: list[str] = []
    for path in [SOURCE_CONTRACT, EVIDENCE_CONTRACT, APP, PAYLOAD_CONTRACT, STATE, ISSUES, TERMINOLOGY, LIFECYCLE]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return fail(errors)

    maps = workspace.maps()
    sources = maps["sources"]
    tasks = maps["tasks"]
    bindings = maps["bindings"]
    regions = maps["regions"]
    pages = maps["pages"]
    transforms = maps["transforms"]
    derived = maps["derived"]

    if workspace.ARCHIVE_COMMIT != "78c20a52db4f391ce0d13b9705b9f04737e218c9":
        errors.append("immutable archive commit drift")

    for task_id in ["ERW-N12-001", "ERW-N12-002", "ERW-N12-003", "ERW-N12-004"]:
        task = tasks.get(task_id)
        binding = bindings.get(task_id)
        if not task or not binding:
            errors.append(f"{task_id}: task/viewer binding missing")
            continue
        if binding.get("binding_state") != "READY":
            errors.append(f"{task_id}: viewer binding is not READY")
        source = sources.get(task.get("source_id"))
        region = regions.get(binding.get("evidence_region_id"))
        page = pages.get(binding.get("page_id"))
        transform = transforms.get(binding.get("transform_id"))
        if not source or source.get("status") != "DOC_PRIMARY_IMMUTABLE":
            errors.append(f"{task_id}: immutable primary source missing")
            continue
        if not region or not page or not transform:
            errors.append(f"{task_id}: F2 provenance chain incomplete")
            continue
        if any(x.get("readiness_state") != "READY" for x in (region, page, transform)):
            errors.append(f"{task_id}: F2 provenance object not READY")
        if region.get("source_version_id") != binding.get("source_version_id") or page.get("source_version_id") != binding.get("source_version_id"):
            errors.append(f"{task_id}: SourceVersion chain mismatch")
        if region.get("page_id") != binding.get("page_id") or transform.get("page_id") != binding.get("page_id"):
            errors.append(f"{task_id}: Page chain mismatch")
        if region.get("transform_id") != binding.get("transform_id"):
            errors.append(f"{task_id}: transform chain mismatch")
        if region.get("coordinate_space") != "NORMALIZED_0_1" or region.get("geometry_type") != "BBOX":
            errors.append(f"{task_id}: canonical normalized BBOX required")
        aid = derived.get(region.get("derived_asset_id"))
        if not aid or aid.get("authority_state") != "DERIVED_REVIEW_AID_ONLY":
            errors.append(f"{task_id}: derived render authority boundary missing")
        version_prefix = binding.get("source_version_id", "").rsplit("-V", 1)[-1].lower()
        if not source.get("sha256", "").lower().startswith(version_prefix):
            errors.append(f"{task_id}: SourceVersion/hash identity mismatch")

    module_text = (ROOT / "scripts/cew_source_evidence_workspace.py").read_text(encoding="utf-8")
    if "CEW_ERW_SOURCE_ASSET_STATUS" in module_text:
        errors.append("stale pre-F2 asset status is being consumed by B1 runtime")
    for marker in ["ARCHIVE_COMMIT", "verify_source_bytes", "SOURCE_SHA256_MISMATCH", "render_verified_pdf", "NORMALIZED_0_1"]:
        if marker not in module_text:
            errors.append(f"runtime integrity marker missing: {marker}")

    payload = b"CEW-B1-INTEGRITY-FIXTURE"
    fake = {"sha256": hashlib.sha256(payload).hexdigest()}
    try:
        workspace.verify_source_bytes(fake, payload)
    except Exception as exc:
        errors.append(f"correct SHA rejected: {exc}")
    try:
        workspace.verify_source_bytes({"sha256": "0" * 64}, payload)
        errors.append("SHA mismatch was accepted")
    except ValueError as exc:
        if "SOURCE_SHA256_MISMATCH" not in str(exc):
            errors.append(f"wrong SHA failure reason: {exc}")

    try:
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text((70, 180), "2 F12 superiori + 2 F12 inferiori", fontsize=14)
        pdf = doc.tobytes()
        doc.close()
        region = {"coordinate_space": "NORMALIZED_0_1", "x": "0.05", "y": "0.15", "width": "0.90", "height": "0.18"}
        rendered = {scale: workspace.render_verified_pdf(pdf, region, 0, scale) for scale in ("MICRO", "MESO", "MACRO")}
        for scale, png in rendered.items():
            if not png.startswith(b"\x89PNG\r\n\x1a\n") or len(png) < 100:
                errors.append(f"{scale}: synthetic render is not valid PNG")
    except Exception as exc:
        errors.append(f"synthetic source rendering failed: {exc}")

    source_hub = workspace.build_source_hub()
    for marker in ["Fonti del progetto", "Fonte primaria immutabile", "Apri fonte", "Vedi evidenze", "TAV-05A", "TAV-06A"]:
        if marker not in source_hub:
            errors.append(f"Source Hub marker missing: {marker}")

    r08 = workspace.build_evidence_workspace("ERW-N12-001")
    for marker in ["MICRO", "MESO", "MACRO", "Già documentato", "Da verificare", "Contesto ingegneristico", "Registra la tua osservazione", "non è una scrittura canonica", "/api/f7/receipt"]:
        if marker not in r08:
            errors.append(f"R08 Evidence Workspace marker missing: {marker}")
    if "Scrivi in linguaggio tecnico naturale" not in r08:
        errors.append("natural engineering language instruction missing")
    if "2 Φ12 superiori + 2 Φ12 inferiori" in r08 or "SEMANTIC_DIRECTIONAL" in r08:
        errors.append("parser grammar leaked into user-facing Evidence Workspace")

    r11 = workspace.build_evidence_workspace("ERW-N12-004")
    if "UNBOUND" not in r11 or "non seleziona automaticamente il membro più vicino" not in r11:
        errors.append("R11 unbound honesty boundary missing")

    natural = "i filari lunghi 1040 son 2 f 12 superiori e 2 f 12 inferiori"
    semantic, reason = patch_builder.reinforcement_payload(natural)
    if reason or not semantic:
        errors.append(f"natural explicit directional observation rejected: {reason}")
    else:
        if semantic.get("upper") != {"count": 2, "diameter_mm": 12} or semantic.get("lower") != {"count": 2, "diameter_mm": 12}:
            errors.append("natural directional semantics parsed incorrectly")
        if semantic.get("raw_human_observation") != natural:
            errors.append("raw natural human observation was rewritten")
        if semantic.get("directional_separation_preserved") is not True:
            errors.append("upper/lower separation not preserved")

    exact, exact_reason = patch_builder.reinforcement_payload("2 Φ12 superiori + 2 Φ12 inferiori")
    if exact_reason or not exact:
        errors.append("previous exact directional form lost compatibility")
    for blocked in ["4 f 12", "2 f 12 superiori", "2 f 12 superiori e diametro 12 inferiori"]:
        semantic, _ = patch_builder.reinforcement_payload(blocked)
        if semantic is not None:
            errors.append(f"underspecified/aggregate observation was accepted: {blocked}")

    contract = json.loads(PAYLOAD_CONTRACT.read_text(encoding="utf-8"))
    invariants = contract.get("invariants", {})
    for key in [
        "generic_total_is_not_equivalent_to_directional_reinforcement",
        "upper_and_lower_must_remain_separate",
        "free_text_semantic_inference_forbidden",
        "natural_language_context_must_not_be_rewritten",
        "missing_direction_count_or_diameter_blocks_semantic_payload",
        "payload_candidate_never_authorizes_canonical_write",
    ]:
        if invariants.get(key) is not True:
            errors.append(f"semantic authority invariant missing: {key}")

    app_text = APP.read_text(encoding="utf-8")
    for route in ['@app.get("/sources"', '@app.get("/sources/{source_id}"', '@app.get("/evidence/review"', '@app.get("/api/source/pdf/{source_id}"', '@app.get("/api/source/render"']:
        if route not in app_text:
            errors.append(f"runtime route missing: {route}")
    if '"source_integrity_policy": "IMMUTABLE_COMMIT_PLUS_SHA256_FAIL_CLOSED"' not in app_text:
        errors.append("health source-integrity policy marker missing")

    state = json.loads(STATE.read_text(encoding="utf-8"))
    issues = json.loads(ISSUES.read_text(encoding="utf-8"))
    terminology = json.loads(TERMINOLOGY.read_text(encoding="utf-8"))
    lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    home_html = project_home.build_project_home(state, issues, list(tasks.values()), terminology, lifecycle)
    if "/sources" not in home_html:
        errors.append("Project Home -> Source Hub navigation missing")
    if "/evidence/review?task=" not in home_html:
        errors.append("Project Home -> Evidence Workspace action missing")

    if errors:
        return fail(errors)

    print("CEW_SOURCE_EVIDENCE_JOURNEY = PASS")
    print("DATA_GATE = PASS")
    print("ENGINEERING_GATE = PASS")
    print("HUMAN_GATE = PASS")
    print("HUMAN_FACTORS_GATE = PASS")
    print("SOURCE_CHAIN = IMMUTABLE_PDF -> SOURCEVERSION -> PAGE -> TRANSFORM -> EVIDENCEREGION")
    print("SOURCE_RENDER = MICRO/MESO/MACRO")
    print("SOURCE_SHA256 = FAIL_CLOSED")
    print("NATURAL_LANGUAGE = EXPLICIT_TOKENS_ONLY_RAW_PRESERVED")
    print("DIRECTIONAL_COLLAPSE = FORBIDDEN")
    print("CANONICAL_WRITE = FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
