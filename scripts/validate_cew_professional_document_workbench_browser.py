#!/usr/bin/env python3
"""Browser/runtime contract for CEW Professional Document Workbench v2.

This test starts the real FastAPI application, opens the mounted Document
Discovery route in Chromium, and validates the DOM that a user actually gets.
Static source markers alone are deliberately insufficient.
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

            # The title/provider must actually be composed into the mature top bar.
            assert page.locator("header .cew-title-main").count() == 1
            assert page.locator("header #provider").count() == 1
            # innerText reflects CSS text-transform:uppercase on the rendered header.
            assert page.locator("#cew-primary-title").inner_text().strip().upper() == "CLUSTER"
            assert page.locator("#cew-inspector-head").is_visible()
            assert page.locator("#cew-inspector-tabs").is_visible()

            # The document editor is the flexible central surface.
            editor = page.locator("#cew-canvas-shell").bounding_box()
            left = page.locator("aside.left").bounding_box()
            right = page.locator("aside.right").bounding_box()
            assert editor and left and right
            assert editor["width"] >= 420, editor
            assert 220 <= left["width"] <= 500, left
            assert 260 <= right["width"] <= 560, right

            # Primary sidebar collapse/restore is available from the persistent rail.
            initial_editor_width = editor["width"]
            cluster_view = page.locator('#cew-activity-rail button[data-nav="clusters"]')
            cluster_view.click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-primary-collapsed").count() == 1
            collapsed_editor = page.locator("#cew-canvas-shell").bounding_box()
            assert collapsed_editor and collapsed_editor["width"] > initial_editor_width
            cluster_view.click()
            page.wait_for_timeout(50)
            assert page.locator("body.cew-primary-collapsed").count() == 0

            # Auxiliary inspector collapse persists; decision remains unavailable.
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
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    print("CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_BROWSER_PASS")
    print("mounted_route=PROFESSIONAL_V2 startup_javascript=PASS canonical_panel_dom=MATERIALIZED")
    print("primary_sidebar=COLLAPSE_RESTORE_PASS auxiliary_sidebar=COLLAPSE_PERSIST_PASS")


if __name__ == "__main__":
    main()
