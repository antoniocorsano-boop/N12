from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
import math
from pathlib import Path
import re
from typing import Any


_N_LABEL = re.compile(r"^N\d{3}$")
_G_METRIC = re.compile(r"^G\d{2}(?:\b|\s)")


def _closed_authority() -> dict[str, Any]:
    return {
        "engineering_authority_effect": "NONE",
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "m0g_authorized": False,
        "original_drafter_grammar_promotion_authorized": False,
        "human_review_required": True,
    }


def _token_class(text: str) -> str:
    if _N_LABEL.fullmatch(text):
        return "HISTORICAL_N_LABEL_TOKEN"
    if _G_METRIC.match(text):
        return "HISTORICAL_METRIC_TOKEN"
    return "HISTORICAL_TEXT_TOKEN"


def _grammar_origin(layer: str) -> str:
    if layer.startswith("S-"):
        return "HISTORICAL_CEW_DERIVED_ANNOTATION"
    return "UNDETERMINED_SOURCE_GRAPHICS"


def _normalize_token(row: dict[str, Any]) -> dict[str, Any]:
    stable_id = str(row.get("stable_id") or "").strip()
    text = str(row.get("text") or "").strip()
    layer = str(row.get("layer") or "").strip()
    insert = row.get("insert")
    if not stable_id or not layer or not isinstance(insert, list) or len(insert) < 2:
        raise ValueError("DXF_DOCUMENTARY_TOKEN_BINDING_INVALID")
    x, y = float(insert[0]), float(insert[1])
    origin = _grammar_origin(layer)
    return {
        "stable_id": stable_id,
        "text": text,
        "layer": layer,
        "insert": [x, y, float(insert[2]) if len(insert) > 2 else 0.0],
        "rotation": float(row.get("rotation") or 0.0),
        "height": float(row.get("height") or 0.0),
        "token_class": _token_class(text),
        "grammar_origin": origin,
        "eligible_to_teach_original_drafter_grammar": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }


def _cross_layer_n_patterns(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for token in tokens:
        if token["token_class"] == "HISTORICAL_N_LABEL_TOKEN":
            grouped[token["text"]].append(token)

    patterns: list[dict[str, Any]] = []
    for label in sorted(grouped):
        rows = grouped[label]
        documented = sorted(
            (row for row in rows if row["layer"] == "S-PIL-ID"),
            key=lambda row: row["stable_id"],
        )
        inferred = sorted(
            (row for row in rows if row["layer"] == "S-ID-CAND-INF"),
            key=lambda row: row["stable_id"],
        )
        if not documented or not inferred:
            continue
        for source in documented:
            target = min(
                inferred,
                key=lambda row: (
                    math.dist(source["insert"][:2], row["insert"][:2]),
                    row["stable_id"],
                ),
            )
            delta_x = target["insert"][0] - source["insert"][0]
            delta_y = target["insert"][1] - source["insert"][1]
            patterns.append(
                {
                    "token": label,
                    "source_stable_id": source["stable_id"],
                    "target_stable_id": target["stable_id"],
                    "source_layer": source["layer"],
                    "target_layer": target["layer"],
                    "delta_x": round(delta_x, 12),
                    "delta_y": round(delta_y, 12),
                    "distance": round(math.hypot(delta_x, delta_y), 12),
                    "interpretation": "HISTORICAL_RECONSTRUCTION_DUPLICATION_PATTERN",
                    "grammar_origin": "HISTORICAL_CEW_DERIVED_ANNOTATION",
                    "eligible_to_teach_original_drafter_grammar": False,
                    "structural_identity_authorized": False,
                    "canonical_write_authorized": False,
                }
            )
    patterns.sort(key=lambda row: (row["token"], row["source_stable_id"], row["target_stable_id"]))
    return patterns


def analyze_dxf_documentary_grammar(bundle: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, dict) or not isinstance(bundle.get("observations"), list):
        raise ValueError("DXF_DOCUMENTARY_BUNDLE_INVALID")

    sources: list[dict[str, Any]] = []
    for observation in sorted(
        bundle["observations"],
        key=lambda row: str((row.get("source") or {}).get("artifact_name") or ""),
    ):
        source = observation.get("source") or {}
        artifact_name = str(source.get("artifact_name") or "").strip()
        source_sha = str(source.get("sha256") or "").strip()
        if not artifact_name or len(source_sha) != 64:
            raise ValueError("DXF_DOCUMENTARY_SOURCE_BINDING_INVALID")
        authority = observation.get("authority") or {}
        if authority.get("authority_effect") != "NONE":
            raise ValueError("DXF_DOCUMENTARY_AUTHORITY_DRIFT")
        if authority.get("structural_identity_authorized") is not False:
            raise ValueError("DXF_DOCUMENTARY_AUTHORITY_DRIFT")
        if authority.get("canonical_write_authorized") is not False:
            raise ValueError("DXF_DOCUMENTARY_AUTHORITY_DRIFT")

        inventory = observation.get("inventories") or {}
        raw_tokens = inventory.get("text_entities") or []
        if not isinstance(raw_tokens, list):
            raise ValueError("DXF_DOCUMENTARY_TEXT_INVENTORY_INVALID")
        tokens = sorted((_normalize_token(row) for row in raw_tokens), key=lambda row: row["stable_id"])
        patterns = _cross_layer_n_patterns(tokens)
        class_counts = dict(sorted(Counter(row["token_class"] for row in tokens).items()))
        layer_counts = dict(sorted(Counter(row["layer"] for row in tokens).items()))
        origin_counts = dict(sorted(Counter(row["grammar_origin"] for row in tokens).items()))

        sources.append(
            {
                "artifact_name": artifact_name,
                "source_sha256": source_sha,
                "tokens": tokens,
                "cross_layer_patterns": patterns,
                "summary": {
                    "text_token_count": len(tokens),
                    "token_class_counts": class_counts,
                    "layer_counts": layer_counts,
                    "grammar_origin_counts": origin_counts,
                    "cross_layer_pattern_count": len(patterns),
                },
                "authority": _closed_authority(),
            }
        )

    return {
        "schema": "CEW_SPIRAL_DXF_DOCUMENTARY_GRAMMAR_v1",
        "source_count": len(sources),
        "sources": sources,
        "interpretation_boundary": {
            "historical_cew_annotations_may_support_proposals": True,
            "historical_cew_annotations_may_teach_original_drafter_grammar": False,
            "historical_dxf_may_resolve_primary_identity": False,
            "original_drafter_grammar_requires_independent_primary_or_human_corrobation": True,
        },
        "authority": _closed_authority(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze CEW-DXF-01 text observations without promoting authority")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    bundle = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze_dxf_documentary_grammar(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary = {
        source["artifact_name"]: source["summary"] for source in result["sources"]
    }
    print("CEW_SPIRAL_DXF_DOCUMENTARY_GRAMMAR=" + json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
