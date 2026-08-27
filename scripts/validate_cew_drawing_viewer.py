#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_drawing_viewer as viewer
import cew_source_evidence_workspace as source_workspace

APP = ROOT / "app.py"
TASK = ROOT / "automation/outbox/CEW_B12_DRAWING_VIEWER_TASK_v1.json"


def fail(errors: list[str]) -> int:
    print("CEW_DRAWING_VIEWER = FAIL")
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def synthetic_pdf(width: float, height: float) -> bytes:
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.insert_text((20, 30), "CEW B1.2 synthetic drawing render gate")
    payload = doc.tobytes()
    doc.close()
    return payload


def main() -> int:
    errors: list[str] = []
    if not APP.exists() or not TASK.exists():
        return fail(["missing app.py or B1.2 task contract"])

    ctx = viewer.drawing_context("TAV-05A")
    if not ctx.get("viewer_ready"):
        errors.append("TAV-05A viewer must be READY from governed Page registry")
    page = ctx.get("page") or {}
    if page.get("readiness_state") != "READY":
        errors.append("TAV-05A Page readiness drift")
    if len(ctx.get("regions", [])) != 3:
        errors.append(f"TAV-05A expected 3 READY EvidenceRegions, got {len(ctx.get('regions', []))}")
    for region in ctx.get("regions", []):
        if region.get("coordinate_space") != "NORMALIZED_0_1":
            errors.append(f"{region.get('evidence_region_id')}: overlay coordinate space drift")
        for key in ["x", "y", "width", "height"]:
            value = float(region[key])
            if value < 0 or value > 1:
                errors.append(f"{region.get('evidence_region_id')}: {key} outside normalized bounds")

    html = viewer.build_viewer("TAV-05A")
    required_controls = [
        "Adatta pagina",
        "Adatta larghezza",
        "＋ Zoom",
        "− Zoom",
        "↶ 90°",
        "↷ 90°",
        "Reset orientamento",
        "Evidenze",
        "PDF verificato",
        "sola visualizzazione",
        "READING_AID_ONLY" if False else "ausilio di lettura",
    ]
    for marker in required_controls:
        if marker.lower() not in html.lower():
            errors.append(f"viewer missing control/authority marker: {marker}")
    for region in ctx.get("regions", []):
        if f"data-region='{region['evidence_region_id']}'" not in html:
            errors.append(f"viewer missing overlay for {region['evidence_region_id']}")
    for marker in ["rotate(90)", "rotate(180)", "rotate(270)", "pointermove", "wheel", "fitWidth", "toggleOverlays"]:
        if marker not in html:
            errors.append(f"viewer interaction implementation missing: {marker}")

    m = source_workspace.maps()
    source_with_no_page = next(
        (sid for sid in m["sources"] if not any(p.get("logical_source_code") == sid for p in m["pages"].values())),
        None,
    )
    if not source_with_no_page:
        errors.append("test fixture requires at least one source without governed Page")
    else:
        fallback = viewer.build_viewer(source_with_no_page)
        if "Viewer non ancora governato" not in fallback:
            errors.append("source without READY Page must fail closed in viewer")
        if "PDF originale verificato" not in fallback:
            errors.append("source without READY Page must preserve verified PDF fallback")

    original_fetch = source_workspace.fetch_verified_source
    try:
        width = float(page["source_width"])
        height = float(page["source_height"])
        source = ctx["source"]
        good_pdf = synthetic_pdf(width, height)
        source_workspace.fetch_verified_source = lambda source_id: (good_pdf, source)
        png, render_ctx = viewer.render_full_page("TAV-05A", 54)
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("governed drawing render did not return PNG")
        if render_ctx.get("derived_authority") != "READING_AID_ONLY":
            errors.append("drawing render authority drift")
        if render_ctx.get("canonical_write_authorized") is not False:
            errors.append("drawing render must never authorize canonical write")

        bad_pdf = synthetic_pdf(width + 10.0, height)
        source_workspace.fetch_verified_source = lambda source_id: (bad_pdf, source)
        try:
            viewer.render_full_page("TAV-05A", 54)
            errors.append("page dimension mismatch was not rejected")
        except ValueError as exc:
            if str(exc) != "PAGE_DIMENSION_MISMATCH":
                errors.append(f"unexpected dimension mismatch reason: {exc}")

        try:
            viewer.render_full_page("TAV-05A", 55)
            errors.append("unsupported drawing DPI was not rejected")
        except ValueError as exc:
            if str(exc) != "UNSUPPORTED_DRAWING_DPI":
                errors.append(f"unexpected unsupported DPI reason: {exc}")
    finally:
        source_workspace.fetch_verified_source = original_fetch

    app_text = APP.read_text(encoding="utf-8")
    for marker in [
        "import cew_drawing_viewer as drawing_viewer",
        '@app.get("/api/drawing/render/{source_id}")',
        '"drawing_viewer": "B12_PREP_AVAILABLE_NOT_PROMOTED"',
        '"X-CEW-Derived-Authority": "READING_AID_ONLY"',
        '"X-CEW-Canonical-Write": "false"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime viewer integration missing: {marker}")

    task_text = TASK.read_text(encoding="utf-8")
    if '"state": "PREP_IN_PROGRESS_BLOCKED_PROMOTION"' not in task_text:
        errors.append("B1.2 preparation state drift")
    if '"promotion_authorized": false' not in task_text:
        errors.append("B1.2 promotion must remain blocked")

    if errors:
        return fail(errors)

    print("CEW_DRAWING_VIEWER = PASS")
    print("TAV05A_PAGE = READY")
    print("TAV05A_OVERLAYS = 3")
    print("ROTATION = VIEWER_STATE_ONLY")
    print("PAN_ZOOM = CLIENT_VIEW_STATE_ONLY")
    print("DERIVED_AUTHORITY = READING_AID_ONLY")
    print("DIMENSION_MISMATCH = FAIL_CLOSED")
    print("B12_PROMOTION_AUTHORIZED = false")
    print("UX_DOC_02 = HVA_REQUIRED")
    print("UX_DOC_03 = HVA_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
