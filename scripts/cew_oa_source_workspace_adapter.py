#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import cew_source_evidence_workspace as base

ROOT = Path(__file__).resolve().parents[1]
OA_TASKS = ROOT / "data/canonical/CEW_OA_TASK_REGISTRY_v1.csv"
OA_BINDINGS = ROOT / "data/canonical/CEW_OA_SOURCE_VIEWER_BINDINGS_v1.csv"


class OAExtendedSourceWorkspace:
    """Read-only adapter exposing OA tasks to Workbench consumers only.

    The base ERW registries remain unchanged. This adapter unions dedicated OA task
    and viewer-binding registries for Workbench/provenance reads; all source access,
    immutable verification and rendering behavior is delegated to the base source
    workspace. It grants no canonical-write or promotion authority.
    """

    def __getattr__(self, name):
        return getattr(base, name)

    def maps(self) -> dict:
        result = deepcopy(base.maps())
        oa_tasks = base.rows(OA_TASKS)
        oa_bindings = base.rows(OA_BINDINGS)
        for row in oa_tasks:
            task_id = row["task_id"].strip()
            if task_id in result["tasks"]:
                raise ValueError(f"OA_TASK_ID_COLLIDES_WITH_ERW:{task_id}")
            result["tasks"][task_id] = row
        for row in oa_bindings:
            task_id = row["task_id"].strip()
            if task_id in result["bindings"]:
                raise ValueError(f"OA_BINDING_ID_COLLIDES_WITH_ERW:{task_id}")
            result["bindings"][task_id] = row
        return result

    def task_context(self, task_id: str) -> dict:
        m = self.maps()
        task = m["tasks"].get(task_id)
        binding = m["bindings"].get(task_id)
        if not task or not binding:
            raise KeyError("TASK_BINDING_NOT_FOUND")
        region = m["regions"].get(binding["evidence_region_id"])
        page = m["pages"].get(binding["page_id"])
        transform = m["transforms"].get(binding["transform_id"])
        if not region or not page or not transform:
            raise KeyError("F2_PROVENANCE_CHAIN_INCOMPLETE")
        if any(x.get("readiness_state") != "READY" for x in (region, page, transform)):
            raise ValueError("F2_PROVENANCE_NOT_READY")
        source = m["sources"].get(task["source_id"])
        if not source:
            raise KeyError("PRIMARY_SOURCE_NOT_REGISTERED")
        derived = m["derived"].get(region.get("derived_asset_id", ""))
        return {
            "task": task,
            "binding": binding,
            "region": region,
            "page": page,
            "transform": transform,
            "source": source,
            "derived": derived,
        }

    def render_task_source(self, task_id: str, scale: str):
        ctx = self.task_context(task_id)
        payload, source = base.fetch_verified_source(ctx["task"]["source_id"])
        png = base.render_verified_pdf(payload, ctx["region"], int(ctx["page"]["page_index"]), scale)
        return png, {**ctx, "verified_sha256": source["sha256"], "scale": scale.upper()}


workspace = OAExtendedSourceWorkspace()
