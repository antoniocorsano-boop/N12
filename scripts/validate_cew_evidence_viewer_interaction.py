#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# Use a managed-runtime identity so this validator follows the same bootstrap
# path used by the Render HVA candidate. No network or canonical write occurs.
os.environ.setdefault("RENDER", "true")
os.environ.setdefault("RENDER_GIT_COMMIT", "0123456789abcdef0123456789abcdef01234567")
os.environ.setdefault("RENDER_EXTERNAL_URL", "https://cew-hva.example.invalid")

import app
import cew_source_evidence_workspace as source_workspace


def require(text: str, marker: str) -> None:
    if marker not in text:
        raise AssertionError(f"missing evidence viewer marker: {marker}")


def main() -> int:
    if not getattr(source_workspace.build_evidence_workspace, "_cew_evidence_interaction", False):
        raise AssertionError("interactive Evidence Workspace wrapper not installed in runtime")

    response = app.evidence_workspace("ERW-N12-001")
    if response.status_code != 200:
        raise AssertionError(f"Evidence Workspace route returned {response.status_code}")
    text = response.body.decode("utf-8")

    for marker in [
        'id="evidenceViewport"',
        'id="viewerState"',
        "＋ Ingrandisci",
        "− Riduci",
        "Adatta",
        "Reset vista",
        "↶ 90°",
        "↷ 90°",
        "addEventListener('wheel'",
        "addEventListener('pointerdown'",
        "addEventListener('pointermove'",
        "addEventListener('keydown'",
        "evidencePointers.size===2",
        "touch-action:none",
        "evidencePanEver?'usato':'non usato'",
        "Zoom ${Math.round(evidenceZoom*100)}%",
        "rotateEvidence",
        "fitEvidenceView",
        "resetEvidenceView",
        "PDF verificato è la fonte primaria",
    ]:
        require(text, marker)

    # Scale switching must remain available and must not be conflated with zoom.
    for marker in [
        "MICRO · dettaglio",
        "MESO · contesto vicino",
        "MACRO · tavola",
        "function scale(s)",
        "sourceImage.src='/api/source/render?task='",
    ]:
        require(text, marker)

    # Human interaction remains a viewer-only operation.
    require(text, "La revisione non è una scrittura canonica")

    print("CEW_EVIDENCE_VIEWER_INTERACTION = PASS")
    print("ZOOM = AVAILABLE")
    print("PAN_POINTER = AVAILABLE")
    print("PINCH_TOUCH = AVAILABLE")
    print("WHEEL_TRACKPAD = AVAILABLE")
    print("KEYBOARD = AVAILABLE")
    print("FIT_RESET_ROTATION = AVAILABLE")
    print("SOURCE_SCALE_MICRO_MESO_MACRO = PRESERVED")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
