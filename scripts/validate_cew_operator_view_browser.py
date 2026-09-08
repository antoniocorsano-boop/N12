#!/usr/bin/env python3
"""Chromium gate for clean operator-facing local review."""
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
            raise AssertionError(f"CEW_OPERATOR_VIEW_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_OPERATOR_VIEW_APP_START_TIMEOUT")


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
            assert headers.get("x-cew-operator-view") == "CLEAN_LOCAL_REVIEW_V1", headers
            assert headers.get("x-cew-local-primitive-visibility") == "DIAGNOSTIC_OPT_IN_V1", headers
            assert headers.get("x-cew-local-unit-focus") == "READING_UNIT_WORKING_VIEW_V1", headers
            assert headers.get("x-cew-local-focus-navigation") == "COLUMN_WIDTH_FIT_VERTICAL_SCROLL_V1", headers
            assert page.locator('body[data-cew-operator-view="clean-local-v1"]').count() == 1

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
            page.evaluate("ensureInspectionStage(); renderPageGeometry(false); window.CEWLayoutLearning.refresh()")
            page.wait_for_function("window.CEWLayoutLearning.units().length >= 3")
            page.locator("#cew-layout-confirm").click()
            page.wait_for_function("window.CEWLayoutPhaseGate.state().confirmed === true")
            page.locator("#cew-layout-overlay .cew-layout-unit").first.click()
            page.wait_for_function("window.CEWLayoutPhaseGate.state().activeUnit !== null")
            page.wait_for_function("document.body.dataset.cewLocalFocus === 'active'")
            page.wait_for_timeout(180)
            page.evaluate("window.CEWOperatorView.sync()")
            page.wait_for_timeout(80)

            summary = page.locator("#cew-local-summary").inner_text().lower()
            assert "vista" in summary and ("lavoro" in summary or "locale" in summary), summary
            assert "non sono" in page.locator("#cew-local-diagnostics-note").inner_text().lower()
            assert "u1" in page.locator("#cew-editor-evidence").inner_text().lower()
            assert page.locator("#cew-local-diagnostics-toggle").is_visible()

            geometry = page.evaluate(
                """() => {
                  const viewer=document.getElementById('viewer');
                  const vr=viewer.getBoundingClientRect();
                  const active=document.querySelector('#cew-layout-overlay .cew-layout-unit.active');
                  const ar=active.getBoundingClientRect();
                  return {
                    viewerWidth:vr.width,
                    activeWidth:ar.width,
                    scrollHeight:viewer.scrollHeight,
                    clientHeight:viewer.clientHeight,
                    hiddenOthers:[...document.querySelectorAll('#cew-layout-overlay .cew-layout-unit:not(.active)')].every(x=>getComputedStyle(x).display==='none'),
                    activeTitle:active.getAttribute('title'),
                    clusterOverlay:getComputedStyle(document.getElementById('cluster-overlay')).display
                  };
                }"""
            )
            assert geometry["activeWidth"] >= geometry["viewerWidth"] * 0.55, geometry
            assert geometry["scrollHeight"] > geometry["clientHeight"] * 1.25, geometry
            assert geometry["hiddenOthers"], geometry
            assert geometry["activeTitle"] is None, geometry
            assert geometry["clusterOverlay"] == "none", geometry

            overlay = page.locator("#cew-local-overlay")
            assert overlay.count() == 1
            assert overlay.evaluate("el => getComputedStyle(el).display") == "none"
            assert page.locator("#cew-local-overlay .cew-local-fragment").count() >= 1

            page.locator("#cew-local-diagnostics-toggle").click()
            assert overlay.evaluate("el => getComputedStyle(el).display") != "none"
            page.locator("#cew-local-diagnostics-toggle").click()
            assert overlay.evaluate("el => getComputedStyle(el).display") == "none"

            assert page.locator("#cew-region-pill").evaluate("el => getComputedStyle(el).display") == "none"
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

    print("CEW_OPERATOR_CLEAN_LOCAL_VIEW_PASS")
    print("reading_unit=WIDTH_FIT_VERTICAL_SCROLL raw_fragments=DIAGNOSTIC_ONLY default_visible=false active_unit=PRIMARY")
    print("semantic_authority=NONE canonical_write=false")


if __name__ == "__main__":
    main()
