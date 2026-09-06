#!/usr/bin/env python3
"""Browser-level smoke contract for CEW Professional Document Workbench v2.

Static HTML markers are insufficient for a workbench shell: this test executes the
actual generated page in Chromium and fails on startup JavaScript errors or when
canonical panel parts do not materialize in the DOM.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

import cew_professional_document_workbench as professional


HTML = professional._patched_page().encode("utf-8")
STATUS = {
    "max_preview_pdf_bytes": 12 * 1024 * 1024,
    "provider_states": {
        "structured_graphic": {"state": "READY"},
        "visual_foundation": {"state": "IMPLEMENTED_NOT_PROVISIONED"},
    },
    "governed_sources": [],
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def do_GET(self):  # noqa: N802 - stdlib handler contract
        path = urlparse(self.path).path
        if path in {"/", "/workbench/document-discovery"}:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(HTML)
            return
        if path == "/api/workbench/document-discovery/status":
            body = json.dumps(STATUS).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    page_errors: list[str] = []
    console_errors: list[str] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                else None,
            )
            page.goto(f"{base}/workbench/document-discovery", wait_until="networkidle")

            required = (
                "body.cew-professional-document",
                "#cew-activity-rail",
                "#cew-primary-head",
                "#cew-primary-content",
                "#cew-left-sash",
                "#cew-canvas-shell",
                "#cew-editor-bar",
                "#cew-inspector-head",
                "#cew-inspector-tabs",
                "#cew-right-sash",
                "#cew-statusbar",
            )
            missing = [selector for selector in required if page.locator(selector).count() != 1]
            assert not missing, f"CEW_BROWSER_DOM_MISSING: {missing}"
            assert not page_errors, f"CEW_BROWSER_PAGE_ERRORS: {page_errors}"
            assert not console_errors, f"CEW_BROWSER_CONSOLE_ERRORS: {console_errors}"

            # The document editor must be the flexible central surface, not a narrow remnant.
            editor = page.locator("#cew-canvas-shell").bounding_box()
            left = page.locator("aside.left").bounding_box()
            right = page.locator("aside.right").bounding_box()
            assert editor and left and right
            assert editor["width"] >= 420, editor
            assert 220 <= left["width"] <= 500, left
            assert 260 <= right["width"] <= 560, right

            # Primary sidebar collapse/restore is available from the persistent activity rail.
            initial_editor_width = editor["width"]
            page.locator('#cew-activity-rail button[data-nav="clusters"]').click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-primary-collapsed").count() == 1
            collapsed_editor = page.locator("#cew-canvas-shell").bounding_box()
            assert collapsed_editor and collapsed_editor["width"] > initial_editor_width
            page.locator('#cew-activity-rail button[data-nav="clusters"]').click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-primary-collapsed").count() == 0

            # Auxiliary inspector can collapse and persists its state; decision remains hidden.
            page.locator("#cew-hide-aux").click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-aux-collapsed").count() == 1
            stored = page.evaluate(
                "JSON.parse(localStorage.getItem('cew.documentDiscovery.workbench.v2'))"
            )
            assert stored["rightVisible"] is False, stored
            assert page.locator("#cew-decision-tab").is_hidden()

            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    print("CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_BROWSER_PASS")
    print("startup_javascript=PASS canonical_panel_dom=MATERIALIZED")
    print("primary_sidebar=COLLAPSE_RESTORE_PASS auxiliary_sidebar=COLLAPSE_PERSIST_PASS")


if __name__ == "__main__":
    main()
