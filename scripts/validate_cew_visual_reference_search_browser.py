#!/usr/bin/env python3
"""Chromium gate for CEW reference-first visual similarity review."""
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
            raise AssertionError(f"CEW_VISUAL_REFERENCE_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_VISUAL_REFERENCE_APP_START_TIMEOUT")


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
            assert headers.get("x-cew-visual-reference-search") == "REFERENCE_FIRST_REVIEW_V1", headers
            assert headers.get("x-cew-visual-similarity") == "DETERMINISTIC_LAYOUT_AWARE_V1", headers
            assert headers.get("x-cew-visual-search-result-action") == "REVIEW_ONLY_V1", headers
            assert headers.get("x-cew-visual-search-semantic-authority") == "NONE", headers
            assert headers.get("x-cew-canonical-write") == "false", headers

            svg = """<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800'>
            <rect width='1200' height='800' fill='white'/>
            <g fill='none' stroke='black' stroke-width='8'>
              <path d='M40 120 L150 70 L260 120'/><path d='M50 330 L250 330'/><path d='M50 430 L220 430'/><path d='M70 540 L240 510'/>
              <path d='M330 120 L440 70 L550 120'/><path d='M340 330 L540 330'/><path d='M340 430 L510 430'/><path d='M360 540 L530 510'/>
              <path d='M620 120 L730 70 L840 120'/><path d='M630 330 L830 330'/><path d='M630 430 L800 430'/><path d='M650 540 L820 510'/>
              <path d='M910 120 L1020 70 L1130 120'/><path d='M920 330 L1120 330'/><path d='M920 430 L1090 430'/><path d='M940 540 L1110 510'/>
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
            page.evaluate("ensureInspectionStage(); renderPageGeometry(false)")
            page.wait_for_function("document.getElementById('page-stage') !== null")
            page.evaluate("window.CEWLayoutLearning.refresh()")
            page.wait_for_function("window.CEWLayoutLearning.units().length >= 4")
            page.wait_for_function("window.CEWLayoutPhaseGate && document.getElementById('cew-layout-confirm')")
            page.locator("#cew-layout-confirm").click()
            page.wait_for_function("window.CEWLayoutPhaseGate.state().confirmed === true")
            page.wait_for_function("document.querySelectorAll('#cew-layout-overlay .cew-layout-unit').length >= 4")

            first_unit = page.locator("#cew-layout-overlay .cew-layout-unit").first
            first_unit.click()
            page.wait_for_function("window.CEWLayoutPhaseGate.state().activeUnit !== null")
            page.wait_for_function("!document.getElementById('cew-visual-search').hidden")
            assert page.locator("#cew-local-overlay").evaluate("el => getComputedStyle(el).display") == "none"
            assert page.locator("#cew-decision-tab").is_hidden()

            page.locator("#cew-reference-start").click()
            page.wait_for_function("window.CEWVisualReferenceSearch.state().mode === 'SELECTING'")
            bbox = first_unit.bounding_box()
            assert bbox is not None
            x1 = bbox["x"] + bbox["width"] * 0.08
            x2 = bbox["x"] + bbox["width"] * 0.92
            y1 = bbox["y"] + bbox["height"] * 0.04
            y2 = bbox["y"] + bbox["height"] * 0.28
            page.mouse.move(x1, y1)
            page.mouse.down()
            page.mouse.move(x2, y2, steps=8)
            page.mouse.up()
            page.wait_for_function("window.CEWVisualReferenceSearch.state().mode === 'REFERENCE_READY'")
            assert page.locator(".cew-visual-ref-box").count() == 1
            assert page.locator("#cew-reference-search").is_visible()

            page.locator("#cew-reference-search").click()
            page.wait_for_function("window.CEWVisualReferenceSearch.state().mode === 'RESULTS'")
            page.wait_for_function("document.querySelectorAll('.cew-visual-match-box').length >= 2")
            state = page.evaluate("window.CEWVisualReferenceSearch.state()")
            assert len(state["matches"]) >= 3, state
            assert page.locator("#cew-visual-results-list label").count() >= 2
            assert page.locator("#cew-decision-tab").is_hidden()
            assert document_authority(page) == "none"
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

    print("CEW_VISUAL_REFERENCE_SEARCH_BROWSER_V1_PASS")
    print("reference_rectangle=REAL_DRAG explicit_search=PASS repeated_units=PASS review_results=PASS")
    print("raw_components=HIDDEN_BY_DEFAULT semantic_authority=NONE canonical_write=false")


def document_authority(page) -> str:
    return page.evaluate("document.body.dataset.cewVisualSearchAuthority || ''")


if __name__ == "__main__":
    main()
