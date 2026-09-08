#!/usr/bin/env python3
"""Compatibility route headers for layout-guided Document Discovery."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_local_focus as local_focus


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def region_guided_compat_page():
        return HTMLResponse(
            local_focus._patched_page(),
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
                "X-CEW-Layout-Phase-Gate": "LAYOUT_CONFIRM_BEFORE_SEMANTICS_V3",
                "X-CEW-Layout-Unit-Selection": "PHASE_GATE_POINTER_V2",
                "X-CEW-Local-Unit-Analysis": "BROWSER_GRAPHIC_FRAGMENTS_V1",
                "X-CEW-Local-Primitive-Visibility": "DIAGNOSTIC_OPT_IN_V1",
                "X-CEW-Operator-View": "CLEAN_LOCAL_REVIEW_V1",
                "X-CEW-Visual-Reference-Search": "REFERENCE_FIRST_REVIEW_V1",
                "X-CEW-Visual-Reference-Capture": "TOOLBAR_YIELD_V1",
                "X-CEW-Local-Unit-Focus": "READING_UNIT_WORKING_VIEW_V1",
                "X-CEW-Local-Focus-Navigation": "COLUMN_WIDTH_FIT_VERTICAL_SCROLL_V1",
                "X-CEW-Visual-Result-Navigation": "RESULT_FOCUS_REVIEW_V1",
                "X-CEW-Visual-Similarity": "DETERMINISTIC_LAYOUT_AWARE_V1",
                "X-CEW-Visual-Search-Result-Action": "REVIEW_ONLY_V1",
                "X-CEW-Visual-Search-Semantic-Authority": "NONE",
                "X-CEW-Semantic-Gate": "LOCAL_BACKEND_CANDIDATE_REQUIRED_V1",
            },
        )

    return router
