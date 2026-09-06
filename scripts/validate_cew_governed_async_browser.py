#!/usr/bin/env python3
"""Chromium gate for governed async analysis and transient 502 recovery."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_app(url: str, proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            raise AssertionError(f"CEW_GOVERNED_ASYNC_BROWSER_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test server
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_GOVERNED_ASYNC_BROWSER_APP_START_TIMEOUT")


def main() -> None:
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env["CEW_AUTH_DISABLED_FOR_TEST"] = "1"
    env.pop("RENDER", None)
    env.pop("VERCEL", None)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
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
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            enqueue_calls = {"count": 0}
            poll_calls = {"count": 0}
            legacy_calls = {"count": 0}

            def handle_enqueue(route):
                enqueue_calls["count"] += 1
                if enqueue_calls["count"] == 1:
                    route.fulfill(
                        status=502,
                        content_type="application/json",
                        body=json.dumps({"state": "TRANSIENT_TEST_502"}),
                    )
                else:
                    route.fulfill(
                        status=202,
                        content_type="application/json",
                        body=json.dumps({"state": "QUEUED", "job_id": "DGJ-browser-test"}),
                    )

            def handle_poll(route):
                poll_calls["count"] += 1
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "state": "FAILED",
                        "job_id": "DGJ-browser-test",
                        "reason": "CEW_TEST_STOP_AFTER_ASYNC_ROUTE",
                    }),
                )

            def handle_legacy(route):
                legacy_calls["count"] += 1
                route.fulfill(
                    status=500,
                    content_type="application/json",
                    body=json.dumps({"reason": "LEGACY_GOVERNED_ROUTE_MUST_NOT_BE_CALLED"}),
                )

            page.route("**/api/workbench/document-discovery/analyze-governed-async", handle_enqueue)
            page.route("**/api/workbench/document-discovery/governed-job/**", handle_poll)
            page.route("**/api/workbench/document-discovery/analyze-governed", handle_legacy)

            response = page.goto(f"{base}/workbench/document-discovery", wait_until="networkidle")
            assert response is not None and response.status == 200
            headers = {k.lower(): v for k, v in response.headers.items()}
            assert headers.get("x-cew-governed-analysis") == "ASYNC_BOUNDED_RECONSTRUCT_V1", headers
            assert page.locator('body[data-cew-governed-analysis="async-bounded-reconstruct-v1"]').count() == 1
            assert page.locator("#source option").count() > 1

            page.locator("#project").fill("N12")
            page.locator("#source").select_option(index=1)
            page.locator("#analyze").click()
            page.wait_for_function(
                "document.getElementById('intake-message').textContent.includes('CEW_TEST_STOP_AFTER_ASYNC_ROUTE')",
                timeout=10000,
            )

            assert enqueue_calls["count"] == 2, enqueue_calls
            assert poll_calls["count"] >= 1, poll_calls
            assert legacy_calls["count"] == 0, legacy_calls
            assert "HTTP 502" not in page.locator("#intake-message").inner_text()
            assert not page_errors, page_errors
            assert not console_errors, console_errors
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    print("CEW_GOVERNED_ASYNC_BROWSER_PASS")
    print("governed_action=ASYNC_BOUNDED legacy_sync_route=NOT_CALLED")
    print("transient_http_502=AUTOMATIC_RETRY terminal_error=DOMAIN_REASON")


if __name__ == "__main__":
    main()
