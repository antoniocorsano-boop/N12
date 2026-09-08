#!/usr/bin/env python3
"""Materialize the governed G4 OAR interaction raster during the Render build.

The deployed Free web worker must only serve this already-verified asset. It must
not allocate the full 7016x12530 RGB pixmap on the first human request.
"""
from __future__ import annotations

import cew_oar_g4_source_resolver as resolver


def main() -> None:
    target = resolver.materialize_build_raster()
    resolver.verify_registered_raster(target)
    print("CEW_OAR_G4_BUILD_RASTER = READY")
    print(f"path={target}")
    print(f"derived_asset_id={resolver.REGISTERED_DERIVED_ASSET_ID}")
    print(f"sha256={resolver.REGISTERED_RENDER_SHA256}")
    print(f"dimensions={resolver.REGISTERED_RENDER_WIDTH_PX}x{resolver.REGISTERED_RENDER_HEIGHT_PX}")
    print(f"dpi={resolver.RUNTIME_DPI}")
    print("runtime_first_request_render=false")
    print("canonical_write_authorized=false")


if __name__ == "__main__":
    main()
