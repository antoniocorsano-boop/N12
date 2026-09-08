#!/usr/bin/env python3
"""Browser gate for CEW layout hypotheses and teach-one-relation propagation."""
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
            raise AssertionError(f"CEW_LAYOUT_LEARNING_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test server
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_LAYOUT_LEARNING_APP_START_TIMEOUT")


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
            assert headers.get("x-cew-layout-learning") == "HYPOTHESIS_PLUS_TEACH_ONE_RELATION_V1", headers
            assert headers.get("x-cew-layout-semantic-authority") == "NONE", headers
            assert headers.get("x-cew-layout-prototype-persistence") == "LOCAL_NON_CANONICAL_V1", headers
            assert page.locator('body[data-cew-layout-learning="v1"]').count() == 1
            assert page.locator("#preview-layout").count() == 1
            assert page.locator("#preview-teach-layout").count() == 1

            svg = """<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800'>
            <rect width='1200' height='800' fill='white'/>
            <g fill='black'>
              <rect x='40' y='60' width='220' height='120'/><rect x='50' y='300' width='200' height='22'/><rect x='50' y='420' width='200' height='22'/><rect x='50' y='540' width='200' height='22'/>
              <rect x='330' y='60' width='220' height='120'/><rect x='340' y='300' width='200' height='22'/><rect x='340' y='420' width='200' height='22'/><rect x='340' y='540' width='200' height='22'/>
              <rect x='620' y='60' width='220' height='120'/><rect x='630' y='300' width='200' height='22'/><rect x='630' y='420' width='200' height='22'/><rect x='630' y='540' width='200' height='22'/>
              <rect x='910' y='60' width='220' height='120'/><rect x='920' y='300' width='200' height='22'/><rect x='920' y='420' width='200' height='22'/><rect x='920' y='540' width='200' height='22'/>
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
            page.evaluate("window.CEWLayoutLearning.refresh()")
            page.wait_for_function("window.CEWLayoutLearning.hypotheses().length >= 1")
            hypotheses = page.evaluate("window.CEWLayoutLearning.hypotheses()")
            vertical = [h for h in hypotheses if h["orientation"] == "VERTICAL_STACK"]
            assert vertical, hypotheses
            assert len(vertical[0]["units"]) >= 3, vertical[0]

            prototype = page.evaluate(
                """() => window.CEWLayoutLearning.teach(
                  {x:0.03,y:0.06,w:0.19,h:0.18},
                  {x:0.03,y:0.34,w:0.19,h:0.39}
                )"""
            )
            assert prototype["orientation"] == "VERTICAL_STACK", prototype
            assert prototype["semantic_authority"] == "NONE", prototype
            assert prototype["canonical_write_authorized"] is False, prototype
            units = page.evaluate("window.CEWLayoutLearning.units()")
            assert len(units) >= 3, units
            assert all(0 <= u["x"] <= 1 and 0 <= u["y"] <= 1 for u in units), units
            assert all(0 < u["w"] <= 1 and 0 < u["h"] <= 1 for u in units), units

            page.locator("#preview-teach-layout").click()
            assert page.locator("#preview-teach-layout").get_attribute("aria-pressed") == "true"
            assert "crosshair" in page.locator("#viewer").evaluate("el => getComputedStyle(el).cursor")
            page.locator("#preview-teach-layout").click()
            assert page.locator("#preview-teach-layout").get_attribute("aria-pressed") == "false"

            source = page.locator("#cew-layout-learning-script").text_content() or ""
            for marker in (
                "LAYOUT_PROTOTYPE_V1",
                "HUMAN_DEMONSTRATION",
                "semantic_authority:'NONE'",
                "localStorage.setItem",
                "function automaticHypotheses()",
                "function propagate(proto)",
            ):
                assert marker in source, marker
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

    print("CEW_LAYOUT_LEARNING_BROWSER_V1_PASS")
    print("layout_hypothesis=VERTICAL_OR_HORIZONTAL teach_one_relation=PASS propagate=PASS")
    print("semantic_authority=NONE persistence=LOCAL_NON_CANONICAL canonical_write=false")


if __name__ == "__main__":
    main()
