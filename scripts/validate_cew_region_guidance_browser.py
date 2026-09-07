#!/usr/bin/env python3
"""Browser gate for CEW non-semantic automatic regions plus corrective ROI."""
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
            raise AssertionError(f"CEW_REGION_GUIDANCE_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test server
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_REGION_GUIDANCE_APP_START_TIMEOUT")


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
            response = page.goto(f"{base}/workbench/document-discovery", wait_until="networkidle")
            assert response is not None and response.status == 200
            headers = {k.lower(): v for k, v in response.headers.items()}
            assert headers.get("x-cew-region-guidance") == "AUTO_LAYOUT_PLUS_HUMAN_ROI_V1", headers
            assert headers.get("x-cew-region-semantic-authority") == "NONE", headers
            assert page.locator('body[data-cew-region-guidance="v1"]').count() == 1
            assert page.locator("#preview-regions").count() == 1
            assert page.locator("#preview-roi").count() == 1

            svg = """<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='700'>
            <rect width='1000' height='700' fill='white'/>
            <g fill='none' stroke='black' stroke-width='5'>
              <rect x='60' y='60' width='360' height='240'/><path d='M80 180 L380 100 M90 230 L390 260'/>
              <rect x='580' y='60' width='350' height='240'/><path d='M610 260 L900 100 M620 130 L890 230'/>
              <rect x='60' y='410' width='360' height='220'/><path d='M90 450 L390 590 M90 560 L390 450'/>
              <rect x='580' y='410' width='350' height='220'/><path d='M610 450 L900 590 M620 590 L890 450'/>
            </g></svg>"""
            page.evaluate(
                """svg => {
                  const img=document.getElementById('page');
                  document.getElementById('viewer-placeholder').hidden=true;
                  img.hidden=false;
                  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
                }""",
                svg,
            )
            page.wait_for_function("document.getElementById('page').naturalWidth > 0")
            page.evaluate("window.CEWRegionGuidance.refresh()")
            page.wait_for_function("window.CEWRegionGuidance.regions().length >= 2")
            count = page.evaluate("window.CEWRegionGuidance.regions().length")
            assert count >= 2, count

            # Let the image-load refresh scheduled by the production client
            # settle before simulating the first operator click.
            page.wait_for_timeout(250)
            page.evaluate(
                """() => {
                  const regions=window.CEWRegionGuidance.regions();
                  window.CEWRegionGuidance.focus(regions[0].id);
                }"""
            )
            page.wait_for_function(
                "document.querySelectorAll('#cew-region-overlay .cew-region-proposal').length >= 2"
            )
            page.wait_for_function(
                "document.querySelectorAll('#cew-region-overlay .cew-region-proposal.active').length === 1"
            )
            assert page.locator("#cew-region-overlay .cew-region-proposal").count() >= 2

            page.locator("#preview-roi").click()
            assert page.locator("#preview-roi").get_attribute("aria-pressed") == "true"
            assert "crosshair" in page.locator("#viewer").evaluate("el => getComputedStyle(el).cursor")

            source = page.locator("#cew-governed-async-script").text_content() or ""
            assert "Sessione CEW scaduta" in source
            assert "identificativo lavoro assente" in source
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

    print("CEW_REGION_GUIDANCE_BROWSER_V1_PASS")
    print("automatic_regions=NON_SEMANTIC_WHITESPACE_LAYOUT corrective_roi=ON_DEMAND")
    print("semantic_authority=NONE canonical_write=false session_expiry=FAIL_CLOSED")


if __name__ == "__main__":
    main()
