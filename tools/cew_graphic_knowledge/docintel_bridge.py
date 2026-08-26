from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tools.cew_graphic_knowledge import fabric as gkf


def import_project_labels(docintel_db: Path, fabric_db: Path, project_id: str) -> dict[str, Any]:
    """Import reviewed project labels into the system Graphic Knowledge Fabric.

    Semantic training evidence is copied with stable GCFP/source lineage and its graphic
    feature signature. Source files and canonical engineering values are never copied.
    """
    if not project_id.strip():
        raise ValueError("project_id is required")
    source = sqlite3.connect(docintel_db)
    source.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "graphic_training_examples" not in tables:
            raise RuntimeError("docintel database has no graphic_training_examples table")
        columns = {r[1] for r in source.execute("PRAGMA table_info(graphic_training_examples)")}
        if "feature_signature" not in columns:
            raise RuntimeError("project graphic labels have no feature_signature; migrate project database first")
        rows = source.execute(
            """SELECT candidate_fingerprint,source_sha256,meaning,verdict,context_json,
                      feature_signature,reviewer,created_at
               FROM graphic_training_examples
               ORDER BY created_at,id"""
        ).fetchall()
    finally:
        source.close()

    imported = 0
    for row in rows:
        if not row["candidate_fingerprint"] or not row["source_sha256"]:
            raise RuntimeError("project label lacks stable GCFP/source SHA lineage")
        gkf.add_example(
            fabric_db,
            project_id=project_id,
            source_sha256=row["source_sha256"],
            candidate_fingerprint=row["candidate_fingerprint"],
            meaning=row["meaning"],
            verdict=row["verdict"],
            context=json.loads(row["context_json"] or "{}"),
            feature=row["feature_signature"],
            reviewer=row["reviewer"],
            reviewed_at=row["created_at"],
        )
        imported += 1
    return {
        "status": "PASS",
        "project_id": project_id,
        "labels_seen": len(rows),
        "labels_imported_or_updated": imported,
        "source_files_copied": 0,
        "feature_signatures_transferred": len(rows),
        "canonical_promotion": "DISABLED",
    }


def resolve_for_project(
    fabric_db: Path,
    project_id: str,
    context: dict[str, Any],
    candidate_feature: str | dict[str, Any] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Return pattern+context transferable candidates; project human review remains authoritative."""
    result = gkf.resolve(
        fabric_db,
        project_id=project_id,
        context=context,
        candidate_feature=candidate_feature,
        limit=limit,
    )
    result["project_specialization_required"] = True
    result["shared_knowledge_mutation"] = "NONE"
    return result
