#!/usr/bin/env python3
"""Browser contract for CEW preview recovery across transient runtime restarts.

The test does not exercise the PDF worker. It intercepts the mounted runtime API
and proves that the real MATURE_V1 browser surface survives:

1. a transient HTTP 502 followed by loss of the in-memory preview job; and
2. loss of the in-memory session after a job has completed.

In both cases the browser must reconstruct once from the still-selected local PDF
instead of surfacing a raw HTTP 502 or requiring the user to choose the file again.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from playwright.sync_api import Route, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_app(url: str, proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            raise AssertionError(f"CEW_RECOVERY_BROWSER_APP_EXITED\n{output}")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback only
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.15)
    raise AssertionError("CEW_RECOVERY_BROWSER_APP_START_TIMEOUT")


def session_payload(session_id: str) -> dict:
    return {
        "state": "DOCUMENT_DISCOVERY_READY",
        "session_id": session_id,
        "project_id": "N12",
        "source_id": None,
        "source_version_id": "PREVIEW-test",
        "source_sha256": "0" * 64,
        "source_registration_state": "UNREGISTERED_PREVIEW",
        "teaching_enabled": False,
        "teaching_blocker": "IMMUTABLE_SOURCE_AND_READY_PAGE_REGISTRATION_REQUIRED",
        "page_count": 0,
        "pages": [],
        "primitive_candidate_count": 0,
        "graphic_cluster_count": 0,
        "clusters": [],
        "library_state": "LIBRARY_NOT_CONFIGURED",
        "semantic_labels_assigned_automatically": False,
        "provider_states": {
            "structured_graphic": {"state": "READY"},
            "visual_foundation": {"state": "IMPLEMENTED_NOT_PROVISIONED"},
        },
        "concepts": [],
        "preview_budget": {"truncated": False},
        "authority": {"canonical_write_authorized": False},
    }


def fulfill_json(route: Route, status: int, payload: dict) -> None:
    route.fulfill(status=status, content_type="application/json", body=json.dumps(payload))


def run_scenario(browser, base: str, loss_at: str) -> None:
    context = browser.new_context(viewport={"width": 1360, "height": 820})
    page = context.new_page()
    page_errors: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    counters = {"enqueue": 0, "job1_poll": 0, "session1": 0}

    def enqueue(route: Route) -> None:
        counters["enqueue"] += 1
        n = counters["enqueue"]
        fulfill_json(
            route,
            202,
            {
                "state": "QUEUED",
                "job_id": f"DPJ-RECOVERY-{n}",
                "project_id": "N12",
                "session_id": None,
                "preview_fallback_used": False,
                "minimum_page_coverage_ratio": None,
            },
        )

    def poll(route: Route) -> None:
        url = route.request.url
        if "DPJ-RECOVERY-1" in url:
            counters["job1_poll"] += 1
            if loss_at == "job":
                if counters["job1_poll"] == 1:
                    fulfill_json(route, 502, {"reason": "SIMULATED_RUNTIME_RESTART"})
                    return
                fulfill_json(
                    route,
                    404,
                    {
                        "state": "DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND",
                        "reason": "DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND",
                    },
                )
                return
            fulfill_json(
                route,
                200,
                {
                    "state": "READY",
                    "job_id": "DPJ-RECOVERY-1",
                    "session_id": "DISC-LOST",
                    "preview_fallback_used": False,
                    "minimum_page_coverage_ratio": None,
                },
            )
            return
        fulfill_json(
            route,
            200,
            {
                "state": "READY",
                "job_id": "DPJ-RECOVERY-2",
                "session_id": "DISC-RECOVERED",
                "preview_fallback_used": False,
                "minimum_page_coverage_ratio": None,
            },
        )

    def sessions(route: Route) -> None:
        url = route.request.url
        if url.endswith("/DISC-LOST"):
            counters["session1"] += 1
            fulfill_json(
                route,
                404,
                {
                    "state": "DOCUMENT_DISCOVERY_SESSION_NOT_FOUND",
                    "reason": "DOCUMENT_DISCOVERY_SESSION_NOT_FOUND",
                },
            )
            return
        if url.endswith("/DISC-RECOVERED"):
            fulfill_json(route, 200, session_payload("DISC-RECOVERED"))
            return
        route.continue_()

    page.route("**/api/workbench/document-discovery/analyze-preview-async?*", enqueue)
    page.route("**/api/workbench/document-discovery/preview-job/**", poll)
    page.route("**/api/workbench/document-discovery/session/**", sessions)

    response = page.goto(f"{base}/workbench/document-discovery", wait_until="networkidle")
    assert response is not None and response.status == 200
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert headers.get("x-cew-panel-quality") == "MATURE_V1"
    assert headers.get("x-cew-preview-runtime-recovery") == "BROWSER_RECONSTRUCT_V1"
    assert page.locator('body[data-cew-preview-runtime-recovery="enabled"]').count() == 1

    page.locator("#project").fill("N12")
    page.locator("#file").set_input_files(
        files=[{"name": "tavola-test.pdf", "mimeType": "application/pdf", "buffer": PDF_BYTES}]
    )
    page.locator("#preview").click()

    try:
        page.wait_for_function("() => document.querySelector('#intake-message')?.textContent.includes('Analisi completata')", timeout=30000)
    except Exception:
        message = page.locator("#intake-message").inner_text()
        file_count = page.locator("#file").evaluate("el => el.files.length")
        print(
            "CEW_PREVIEW_RUNTIME_RECOVERY_DIAGNOSTIC "
            f"loss_at={loss_at} counters={counters} message={message!r} "
            f"file_count={file_count} page_errors={page_errors!r} console_errors={console_errors!r}",
            flush=True,
        )
        raise
    assert counters["enqueue"] == 2, counters
    if loss_at == "job":
        assert counters["job1_poll"] >= 2, counters
    else:
        assert counters["session1"] == 1, counters
    message = page.locator("#intake-message").inner_text()
    assert "HTTP 502" not in message, message
    assert "Errore CEW" not in message, message
    assert page.locator("#file").evaluate("el => el.files.length") == 1
    assert not page_errors, page_errors
    assert not console_errors, console_errors
    context.close()


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
    try:
        wait_for_app(f"{base}/workbench/document-discovery", proc)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            run_scenario(browser, base, "job")
            run_scenario(browser, base, "session")
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    print("CEW_PREVIEW_RUNTIME_RECOVERY_BROWSER_PASS")
    print("transient_502=RETRIED lost_job=AUTO_REBUILT lost_session=AUTO_REBUILT")
    print("browser_pdf_selection=PRESERVED rebuild_budget=ONE no_raw_502_user_error=PASS")


if __name__ == "__main__":
    main()
