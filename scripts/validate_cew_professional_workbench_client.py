#!/usr/bin/env python3
from __future__ import annotations

import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "scripts/cew_professional_workbench_client.py"
API = ROOT / "scripts/cew_professional_workbench_api.py"
HOME = ROOT / "scripts/cew_project_home.py"
CORE = ROOT / "scripts/cew_professional_workbench_core.py"
CONTRACT = ROOT / "docs/DESIGN/CEW_PROFESSIONAL_WORKBENCH_PRODUCT_CONTRACT_v1.md"
WIREFRAMES = ROOT / "docs/DESIGN/CEW_PROFESSIONAL_WORKBENCH_UX_WIREFRAMES_STATE_MAPS_v1.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def text(path: Path) -> str:
    require(path.is_file(), f"missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    for path in (CLIENT, API, HOME):
        py_compile.compile(str(path), doraise=True)

    client = text(CLIENT)
    api = text(API)
    home = text(HOME)
    core = text(CORE)
    contract = text(CONTRACT)
    wireframes = text(WIREFRAMES)
    client_lower = client.lower()

    for marker in (
        "F3_DZI_OPENSEADRAGON_REUSED",
        "WORKBENCH_SCENE_OBJECTS_RENDERED_AS_SVG",
        "EXPLICIT_EVIDENCE_LINK_ONLY",
        "OVERLAY_DISABLED_WITHOUT_VERIFIED_REGISTRATION",
        "OBJECT_ANCHORED_NON_CANONICAL_WORKING_EDIT",
        "GRAPHICALLY_ANCHORED_NON_CANONICAL_READING_ISSUE",
        "WORK_EVIDENCE_PROVENANCE",
        'data-canonical-write-authorized="false"',
        "/workbench/assets/source-viewer/vendor/openseadragon/openseadragon.min.js",
        "/api/workbench/scene?task=",
        "/api/workbench/view/resolve",
        "/api/workbench/working-edit/preview",
        "/api/workbench/reading-issue/preview",
        "Evidenza",
        "Provenienza",
    ):
        require(marker in client, f"client marker missing: {marker}")
    require("rappresentazione tecnica derivata" in client_lower, "technical representation label missing")
    require("keydown" in client and "ArrowLeft" in client and "ArrowRight" in client, "keyboard viewport alternatives missing")

    require("canonical_write_authorized=true" not in client_lower, "client must never authorize canonical write")
    require("VISUAL_PROXIMITY" not in client, "client must not create proximity bindings")

    for marker in (
        '@router.get("/workbench", response_class=HTMLResponse)',
        'X-CEW-Canonical-Write": "false"',
        'X-CEW-Engineering-Authority-Effect": "NONE"',
        "client.build_client(task.strip())",
    ):
        require(marker in api, f"workbench route marker missing: {marker}")

    require('/workbench?task={quote(task.get(\'task_id\',\'\'))}' in home, "Project Home must route review actions to Workbench")
    require('/evidence/review?task={quote(task.get(\'task_id\',\'\'))}' not in home, "Project Home must not bypass the Workbench for primary review action")

    for marker in (
        "OVERLAY_REQUIRES_VERIFIED_REVISION_MATCHED_REGISTRATION",
        "SPATIAL_LOCK_REQUIRES_VERIFIED_REVISION_MATCHED_REGISTRATION",
        "WORKING_EDIT_CANONICAL_WRITE_FORBIDDEN",
        "READING_ISSUE_CANONICAL_WRITE_FORBIDDEN",
    ):
        require(marker in core, f"kernel fail-closed marker missing: {marker}")

    for marker in (
        "Drawing first",
        "Direct manipulation",
        "Progressive disclosure",
        "F3 OpenSeadragon/DZI source viewer",
        "selectable technical objects",
    ):
        require(marker in contract, f"product contract marker missing: {marker}")
    for marker in ("Desktop default — SPLIT", "Internal SourceVersion/EvidenceRegion ids are hidden", "OVERLAY is disabled"):
        require(marker in wireframes, f"wireframe marker missing: {marker}")

    # The integration is intentionally a candidate. These client checks do not
    # satisfy PWB-005 document geometry, verified registration, HVA or B1 promotion.
    print("CEW_PROFESSIONAL_WORKBENCH_CLIENT_INTEGRATION = PASS")
    print("PROJECT_HOME_TO_WORKBENCH = PASS")
    print("F3_DZI_CLIENT_CONSUMPTION = PASS")
    print("TECHNICAL_SVG_SELECTION_CLIENT = PASS")
    print("SEMANTIC_SYNC_EXPLICIT_LINK_ONLY = PASS")
    print("OVERLAY_FAIL_CLOSED_WITHOUT_VERIFIED_REGISTRATION = PASS")
    print("WORKING_EDIT_NON_CANONICAL = PASS")
    print("READING_ISSUE_NON_CANONICAL = PASS")
    print("PROGRESSIVE_DISCLOSURE = PASS")
    print("HVA_EXECUTION_AUTHORIZED = false")
    print("B1_PROMOTION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
