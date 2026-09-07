#!/usr/bin/env python3
"""Chromium gate for real layout confirmation, local analysis and semantic lock."""
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
            raise AssertionError(f"CEW_LAYOUT_PHASE_GATE_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_LAYOUT_PHASE_GATE_APP_START_TIMEOUT")


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
            assert headers.get("x-cew-layout-phase-gate") == "LAYOUT_CONFIRM_BEFORE_SEMANTICS_V2", headers
            assert headers.get("x-cew-local-unit-analysis") == "BROWSER_GRAPHIC_FRAGMENTS_V1", headers
            assert headers.get("x-cew-semantic-gate") == "LOCAL_BACKEND_CANDIDATE_REQUIRED_V1", headers
            assert page.locator('body[data-cew-layout-phase-gate="v2"]').count() == 1
            assert page.locator("#cew-layout-structure-tab").count() == 1
            assert page.locator("#cew-decision-tab").is_hidden()

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
            page.evaluate("window.CEWLayoutLearning.refresh()")
            page.wait_for_function("window.CEWLayoutLearning.units().length >= 3")
            page.wait_for_function("window.CEWLayoutPhaseGate && window.CEWLayoutPhaseGate.describe().label.includes('candidate')")
            assert "colonne di lettura candidate" in page.locator("#cew-layout-proposal").inner_text().lower()
            before = page.evaluate("window.CEWLayoutPhaseGate.state()")
            assert before["confirmed"] is False, before
            assert page.locator("#cew-layout-confirm").is_visible()

            # This deliberately uses the actual UI control rather than the JS API.
            page.locator("#cew-layout-confirm").click()
            page.wait_for_function("window.CEWLayoutPhaseGate.state().confirmed === true")
            assert "struttura confermata" in page.locator("#cew-layout-state").inner_text().lower()
            assert page.locator("#cew-layout-confirm").is_hidden()
            assert page.locator("#cew-layout-reset").is_visible()
            assert "seleziona una unità" in page.locator("#cew-layout-feedback").inner_text().lower()

            units = page.evaluate("window.CEWLayoutLearning.units()")
            assert len(units) >= 3, units
            page.evaluate("id => window.CEWLayoutPhaseGate.selectUnit(id)", units[0]["id"])
            page.wait_for_function("window.CEWLayoutPhaseGate.state().activeUnit !== null")
            local = page.evaluate("window.CEWLayoutPhaseGate.state()")
            assert local["localCandidateCount"] >= 1, local
            assert local["semanticReady"] is False, local
            assert page.locator("#cew-decision-tab").is_hidden()
            assert "semantica resta bloccata" in page.locator("#cew-local-block").inner_text().lower()

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

    print("CEW_LAYOUT_PHASE_GATE_BROWSER_V2_PASS")
    print("real_confirm_click=PASS visible_feedback=PASS local_unit_analysis=PASS")
    print("semantic_gate=LOCAL_BACKEND_CANDIDATE_REQUIRED canonical_write=false")


if __name__ == "__main__":
    main()
