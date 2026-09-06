#!/usr/bin/env python3
"""Browser gate for the HVA-refined operator copy inside MATURE_V1 panels."""
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
            raise AssertionError(f"CEW_MATURE_CONTENT_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test server
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_MATURE_CONTENT_APP_START_TIMEOUT")


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
            assert headers.get("x-cew-panel-quality") == "MATURE_V1", headers
            assert headers.get("x-cew-panel-content") == "HVA_REFINED_V1", headers
            assert not page_errors, page_errors
            assert not console_errors, console_errors

            assert page.locator('body[data-cew-panel-content="hva-refined-v1"]').count() == 1
            assert page.locator("header h1").inner_text().strip() == "CEW — Analisi documentale"
            assert page.locator("header small").inner_text().strip() == "Documento → elementi grafici → gruppi candidati → verifica umana."

            provider = page.locator("#provider")
            provider_text = provider.inner_text().strip()
            assert provider_text.startswith("Analisi grafica:"), provider_text
            assert "DINOv3" not in provider_text
            assert "IMPLEMENTED_NOT_PROVISIONED" not in provider_text
            assert "DINOv3" in (provider.get_attribute("title") or "")

            assert page.locator("#source option").first.inner_text().strip() == "Apri fonte governata…"
            assert page.locator("#preview").inner_text().strip() == "Analizza PDF"
            intake = page.locator("#intake-message").inner_text().strip()
            assert intake.startswith("Apri una fonte governata oppure scegli un PDF locale"), intake
            assert "training" not in intake.lower(), intake

            placeholder = page.locator("#viewer-placeholder").inner_text().strip()
            assert placeholder.startswith("Apri una tavola per iniziare."), placeholder
            assert "fonte di riferimento" in placeholder

            assert page.locator("#cew-editor-label").inner_text().strip() == "Nessuna fonte aperta"
            assert page.locator("#cew-editor-evidence").inner_text().strip() == "Nessuna fonte"
            assert page.locator("#cew-editor-authority").inner_text().strip() == "Sola lettura"
            assert page.locator("#cew-viewport-note").inner_text().strip() == "Pan attivo · trascina per spostare · rotella per zoom"

            pan = page.locator("#preview-pan")
            assert pan.count() == 1
            assert pan.get_attribute("aria-pressed") == "true"
            assert "Pan attivo" in (pan.get_attribute("aria-label") or "")
            page.evaluate(
                """
                () => {
                  const viewer=document.getElementById('viewer');
                  const img=document.getElementById('page');
                  img.hidden=false;
                  viewer.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:77,button:0,clientX:300,clientY:300}));
                  viewer.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,pointerId:77,button:0,clientX:360,clientY:345}));
                  viewer.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:77,button:0,clientX:360,clientY:345}));
                }
                """
            )
            translated = page.locator(".pagewrap").evaluate("el => el.style.translate")
            assert translated and translated != "0px 0px", translated

            assert page.locator("#cew-inspector-head strong").inner_text().strip().upper() == "DETTAGLI"
            assert page.locator("#title").inner_text().strip() == "Nessun elemento selezionato"
            inspector_empty = page.locator("#cew-inspector-meta .cew-empty").inner_text().strip()
            assert "seleziona un elemento" in inspector_empty.lower(), inspector_empty

            page.evaluate(
                """
                () => {
                  document.getElementById('title').textContent='Famiglia grafica · 1 occorrenze';
                  document.getElementById('detail').innerHTML='<span class="pill">LINEAR_STROKE_GROUP</span><span class="pill">SQUAREISH</span><span class="pill">LARGE</span><br>Significato automatico: <b>nessuno</b>';
                  document.getElementById('cew-inspector-meta').innerHTML='<h4>Cluster selezionato</h4><dl class="cew-kv"><dt>ID</dt><dd>GC-test</dd><dt>Famiglia</dt><dd>LINEAR_STROKE_GROUP</dd><dt>Occorrenze</dt><dd>1</dd><dt>Pagina</dt><dd>1</dd><dt>BBox</dt><dd>0.0089 · 0.0000 · 0.9911 · 1.0000</dd><dt>Significato</dt><dd>NON ASSEGNATO</dd><dt>Validazione</dt><dd>UMANA RICHIESTA</dd></dl>';
                  document.getElementById('cew-provenance-meta').innerHTML='<h4>Provenienza e autorità</h4><dl class="cew-kv"><dt>Sessione</dt><dd>DISC-test</dd></dl>';
                }
                """
            )
            page.wait_for_timeout(100)
            assert page.locator("#title").inner_text().strip() == "Gruppo grafico · 1 occorrenza"
            assert page.locator("#detail .pill").nth(0).inner_text().strip() == "Gruppo lineare"
            assert page.locator("#detail .pill").nth(1).inner_text().strip() == "Forma compatta"
            assert page.locator("#detail .pill").nth(2).inner_text().strip() == "Area grande"
            assert page.locator("#cew-inspector-meta h4").inner_text().strip() == "Gruppo selezionato"
            assert page.locator("#cew-inspector-meta").get_by_text("BBox", exact=True).count() == 0
            assert page.locator("#cew-provenance-meta").get_by_text("Riquadro normalizzato", exact=True).count() == 1

            status = page.locator("#cew-statusbar")
            status_text = status.inner_text().strip()
            for expected in ("Pagina", "Zoom", "Elementi", "Gruppi", "Fonte"):
                assert expected in status_text, status_text
            for forbidden in ("Renderer", "Training", "Rot "):
                assert forbidden not in status_text, status_text
            diagnostic_title = status.get_attribute("title") or ""
            assert "Renderer" in diagnostic_title and "Training" in diagnostic_title, diagnostic_title

            assert page.locator('#cew-activity-rail button[data-nav="primitives"]').get_attribute("aria-label") == "Elementi grafici"
            assert page.locator('#cew-activity-rail button[data-nav="clusters"]').get_attribute("aria-label") == "Gruppi candidati"

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

    print("CEW_MATURE_PANEL_CONTENT_HVA_REFINED_V1_PASS")
    print("operator_copy=ITALIAN_TASK_FIRST technical_diagnostics=SECONDARY_HOVER")
    print("pan=EXPLICIT_FREE_CAMERA_DRAG cluster_details=HUMANIZED bbox=PROVENANCE")
    print("empty_state=CONTEXTUAL statusbar=OPERATIVE_ONLY topology=UNCHANGED")


if __name__ == "__main__":
    main()
