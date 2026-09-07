#!/usr/bin/env python3
"""Compatibility route headers for layout-guided Document Discovery."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_layout_learning as layout_learning


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def region_guided_compat_page():
        return HTMLResponse(
            layout_learning._patched_page(),
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
                "X-CEW-Region-Guidance": "LAYOUT_PRIMITIVES_V1",
                "X-CEW-Region-Semantic-Authority": "NONE",
                "X-CEW-Layout-Learning": "HYPOTHESIS_PLUS_TEACH_ONE_RELATION_V1",
                "X-CEW-Layout-Semantic-Authority": "NONE",
                "X-CEW-Layout-Prototype-Persistence": "LOCAL_NON_CANONICAL_V1",
            },
        )

    return router
