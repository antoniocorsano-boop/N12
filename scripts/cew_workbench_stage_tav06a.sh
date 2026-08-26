#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_COMMIT="78c20a52db4f391ce0d13b9705b9f04737e218c9"
ARCHIVE_PATH="archive/documentazione_originaria/tavola 6.pdf"
ARCHIVE_BLOB_SHA="c3048472adfdaa5b1e902f84c20ccfb20d679b1f"
CANONICAL_COMMIT="b4356bc78807257901a0b97892a63d9f4c9744c9"
EXPECTED_WIDTH=4299
EXPECTED_HEIGHT=25376
DPI=300
WORKBENCH_DIR="${1:-ui/workbench}"
RUNTIME_DIR="${WORKBENCH_DIR}/public/runtime"
PDF="/tmp/cew-ux1-tav06a.pdf"
IMAGE="${RUNTIME_DIR}/tav06a-p001.jpg"
MANIFEST="${RUNTIME_DIR}/tav06a-p001.manifest.json"

mkdir -p "$RUNTIME_DIR"
rm -f "$IMAGE" "$MANIFEST" "$PDF"

git fetch --no-tags --depth=1 origin "$ARCHIVE_COMMIT"
actual_blob="$(git ls-tree "$ARCHIVE_COMMIT" "$ARCHIVE_PATH" | awk '{print $3}')"
if [[ "$actual_blob" != "$ARCHIVE_BLOB_SHA" ]]; then
  echo "Archive blob drift: expected $ARCHIVE_BLOB_SHA, got $actual_blob" >&2
  exit 21
fi

git show "${ARCHIVE_COMMIT}:${ARCHIVE_PATH}" > "$PDF"
pdftoppm -jpeg -jpegopt quality=92 -r "$DPI" -singlefile "$PDF" "${RUNTIME_DIR}/tav06a-p001" >/dev/null

python - "$IMAGE" "$MANIFEST" <<'PY'
import hashlib
import json
import struct
import sys
from pathlib import Path

image = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
expected_width = 4299
expected_height = 25376

raw = image.read_bytes()
if raw[:2] != b'\xff\xd8':
    raise SystemExit("staged render is not JPEG")

i = 2
width = height = None
sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
while i < len(raw):
    if raw[i] != 0xFF:
        i += 1
        continue
    while i < len(raw) and raw[i] == 0xFF:
        i += 1
    if i >= len(raw):
        break
    marker = raw[i]
    i += 1
    if marker in {0xD8, 0xD9}:
        continue
    if i + 2 > len(raw):
        break
    length = struct.unpack(">H", raw[i:i + 2])[0]
    if marker in sof:
        if i + 7 > len(raw):
            break
        height, width = struct.unpack(">HH", raw[i + 3:i + 7])
        break
    i += length

if (width, height) != (expected_width, expected_height):
    raise SystemExit(f"render dimension drift: {(width, height)} != {(expected_width, expected_height)}")

manifest = {
    "schema_version": "1.0",
    "stage_status": "READY",
    "canonical_commit": "b4356bc78807257901a0b97892a63d9f4c9744c9",
    "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "archive_path": "archive/documentazione_originaria/tavola 6.pdf",
    "archive_blob_sha": "c3048472adfdaa5b1e902f84c20ccfb20d679b1f",
    "render_dpi": 300,
    "render_width_px": width,
    "render_height_px": height,
    "render_file_sha256": hashlib.sha256(raw).hexdigest(),
    "image_url": "./runtime/tav06a-p001.jpg",
    "authority": "DERIVATIVE_REVIEW_CONTEXT_ONLY"
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
PY
