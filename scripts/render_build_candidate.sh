#!/usr/bin/env bash
set -euo pipefail

if [[ ! "${RENDER_GIT_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "CEW_RENDER_BUILD_FAIL: RENDER_GIT_COMMIT must be a full immutable SHA" >&2
  exit 1
fi

printf 'CEW_RENDER_BUILD_CANDIDATE_SHA = %s\n' "$RENDER_GIT_COMMIT"

# Render can provide a valid Git checkout without preserving a named `origin`
# remote. Managed F3 must still materialize immutable source files from their
# frozen historical commit. Recreate only the canonical public N12 origin when
# it is absent; reject any unexpected origin rather than fetching evidence from
# an ungoverned repository.
CANONICAL_REPO_URL="https://github.com/antoniocorsano-boop/N12.git"
ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "$ORIGIN_URL" ]]; then
  git remote add origin "$CANONICAL_REPO_URL"
  echo "CEW_RENDER_GIT_ORIGIN = ADDED_CANONICAL_PUBLIC_N12"
else
  case "$ORIGIN_URL" in
    https://github.com/antoniocorsano-boop/N12|https://github.com/antoniocorsano-boop/N12.git|git@github.com:antoniocorsano-boop/N12.git)
      echo "CEW_RENDER_GIT_ORIGIN = VERIFIED_CANONICAL_N12"
      ;;
    *)
      echo "CEW_RENDER_BUILD_FAIL: unexpected git origin $ORIGIN_URL" >&2
      exit 1
      ;;
  esac
fi

pip install -r requirements.txt
# Materialize the exact governed 300-DPI G4 interaction asset while the Render
# build pipeline has its separate high-memory compute. The Free web worker then
# serves the verified file and never cold-renders 7016x12530 on a human request.
python scripts/build_cew_oar_g4_runtime_asset.py
# Build the additive assisted-localization POC from the same governed raster:
# self-hosted OpenSeadragon/Annotorious assets, a libvips DZI pyramid and
# build-only OpenCV snap candidates. None of these derived interaction aids
# carries evidence, classification or engineering authority.
python scripts/build_cew_oar_g4_assisted_assets.py
python scripts/build_cew_runtime_render_cache.py
python scripts/build_cew_managed_f3_assets.py
python scripts/build_cew_document_geometry_artifacts.py
python scripts/build_cew_evidence_region_content_diagnostic.py
python scripts/build_cew_evidence_region_mapping_root_cause.py
python scripts/build_cew_raster_geometry_candidates.py
python scripts/build_cew_raster_geometry_quality.py
python scripts/build_cew_raster_geometry_consolidation.py
python scripts/build_cew_raster_geometry_topology.py
python scripts/build_cew_raster_support_continuity.py
python scripts/build_cew_raster_support_negative_controls.py
python scripts/build_cew_raster_bridge_review_layer.py
python scripts/build_cew_raster_gap_review_view.py
CEW_REVIEW_HEAD_SHA="$RENDER_GIT_COMMIT" python scripts/build_cew_human_gap_review_receipts.py
CEW_REVIEW_HEAD_SHA="$RENDER_GIT_COMMIT" python scripts/validate_cew_human_gap_review_receipts.py
CEW_RUNTIME_REVISION="$RENDER_GIT_COMMIT" python scripts/validate_cew_b18_hva_hardening.py

python - <<'PY'
import json
import os
from pathlib import Path

manifest_path = Path('artifacts/cew_r2hr_review/manifest.json')
if not manifest_path.is_file():
    raise SystemExit('CEW_RENDER_BUILD_FAIL: R2HR manifest missing after build')
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
expected = os.environ['RENDER_GIT_COMMIT'].lower()
actual = str(manifest.get('candidate_head_sha', '')).lower()
if actual != expected:
    raise SystemExit(f'CEW_RENDER_BUILD_FAIL: R2HR candidate mismatch {actual} != {expected}')
regions = manifest.get('regions') or []
if len(regions) != 4 or manifest.get('gap_hypothesis_total') != 10:
    raise SystemExit('CEW_RENDER_BUILD_FAIL: R2HR coverage mismatch')

assisted_manifest_path = Path('artifacts/cew_oar_g4_assisted/manifest.json')
if not assisted_manifest_path.is_file():
    raise SystemExit('CEW_RENDER_BUILD_FAIL: assisted OAR manifest missing after build')
assisted = json.loads(assisted_manifest_path.read_text(encoding='utf-8'))
if assisted.get('build_revision', '').lower() != expected:
    raise SystemExit('CEW_RENDER_BUILD_FAIL: assisted OAR revision mismatch')
if assisted.get('authority', {}).get('canonical_write_authorized') is not False:
    raise SystemExit('CEW_RENDER_BUILD_FAIL: assisted OAR authority drift')
if assisted.get('deepzoom', {}).get('tile_count', 0) <= 0 or assisted.get('snap', {}).get('candidate_count', 0) <= 0:
    raise SystemExit('CEW_RENDER_BUILD_FAIL: assisted OAR assets incomplete')

print('CEW_RENDER_R2HR_RUNTIME_ARTIFACT = READY')
print('CEW_RENDER_R2HR_REGION_COVERAGE = 4/4')
print('CEW_RENDER_R2HR_GAP_TOTAL = 10')
print('CEW_RENDER_OAR_ASSISTED = READY')
print('CEW_RENDER_BUILD = PASS')
PY
