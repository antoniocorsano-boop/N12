#!/usr/bin/env python3
"""Compatibility route headers for region-guided Document Discovery."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_region_guidance as region_guidance


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def region_guided_compat_page():
        return HTMLResponse(
            region_guidance._patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Architecture": "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS",
                "X-CEW-Panel-Quality": "MATURE_V1",
                "X-CEW-Panel-Content": "HVA_REFINED_V1",
                "X-CEW-Governed-Analysis": "ASYNC_BOUNDED_RECONSTRUCT_V1",
                "X-CEW-Preview-Runtime-Recovery": "BROWSER_RECONSTRUCT_V1",
                "X-CEW-Region-Guidance": "AUTO_LAYOUT_PLUS_HUMAN_ROI_V1",
                "X-CEW-Region-Semantic-Authority": "NONE",
            },
        )

    return router
