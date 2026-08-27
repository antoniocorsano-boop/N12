#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_runtime_audit_store as audit_store

FUNCTION = ROOT / "netlify/functions/cew-audit.mjs"
MIGRATION = ROOT / "netlify/database/migrations/001_cew-audit/migration.sql"


class AuditMock(BaseHTTPRequestHandler):
    seen: set[str] = set()
    secret = "ci-netlify-audit-secret"

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        if self.headers.get("Authorization") != f"Bearer {self.secret}":
            self.send_response(401)
            self.end_headers()
            return
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        payload = json.loads(raw.decode("utf-8"))
        decision_id = payload["decision_id"]
        if payload["authority"] != "RUNTIME_AUDIT_ONLY" or payload["canonical_write"] is not False:
            self.send_response(422)
            self.end_headers()
            return
        if decision_id in self.seen:
            self.send_response(409)
            self.end_headers()
            self.wfile.write(b'{"reason":"DUPLICATE_DECISION_ID"}')
            return
        self.seen.add(decision_id)
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"state":"AUDIT_STORED"}')


def assert_static_contracts():
    fn = FUNCTION.read_text(encoding="utf-8")
    mig = MIGRATION.read_text(encoding="utf-8")
    required_fn = [
        '@netlify/database',
        'CEW_AUDIT_SHARED_SECRET',
        'RUNTIME_AUDIT_ONLY',
        'RECEIPT_DIGEST_MISMATCH',
        'DUPLICATE_DECISION_ID',
        'canonical_write',
    ]
    for marker in required_fn:
        if marker not in fn:
            raise SystemExit(f"FAIL: missing Netlify function marker {marker}")
    required_mig = [
        "PRIMARY KEY",
        "canonical_write = false",
        "BEFORE UPDATE OR DELETE",
        "BEFORE TRUNCATE",
        "append-only",
    ]
    lower = mig.lower()
    for marker in required_mig:
        if marker.lower() not in lower:
            raise SystemExit(f"FAIL: missing append-only migration marker {marker}")


def main():
    assert_static_contracts()
    server = ThreadingHTTPServer(("127.0.0.1", 0), AuditMock)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_address[1]}/api/cew-audit"

    previous = {k: os.environ.get(k) for k in ("CEW_AUDIT_HTTPS_URL", "CEW_AUDIT_SHARED_SECRET", "VERCEL")}
    os.environ["CEW_AUDIT_HTTPS_URL"] = endpoint
    os.environ["CEW_AUDIT_SHARED_SECRET"] = AuditMock.secret
    os.environ["VERCEL"] = "1"
    try:
        if audit_store.backend_status() != "NETLIFY_AUDIT_HTTPS":
            raise SystemExit("FAIL: Netlify audit backend not selected")
        receipt = {
            "schema_version": "1.0",
            "decision_id": "HUMAN-ERW-N12-001-CI-NETLIFY",
            "task_id": "ERW-N12-001",
            "residual_id": "M1E-B06-R08",
            "review_mode": "HUMAN_REVIEW",
            "reviewer": "CI",
            "timestamp": "2026-08-27T00:00:00Z",
            "outcome": "CONFIRMED",
            "human_observation": "2 Φ12 superiori + 2 Φ12 inferiori",
            "evidence_regions": ["CEW-N12-REG-G01-R06"],
            "source_versions": ["CEW-N12-SRC-TAV05A-V17DEC414"],
            "direct_primary_evidence_observed": True,
            "requested_epistemic_state": "DOC",
            "target_id": "CEW-TARGET-REINFORCEMENT-OBSERVATION",
            "reopen_approval_id": "",
            "authority_acknowledgement": "I reviewed the cited immutable primary-source evidence and understand this receipt is not itself a canonical write.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            stored = audit_store.persist_runtime_receipt(receipt, Path(tmp))
            if stored.get("audit_backend") != "NETLIFY_AUDIT_HTTPS":
                raise SystemExit("FAIL: receipt did not use Netlify audit backend")
            if stored.get("canonical_write") is not False:
                raise SystemExit("FAIL: audit bridge changed canonical write authority")
            try:
                audit_store.persist_runtime_receipt(receipt, Path(tmp))
            except ValueError as exc:
                if "duplicate decision_id" not in str(exc):
                    raise
            else:
                raise SystemExit("FAIL: duplicate receipt was not rejected")
        import app
        health = app.healthz()
        if health.get("audit_backend") != "NETLIFY_AUDIT_HTTPS":
            raise SystemExit("FAIL: web pilot health does not expose Netlify audit backend")
        if health.get("production_receipt_submit_ready") is not True:
            raise SystemExit("FAIL: configured Netlify audit backend is not production-ready")
        if health.get("canonical_write_authorized") is not False:
            raise SystemExit("FAIL: web health altered canonical authority")
    finally:
        server.shutdown()
        server.server_close()
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    print("CEW_NETLIFY_AUDIT_BRIDGE_PASS")
    print("AUDIT_BACKEND=NETLIFY_AUDIT_HTTPS")
    print("APPEND_ONLY_DUPLICATE_REJECTION=PASS")
    print("PRODUCTION_RECEIPT_SUBMIT_READY=PASS")
    print("CANONICAL_WRITE=FORBIDDEN")


if __name__ == "__main__":
    main()
