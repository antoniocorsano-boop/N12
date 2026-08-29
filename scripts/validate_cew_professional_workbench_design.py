#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs" / "DESIGN"
FILES = {
    "product": DESIGN / "CEW_PROFESSIONAL_WORKBENCH_PRODUCT_CONTRACT_v1.md",
    "interaction": DESIGN / "CEW_PROFESSIONAL_WORKBENCH_INTERACTION_ARCHITECTURE_v1.md",
    "projection": DESIGN / "CEW_PROFESSIONAL_WORKBENCH_TECHNICAL_PROJECTION_MODEL_v1.md",
    "rendering": DESIGN / "CEW_PROFESSIONAL_WORKBENCH_RENDERING_ARCHITECTURE_v1.md",
    "ux": DESIGN / "CEW_PROFESSIONAL_WORKBENCH_UX_WIREFRAMES_STATE_MAPS_v1.md",
    "hva": DESIGN / "CEW_PROFESSIONAL_WORKBENCH_HVA_PROTOCOL_v1.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(name: str) -> str:
    path = FILES[name]
    require(path.exists(), f"missing design deliverable: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    docs = {name: read(name) for name in FILES}
    all_text = "\n".join(docs.values())

    # Cross-package authority boundaries.
    require(all("Canonical write" in text or "canonical write" in text.lower() for text in docs.values()), "canonical-write boundary missing from design package")
    require("HVA_EXECUTION_AUTHORIZED = false" in docs["product"], "product contract must keep HVA closed")
    require("HVA_EXECUTION_AUTHORIZED = false" in docs["hva"], "HVA protocol must keep execution closed")
    require("document geometry != technical candidate != structural identity" in docs["projection"], "three-layer geometry/identity invariant missing")

    # Reuse obligations.
    for marker in ("F3", "OpenSeadragon", "DZI"):
        require(marker in docs["rendering"], f"source-viewer reuse marker missing: {marker}")
    require("Dual Vector Agreement" in docs["projection"], "dual-vector reuse missing from projection model")
    require("F6" in docs["projection"], "F6 structural-scene reuse missing from projection model")
    require("Reuse" in docs["product"] or "reuse" in docs["product"].lower(), "reuse-first product boundary missing")

    # Professional interaction model.
    for mode in ("SOURCE", "TECHNICAL", "SPLIT", "OVERLAY"):
        require(mode in docs["product"] and mode in docs["ux"], f"display mode missing across product/UX contracts: {mode}")
    require("SEMANTIC" in docs["interaction"] and "SPATIAL_LOCKED" in docs["interaction"], "semantic/spatial synchronization separation missing")
    require("VERIFIED" in docs["interaction"] and "Overlay" in docs["interaction"], "overlay registration guard missing")

    # Technical scene and object-anchored editing/issues.
    for marker in (
        "DocumentGraphicPrimitive",
        "RecognizedText",
        "TechnicalObjectCandidate",
        "EvidenceLink",
        "WorkingEdit",
        "ReadingIssue",
        "RegistrationTransform",
    ):
        require(marker in docs["projection"], f"technical projection object missing: {marker}")
    require("select object → Edit" in docs["interaction"], "object-anchored edit interaction missing")
    require("graphical marker" in docs["interaction"], "graphically anchored ReadingIssue interaction missing")

    # Coordinate and registration safety.
    require("SOURCE_PAGE_PT" in docs["projection"] and "TECHNICAL_2D" in docs["projection"], "coordinate-space model missing")
    require("UNAVAILABLE" in docs["projection"] and "VERIFIED" in docs["projection"] and "STALE" in docs["projection"], "registration state model missing")
    require("overlay is unavailable" in docs["rendering"].lower(), "rendering must fail closed when registration is not verified")

    # Progressive disclosure / drawing-first UX.
    require("Drawing first" in docs["product"], "drawing-first product principle missing")
    require("Provenance" in docs["ux"] and "Inspector" in docs["ux"], "progressive disclosure UX missing")
    require("No forced side-by-side miniature drawings" in docs["ux"], "narrow-layout professional boundary missing")

    # HVA must be engineering-task based and separate from accessibility/promotion.
    for marker in ("find → orient → compare", "Critical blocker", "accessibility", "same-revision"):
        require(marker.lower() in docs["hva"].lower(), f"professional HVA marker missing: {marker}")
    require("Current B1.8 candidate does not satisfy this entry gate" in docs["hva"], "current candidate must remain excluded from HVA")

    # The design package does not claim implementation readiness.
    require("REWORK_REQUIRED" in all_text, "design package must preserve current REWORK_REQUIRED state")

    print("CEW_PROFESSIONAL_WORKBENCH_DESIGN_PACKAGE = PASS")
    print("DELIVERABLES = 6/6")
    print("REUSE_FIRST = PASS")
    print("REGISTRATION_FAIL_CLOSED = PASS")
    print("OBJECT_ANCHORED_EDITING_MODEL = PASS")
    print("READING_ISSUE_MODEL = PASS")
    print("PROFESSIONAL_HVA_PROTOCOL = VERSIONED_NOT_EXECUTED")
    print("PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED")
    print("HVA_EXECUTION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")


if __name__ == "__main__":
    main()
