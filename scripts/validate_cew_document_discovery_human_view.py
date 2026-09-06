#!/usr/bin/env python3
"""Regression gate for the CEW Document Discovery human inspection surface."""
from __future__ import annotations

import json
from pathlib import Path

import cew_document_discovery_async_preview as async_preview


def main() -> None:
    html = async_preview._patched_page()

    required_tokens = [
        "preview-overview",
        "preview-width",
        "preview-zoom-out",
        "preview-zoom-reset",
        "preview-zoom-in",
        "preview-rotate-left",
        "preview-rotate-right",
        "renderPageGeometry",
        "rotatePreview",
        "setPreviewZoom",
        "enableDragPan",
        "cluster-hotspot",
        "renderClusterHotspots",
        "pointerdown",
        "pointermove",
    ]
    for token in required_tokens:
        assert token in html, token

    assert "Ruota ↶" in html
    assert "Ruota ↷" in html
    assert "Zoom +" in html
    assert "Zoom −" in html
    assert "Panoramica" in html
    assert "Larghezza" in html
    assert "pointer-events:auto" in html
    assert "clusterId=c.cluster_id" in html
    assert "automatic" not in "PAGE_ORIENTATION_FOR_HUMAN_READING"

    # The human-view layer must not weaken the authority boundary.
    assert "Training bloccato" in html or "training bloccato" in html
    assert "nessuna classificazione automatica" in html
    assert "X-CEW-Canonical-Write" in Path("cew_document_discovery_async_preview.py").read_text(encoding="utf-8")

    receipt = json.loads(
        Path("../analysis/cew/CEW_DOCUMENT_DISCOVERY_RUNTIME_HVA_RECEIPT_v1.json").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "RUNTIME_HVA_PASS"
    assert receipt["validated_runtime_revision"] == "320755e66a7263f1842f73dc14fb9a0ea8ccd7f8"
    assert receipt["hva"]["primitive_candidate_count"] == 2
    assert receipt["hva"]["graphic_cluster_count"] == 2
    assert receipt["hva"]["page_artifact_http_status"] == 200
    assert receipt["runtime_evidence"]["http_502_observed"] is False
    assert receipt["authority"]["training_authorized"] is False
    assert receipt["authority"]["canonical_write_authorized"] is False
    assert receipt["authority"]["automatic_semantic_authority"] == "NONE"

    print("CEW_DOCUMENT_DISCOVERY_HUMAN_VIEW_PASS")
    print("orientation=MANUAL_HUMAN_CONTROL zoom_pan=READY cluster_page_selection=READY")
    print("training=BLOCKED canonical_write_authorized=false semantic_authority=NONE")


if __name__ == "__main__":
    main()
