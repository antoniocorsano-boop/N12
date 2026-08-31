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

# Human-first, enterprise frame/review, and governed context continuity are
# managed-runtime requirements, not browser preferences. A deploy must fail
# before artifact generation if the professional interaction contract regresses.
python scripts/validate_cew_oa_human_first_ux.py
python scripts/validate_cew_ews1_application_frame.py
python scripts/validate_cew_ews4_oa_result_review.py
python scripts/validate_cew_enterprise_context_continuity.py

python scripts/build_cew_runtime_render_cache.py
python scripts/build_cew_managed_f3_assets.py

# The F3 standalone viewer keeps DZI paths relative to its own source-viewer
# root (tiles/<source>.dzi). The Professional Workbench serves assets from the
# parent managed asset root. Provide a runtime-only compatibility alias so the
# existing F3 relative reference resolves without duplicating or re-authoring
# any evidence asset. The symlink target stays inside the governed asset root.
MANAGED_F3_ROOT=".cew_professional_workbench_assets"
if [[ ! -d "$MANAGED_F3_ROOT/source-viewer/tiles" ]]; then
  echo "CEW_RENDER_BUILD_FAIL: managed F3 source-viewer tiles missing" >&2
  exit 1
fi
rm -f "$MANAGED_F3_ROOT/tiles"
ln -s "source-viewer/tiles" "$MANAGED_F3_ROOT/tiles"
if [[ ! -f "$MANAGED_F3_ROOT/tiles/TAV-05S.dzi" ]]; then
  echo "CEW_RENDER_BUILD_FAIL: Workbench TAV-05S DZI alias unresolved" >&2
  exit 1
fi
echo "CEW_RENDER_WORKBENCH_F3_ASSET_ALIAS = READY"

python scripts/build_cew_document_geometry_artifacts.py
# PWB-005 legacy diagnostics are explicitly frozen to the four historical
# EvidenceRegion cases. OA extensions are governed separately and must not be
# ingested as additional PWB-005 cases during managed-runtime builds.
python scripts/run_cew_pwb005_r1_frozen_scope.py
python scripts/run_cew_pwb005_r1a_frozen_scope.py
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
print('CEW_RENDER_R2HR_RUNTIME_ARTIFACT = READY')
print('CEW_RENDER_R2HR_REGION_COVERAGE = 4/4')
print('CEW_RENDER_R2HR_GAP_TOTAL = 10')
print('CEW_RENDER_OA_HUMAN_FIRST_UX = READY')
print('CEW_RENDER_EWS1_APPLICATION_FRAME = READY')
print('CEW_RENDER_EWS4_OA_RESULT_REVIEW = READY')
print('CEW_RENDER_ENTERPRISE_CONTEXT_CONTINUITY = READY')
print('CEW_RENDER_BUILD = PASS')
PY
