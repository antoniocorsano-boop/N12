#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from urllib.parse import quote
from urllib.request import Request, urlopen

import fitz

ARCHIVE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"
REMOTE_PATH = "archive/documentazione_originaria/tavola 5.pdf"
EXPECTED_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
URL = "https://raw.githubusercontent.com/antoniocorsano-boop/N12/" + ARCHIVE_COMMIT + "/" + "/".join(quote(p) for p in REMOTE_PATH.split("/"))


def main() -> None:
    req = Request(URL, headers={"User-Agent": "CEW/1 immutable-source-measurement"})
    with urlopen(req, timeout=30) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"FAIL: TAV05S SHA mismatch {digest}")
    with fitz.open(stream=payload, filetype="pdf") as doc:
        if doc.page_count != 1:
            raise SystemExit(f"FAIL: expected single page, got {doc.page_count}")
        page = doc.load_page(0)
        rect = page.rect
        rotation = page.rotation
        pix = page.get_pixmap(dpi=300, alpha=False)
        print("TAV05S_IMMUTABLE_SOURCE_VERIFIED")
        print(f"TAV05S_PAGE_COUNT={doc.page_count}")
        print(f"TAV05S_PAGE_WIDTH_PT={rect.width:.6f}")
        print(f"TAV05S_PAGE_HEIGHT_PT={rect.height:.6f}")
        print(f"TAV05S_PAGE_ROTATION={rotation}")
        print(f"TAV05S_RENDER_300DPI={pix.width}x{pix.height}")
        print(f"TAV05S_SHA256={digest}")


if __name__ == "__main__":
    main()
