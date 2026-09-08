#!/usr/bin/env python3
"""Browser/runtime contract for CEW Professional Document Workbench v2.

This test starts the real FastAPI application, opens the mounted Document
Discovery route in Chromium, and validates the DOM and mature-panel interaction
state that a user actually gets. Static source markers alone are deliberately
insufficient.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_app(url: str, proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            raise AssertionError(f"CEW_BROWSER_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test server
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_BROWSER_APP_START_TIMEOUT")


def main() -> None:
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env["CEW_AUTH_DISABLED_FOR_TEST"] = "1"
    env.pop("RENDER", None)
    env.pop("VERCEL", None)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    page_errors: list[str] = []
    console_errors: list[str] = []

    try:
        wait_for_app(f"{base}/workbench/document-discovery", proc)
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
            response = page.goto(
                f"{base}/workbench/document-discovery",
                wait_until="networkidle",
            )
            assert response is not None and response.status == 200
            headers = {k.lower(): v for k, v in response.headers.items()}
            assert headers.get("x-cew-document-workbench") == "PROFESSIONAL_V2", headers
            assert headers.get("x-cew-panel-architecture") == "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS", headers
            assert headers.get("x-cew-panel-quality") == "MATURE_V1", headers

            # Startup errors are checked before DOM assertions so a broken script
            # cannot be mistaken for a layout-marker failure.
            assert not page_errors, f"CEW_BROWSER_PAGE_ERRORS: {page_errors}"
            assert not console_errors, f"CEW_BROWSER_CONSOLE_ERRORS: {console_errors}"

            required = (
                "body.cew-professional-document",
                "#cew-activity-rail",
                ".cew-primary-head",
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
            assert page.locator('body[data-cew-panel-quality="mature-v1"]').count() == 1

            # The title/provider must actually be composed into the mature top bar.
            assert page.locator("header .cew-title-main").count() == 1
            assert page.locator("header #provider").count() == 1
            assert page.locator("#cew-primary-title").inner_text().strip().upper() == "CLUSTER"
            assert page.locator("#cew-inspector-head").is_visible()
            assert page.locator("#cew-inspector-tabs").is_visible()

            # Activity Rail exposes stable current state and compact iconography.
            cluster_view = page.locator('#cew-activity-rail button[data-nav="clusters"]')
            assert cluster_view.get_attribute("aria-pressed") == "true"
            assert cluster_view.inner_text().strip() == "◎"
            assert cluster_view.get_attribute("aria-controls") == "cew-nav-clusters"
            assert "Alt+3" in (cluster_view.get_attribute("title") or "")

            # The document editor is the flexible central surface.
            editor = page.locator("#cew-canvas-shell").bounding_box()
            left = page.locator("aside.left").bounding_box()
            right = page.locator("aside.right").bounding_box()
            assert editor and left and right
            assert editor["width"] >= 420, editor
            assert 220 <= left["width"] <= 500, left
            assert 260 <= right["width"] <= 560, right

            # Accessible panel/sash state is materialized, not inferred by source markers.
            assert page.locator("#cew-toggle-primary").get_attribute("aria-expanded") == "true"
            assert page.locator("#cew-toggle-aux").get_attribute("aria-expanded") == "true"
            for sash_id, min_value, max_value in (
                ("#cew-left-sash", "220", "500"),
                ("#cew-right-sash", "260", "560"),
            ):
                sash = page.locator(sash_id)
                assert sash.get_attribute("aria-orientation") == "vertical"
                assert sash.get_attribute("aria-valuemin") == min_value
                assert sash.get_attribute("aria-valuemax") == max_value
                assert int(sash.get_attribute("aria-valuenow") or "0") > 0

            tabs = page.locator("#cew-inspector-tabs")
            assert tabs.get_attribute("role") == "tablist"
            props_tab = page.locator('#cew-inspector-tabs button[data-inspector="properties"]')
            assert props_tab.get_attribute("role") == "tab"
            assert props_tab.get_attribute("aria-selected") == "true"

            # The active-view title is owned by the sidebar header only; body duplicate is hidden.
            duplicate_title = page.locator("#cew-nav-clusters > .cew-sidebar-title:first-child")
            if duplicate_title.count():
                assert duplicate_title.is_hidden()

            # Mature activity shortcuts switch the view without changing topology.
            page.keyboard.press("Alt+4")
            page.wait_for_timeout(80)
            assert page.locator("#cew-primary-title").inner_text().strip().upper() == "DA VERIFICARE"
            verify_panel = page.locator("#cew-nav-verify")
            assert verify_panel.is_visible()
            verify_text = verify_panel.inner_text()
            assert "Nessuna regione grafica acquisita" in verify_text
            assert "NESSUNA_REGIONE_GRAFICA_ACQUISITA" not in verify_text
            assert page.locator('#cew-activity-rail button[data-nav="verify"]').get_attribute("aria-pressed") == "true"

            # Primary sidebar collapse/restore expands the central editor.
            initial_editor_width = page.locator("#cew-canvas-shell").bounding_box()["width"]
            verify_view = page.locator('#cew-activity-rail button[data-nav="verify"]')
            verify_view.click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-primary-collapsed").count() == 1
            collapsed_editor = page.locator("#cew-canvas-shell").bounding_box()
            assert collapsed_editor and collapsed_editor["width"] > initial_editor_width
            assert page.locator("#cew-toggle-primary").get_attribute("aria-expanded") == "false"
            verify_view.click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-primary-collapsed").count() == 0
            assert page.locator("#cew-toggle-primary").get_attribute("aria-expanded") == "true"

            # Ctrl+J provides mature right-sidebar keyboard parity and persists state.
            page.keyboard.press("Control+J")
            page.wait_for_timeout(80)
            assert page.locator("body.cew-aux-collapsed").count() == 1
            assert page.locator("#cew-toggle-aux").get_attribute("aria-expanded") == "false"
            stored = page.evaluate(
                "JSON.parse(localStorage.getItem('cew.documentDiscovery.workbench.v2'))"
            )
            assert stored["rightVisible"] is False, stored
            page.keyboard.press("Control+J")
            page.wait_for_timeout(80)
            assert page.locator("body.cew-aux-collapsed").count() == 0
            assert page.locator("#cew-toggle-aux").get_attribute("aria-expanded") == "true"

            # Decision remains unavailable while teaching is blocked.
            assert page.locator("#cew-decision-tab").is_hidden()
            assert not page_errors, f"CEW_BROWSER_PAGE_ERRORS_LATE: {page_errors}"
            assert not console_errors, f"CEW_BROWSER_CONSOLE_ERRORS_LATE: {console_errors}"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    print("CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_BROWSER_MATURE_PANELS_PASS")
    print("mounted_route=PROFESSIONAL_V2 panel_quality=MATURE_V1 canonical_panel_dom=MATERIALIZED")
    print("primary_sidebar=COLLAPSE_RESTORE_PASS auxiliary_sidebar=CTRL_J_PERSIST_PASS")
    print("panel_copy=HUMAN_READABLE single_title=PASS accessibility_state=PASS")


if __name__ == "__main__":
    main()
