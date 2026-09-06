#!/usr/bin/env python3
"""Deterministic gate for offline verified external-reference review assets."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

import cew_external_graphic_reference_acquisition as acquisition_tools
import cew_external_graphic_reference_review_asset_hardening as asset_hardening
import cew_external_graphic_reference_review_hardening as race_hardening
import cew_external_graphic_reference_review_workbench as review
import cew_runtime_audit_store as audit_store


def main() -> None:
    race_hardening.install(review)
    asset_hardening.install(review)

    def _network_forbidden(*_args, **_kwargs):
        raise AssertionError("runtime external fetch must not be called")

    old_fetch = acquisition_tools._fetch_exact_bytes
    old_store = review.REVIEW_STORE
    old_backend = audit_store.backend_status
    acquisition_tools._fetch_exact_bytes = _network_forbidden
    try:
        manifest, rows = asset_hardening._manifest(review)
        assert manifest["asset_count"] == 5
        assert manifest["runtime_external_fetch_required"] is False
        assert manifest["authority"]["reading_aid_only"] is True
        assert manifest["authority"]["project_semantic_authority"] == "NONE"

        _acquisition, queue = review._governed()
        queued = review._queue_index(queue)
        assert set(rows) == set(queued)
        hashes = set()
        for item_id in sorted(queued):
            image = review.render_review_page(item_id)
            assert image.startswith(b"\xff\xd8")
            digest = hashlib.sha256(image).hexdigest()
            assert digest == rows[item_id]["image_sha256"]
            assert len(image) == rows[item_id]["image_byte_count"]
            hashes.add(digest)
        assert len(hashes) == 5

        with tempfile.TemporaryDirectory(prefix="cew-reference-review-assets-") as tmp:
            review.REVIEW_STORE = Path(tmp)
            audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
            app = FastAPI()
            app.include_router(review.build_router())
            client = TestClient(app)
            status = client.get("/api/workbench/reference-review/status")
            assert status.status_code == 200
            for item_id in sorted(queued):
                response = client.get(f"/api/workbench/reference-review/page/{item_id}.jpg")
                assert response.status_code == 200, response.text
                assert response.headers["content-type"].startswith("image/jpeg")
                assert response.headers["x-cew-reference-only"] == "true"
                assert response.content.startswith(b"\xff\xd8")
                assert hashlib.sha256(response.content).hexdigest() == rows[item_id]["image_sha256"]
    finally:
        acquisition_tools._fetch_exact_bytes = old_fetch
        review.REVIEW_STORE = old_store
        audit_store.backend_status = old_backend

    print("CEW_EXTERNAL_REFERENCE_REVIEW_OFFLINE_ASSET_PASS")
    print("review_items=5 runtime_external_fetch=false source_document_remains_authority=true")
    print("project_semantic_authority=NONE canonical_write_authorized=false structural_identity_authorized=false")


if __name__ == "__main__":
    main()
