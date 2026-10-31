#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_f7_native_review_service as f7
from build_cew_mobile_review_pack import build_html
from cew_mobile_review import validate_manifest


class MobileReviewHandler(f7.Handler):
    mobile_manifest: dict | None = None

    def do_GET(self):
        if urlparse(self.path).path == "/review/mobile":
            if self.mobile_manifest is None:
                self.send_json({"error": "mobile_review_manifest_not_configured"}, 404)
                return
            self.send_html(build_html(self.mobile_manifest))
            return
        super().do_GET()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--receipt-store", type=Path, default=f7.DEFAULT_STORE)
    ap.add_argument("--mobile-review-manifest", type=Path, required=True)
    args = ap.parse_args()

    contract = f7.load_json(f7.SERVICE_CONTRACT)
    if contract.get("product_surface") != "PROJECT_CONTROL_ROOM":
        raise SystemExit("FAIL: native review service contract drift")
    manifest = f7.load_json(args.mobile_review_manifest)
    validate_manifest(manifest)

    MobileReviewHandler.mobile_manifest = manifest
    MobileReviewHandler.receipt_store = f7.ensure_runtime_store(args.receipt_store)
    server = ThreadingHTTPServer((args.host, args.port), MobileReviewHandler)
    print(f"CEW MOBILE REVIEW: http://{args.host}:{args.port}/review/mobile")
    print("F7_RECEIPT_SUBMIT=NATIVE")
    print("CANONICAL_WRITE=FORBIDDEN")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
