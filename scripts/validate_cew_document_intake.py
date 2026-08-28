#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_document_intake as intake

MODEL = ROOT / "automation/CEW_DOCUMENT_INTAKE_MODEL_v1.json"
CONTRACT = ROOT / "docs/PRODUCT/CEW_DOCUMENT_INTAKE_VERSIONING_V1_CONTRACT.md"
APP = ROOT / "app.py"

TAV05_SHA = "17dec414f0f0505e2cd2acb519029afba7672df1793a580badb8b59b6214f325"
NEW_SHA = "a" * 64


def fail(errors: list[str]) -> int:
    print("CEW_DOCUMENT_INTAKE = FAIL")
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def main() -> int:
    errors: list[str] = []
    for path in [MODEL, CONTRACT, APP]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return fail(errors)

    model = json.loads(MODEL.read_text(encoding="utf-8"))
    if model.get("duplicate_policy", {}).get("filename_only_binding") != "FORBIDDEN":
        errors.append("filename-only binding must remain forbidden")
    storage = model.get("storage_policy", {})
    if storage.get("production_adapter_state") != "NOT_CONFIGURED_IN_B14_PREPARATION":
        errors.append("B1.4 must not claim Production byte storage configured")
    if storage.get("metadata_only_analysis_uploads_bytes") is not False:
        errors.append("metadata-only analysis must not upload bytes")
    promotion = model.get("promotion_policy", {})
    for key in ["sourceversion_overwrite", "metadata_analysis_is_canonical_write", "stored_private_is_canonical_write", "sourceversion_proposal_is_canonical_write"]:
        if promotion.get(key) is not False:
            errors.append(f"unsafe promotion policy: {key}")

    exact = intake.analyze_metadata({
        "filename": "qualunque-nome.pdf",
        "size_bytes": 1186994,
        "mime_type": "application/pdf",
        "sha256": TAV05_SHA,
        "selected_source_id": "",
    })
    if exact.get("state") != "EXACT_DUPLICATE" or exact.get("matching_source_id") != "TAV-05A":
        errors.append(f"exact SHA must resolve TAV-05A duplicate, got {exact}")
    if exact.get("bytes_uploaded") is not False or exact.get("canonical_write_authorized") is not False:
        errors.append("exact duplicate analysis must remain metadata-only/noncanonical")

    version = intake.analyze_metadata({
        "filename": "nuova-versione.pdf",
        "size_bytes": 1200000,
        "mime_type": "application/pdf",
        "sha256": NEW_SHA,
        "selected_source_id": "TAV-05A",
    })
    if version.get("state") != "NEW_VERSION_CANDIDATE" or version.get("selected_source_id") != "TAV-05A":
        errors.append(f"explicit source + new hash must become version candidate, got {version}")
    if version.get("next_action") != "HUMAN_CONFIRM_VERSION_RELATION_AND_CLASSIFICATION":
        errors.append("new version candidate must require human confirmation/classification")

    unknown = intake.analyze_metadata({
        "filename": "documento-nuovo.pdf",
        "size_bytes": 900000,
        "mime_type": "application/pdf",
        "sha256": "b" * 64,
        "selected_source_id": "",
    })
    if unknown.get("state") != "SOURCE_DECISION_REQUIRED":
        errors.append(f"new unmatched file must require source decision, got {unknown}")
    if unknown.get("filename_hint_is_binding") is not False:
        errors.append("filename hint may never be a binding")

    filename_only = intake.analyze_metadata({
        "filename": "tavola 5-3.pdf",
        "size_bytes": 1186995,
        "mime_type": "application/pdf",
        "sha256": "c" * 64,
        "selected_source_id": "",
    })
    if filename_only.get("state") != "SOURCE_DECISION_REQUIRED":
        errors.append("same filename with different hash must not auto-bind")
    if "TAV-05A" not in filename_only.get("filename_similarity_hints", []):
        errors.append("same filename may be exposed only as non-binding hint")
    if filename_only.get("filename_hint_is_binding") is not False:
        errors.append("filename similarity must remain non-binding")

    try:
        intake.analyze_metadata({"filename":"x.pdf","size_bytes":1,"mime_type":"application/pdf","sha256":"bad","selected_source_id":""})
    except ValueError as exc:
        if str(exc) != "INVALID_SHA256":
            errors.append(f"invalid SHA wrong reason: {exc}")
    else:
        errors.append("invalid SHA must fail closed")

    html = intake.build_intake_page().lower()
    for token in ["calcolo sha-256 locale", "nessun byte inviato", "non viene caricato", "storage", "non ancora autorizzato"]:
        if token not in html:
            errors.append(f"intake UI missing privacy/status marker: {token}")
    if "crypto.subtle.digest('sha-256'" not in html:
        errors.append("browser Web Crypto SHA-256 implementation missing")
    if "type=\"file\"" not in html and "type='file'" not in html:
        errors.append("intake file selector missing")

    app_text = APP.read_text(encoding="utf-8")
    for marker in [
        "import cew_document_intake as document_intake",
        '@app.get("/documents/intake"',
        '@app.post("/api/intake/analyze"',
        '"document_intake": "B14_METADATA_ONLY_PREP_AVAILABLE_NOT_PROMOTED"',
        '"document_byte_storage": "NOT_CONFIGURED"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime integration missing: {marker}")

    contract = CONTRACT.read_text(encoding="utf-8").lower()
    for token in ["never overwrite", "private", "exact sha-256", "filename similarity alone", "metadata-only"]:
        if token not in contract:
            errors.append(f"contract missing boundary: {token}")

    if errors:
        return fail(errors)

    print("CEW_DOCUMENT_INTAKE = PASS")
    print("EXACT_DUPLICATE_TAV05A = PASS")
    print("NEW_VERSION_CANDIDATE_REQUIRES_HUMAN = PASS")
    print("NEW_SOURCE_RELATION_AUTO_BIND = false")
    print("FILENAME_ONLY_BINDING = false")
    print("METADATA_ONLY_BYTES_UPLOADED = false")
    print("DOCUMENT_BYTE_STORAGE = NOT_CONFIGURED")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
