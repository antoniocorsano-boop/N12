#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

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
    stored: dict[str, dict] = {}
    secret = "ci-netlify-audit-secret"

    def log_message(self, fmt, *args):
        pass

    def _authorized(self) -> bool:
        if self.headers.get("Authorization") != f"Bearer {self.secret}":
            self.send_response(401)
            self.end_headers()
            return False
        return True

    def do_POST(self):
        if not self._authorized():
            return
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        payload = json.loads(raw.decode("utf-8"))
        decision_id = payload["decision_id"]
        if payload["authority"] != "RUNTIME_AUDIT_ONLY" or payload["canonical_write"] is not False:
            self.send_response(422)
            self.end_headers()
            return
        if decision_id in self.stored:
            self.send_response(409)
            self.end_headers()
            self.wfile.write(b'{"reason":"DUPLICATE_DECISION_ID"}')
            return
        self.stored[decision_id] = payload
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"state":"AUDIT_STORED"}')

    def do_GET(self):
        if not self._authorized():
            return
        query = parse_qs(urlsplit(self.path).query)
        receipt_type = query.get("receipt_type", [""])[0]
        limit = int(query.get("limit", ["501"])[0])
        receipts = [
            row["receipt_json"]
            for row in self.stored.values()
            if row.get("receipt_json", {}).get("receipt_type") == receipt_type
        ][:limit]
        body = json.dumps(
            {
                "state": "AUDIT_READ_OK",
                "receipts": receipts,
                "authority": "RUNTIME_AUDIT_READ_ONLY",
                "canonical_write": False,
                "engineering_authority_effect": "NONE",
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


def assert_static_contracts():
    fn = FUNCTION.read_text(encoding="utf-8")
    mig = MIGRATION.read_text(encoding="utf-8")
    required_fn = [
        '@netlify/database',
        'CEW_AUDIT_SHARED_SECRET',
        'RUNTIME_AUDIT_ONLY',
        'RUNTIME_AUDIT_READ_ONLY',
        'RECEIPT_DIGEST_MISMATCH',
        'DUPLICATE_DECISION_ID',
        'canonical_write',
        'req.method === "GET"',
        "SELECT receipt_json",
        "receipt_json->>'receipt_type'",
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
    AuditMock.stored = {}
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
            "receipt_type": "CEW_HUMAN_DECISION_RECEIPT_v1",
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
            store = Path(tmp)
            stored = audit_store.persist_runtime_receipt(receipt, store)
            if stored.get("audit_backend") != "NETLIFY_AUDIT_HTTPS":
                raise SystemExit("FAIL: receipt did not use Netlify audit backend")
            if stored.get("canonical_write") is not False:
                raise SystemExit("FAIL: audit bridge changed canonical write authority")
            loaded = audit_store.load_runtime_receipts(receipt["receipt_type"], store)
            if loaded.get("audit_backend") != "NETLIFY_AUDIT_HTTPS":
                raise SystemExit("FAIL: governed read did not use Netlify backend")
            if loaded.get("receipt_count") != 1 or loaded["receipts"][0] != receipt:
                raise SystemExit("FAIL: governed Netlify read-back mismatch")
            if loaded.get("authority") != "RUNTIME_AUDIT_READ_ONLY":
                raise SystemExit("FAIL: governed read authority drift")
            if loaded.get("canonical_write") is not False:
                raise SystemExit("FAIL: governed read changed canonical authority")
            try:
                audit_store.persist_runtime_receipt(receipt, store)
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
    print("GOVERNED_RECEIPT_READ_BACK=PASS")
    print("PRODUCTION_RECEIPT_SUBMIT_READY=PASS")
    print("CANONICAL_WRITE=FORBIDDEN")


if __name__ == "__main__":
    main()
