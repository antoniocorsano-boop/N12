#!/usr/bin/env python3
"""Chromium gate for readable CEW ReadingUnit working focus."""
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
            raise AssertionError(f"CEW_LOCAL_FOCUS_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_LOCAL_FOCUS_APP_START_TIMEOUT")


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
    try:
        wait_for_app(f"{base}/workbench/document-discovery", proc)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            response = page.goto(f"{base}/workbench/document-discovery", wait_until="networkidle")
            assert response is not None and response.status == 200
            headers = {k.lower(): v for k, v in response.headers.items()}
            assert headers.get("x-cew-local-unit-focus") == "READING_UNIT_WORKING_VIEW_V1", headers
            assert headers.get("x-cew-local-focus-navigation") == "COLUMN_WIDTH_FIT_VERTICAL_SCROLL_V1", headers
            assert headers.get("x-cew-visual-result-navigation") == "RESULT_FOCUS_REVIEW_V1", headers
            assert headers.get("x-cew-canonical-write") == "false", headers

            svg = """<svg xmlns='http://www.w3.org/2000/svg' width='1400' height='900'>
            <rect width='1400' height='900' fill='white'/>
            <g fill='none' stroke='black' stroke-width='7'>
              <path d='M60 110 L170 65 L280 110'/><path d='M70 360 L270 360'/><path d='M70 500 L250 500'/><path d='M80 700 L260 660'/>
              <path d='M390 110 L500 65 L610 110'/><path d='M400 360 L600 360'/><path d='M400 500 L580 500'/><path d='M410 700 L590 660'/>
              <path d='M720 110 L830 65 L940 110'/><path d='M730 360 L930 360'/><path d='M730 500 L910 500'/><path d='M740 700 L920 660'/>
              <path d='M1050 110 L1160 65 L1270 110'/><path d='M1060 360 L1260 360'/><path d='M1060 500 L1240 500'/><path d='M1070 700 L1250 660'/>
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
            page.wait_for_function("window.CEWLayoutLearning.units().length >= 4")
            page.locator("#cew-layout-confirm").click()
            page.wait_for_function("window.CEWLayoutPhaseGate.state().confirmed === true")
            units = page.locator("#cew-layout-overlay .cew-layout-unit")
            assert units.count() >= 4
            units.nth(1).click()
            page.wait_for_function("document.body.dataset.cewLocalFocus === 'active'")
            page.wait_for_timeout(180)

            geometry = page.evaluate(
                """() => {
                  const v=document.getElementById('viewer').getBoundingClientRect();
                  const active=document.querySelector('#cew-layout-overlay .cew-layout-unit.active').getBoundingClientRect();
                  const img=document.getElementById('page').getBoundingClientRect();
                  const others=[...document.querySelectorAll('#cew-layout-overlay .cew-layout-unit:not(.active)')].map(x=>getComputedStyle(x).display);
                  const overlay=document.getElementById('cew-local-overlay');
                  return {
                    viewer:{w:v.width,h:v.height}, active:{w:active.width,h:active.height}, image:{w:img.width,h:img.height},
                    scrollHeight:document.getElementById('viewer').scrollHeight,
                    clientHeight:document.getElementById('viewer').clientHeight,
                    others,
                    localOverlay:overlay?getComputedStyle(overlay).display:'missing',
                    clusterOverlay:getComputedStyle(document.getElementById('cluster-overlay')).display,
                    title:document.querySelector('#cew-layout-overlay .cew-layout-unit.active').getAttribute('title'),
                    mode:window.CEWLocalFocus.state()
                  };
                }"""
            )
            assert geometry["active"]["w"] >= geometry["viewer"]["w"] * 0.55, geometry
            assert geometry["scrollHeight"] > geometry["clientHeight"] * 1.35, geometry
            assert all(value == "none" for value in geometry["others"]), geometry
            assert geometry["localOverlay"] == "none", geometry
            assert geometry["clusterOverlay"] == "none", geometry
            assert geometry["title"] is None, geometry

            page.locator("#preview-overview").click()
            page.wait_for_function("document.body.dataset.cewLocalFocus === 'none'")
            page.locator("#cew-reference-start").click()
            page.wait_for_function("window.CEWVisualReferenceSearch.state().mode === 'SELECTING'")
            page.wait_for_function("document.body.dataset.cewLocalFocus === 'active'")
            refocus = page.evaluate("() => ({scrollHeight:viewer.scrollHeight,clientHeight:viewer.clientHeight,active:document.querySelector('#cew-layout-overlay .cew-layout-unit.active').getBoundingClientRect().width,viewer:viewer.getBoundingClientRect().width})")
            assert refocus["active"] >= refocus["viewer"] * 0.55, refocus
            assert refocus["scrollHeight"] > refocus["clientHeight"] * 1.35, refocus
            assert not page_errors, page_errors
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    print("CEW_LOCAL_FOCUS_BROWSER_V1_PASS")
    print("reading_unit=WIDTH_FIT tall_unit=VERTICAL_SCROLL overlays=SUPPRESSED hover_tooltip=REMOVED reference_refocus=PASS")
    print("semantic_authority=NONE canonical_write=false")


if __name__ == "__main__":
    main()
