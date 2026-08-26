from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "automation" / "CEW_DEGRADATION_CAPABILITY_MANIFEST_v0.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob(path: Path) -> str:
    return subprocess.run(["git", "hash-object", str(path)], text=True, capture_output=True, check=True).stdout.strip()


def main() -> None:
    p = argparse.ArgumentParser(description="Validate Platform OS adoption of the existing CEW degradation safety capability")
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    manifest = load(a.manifest)
    origin = manifest["origin"]
    registry_path = ROOT / origin["registry"]["path"]
    engine_path = ROOT / origin["safety_engine"]["path"]
    errors: list[str] = []

    if git_blob(registry_path) != origin["registry"]["git_blob_sha"]:
        errors.append("degradation registry drift from validated origin")
    if git_blob(engine_path) != origin["safety_engine"]["git_blob_sha"]:
        errors.append("degradation engine drift from validated origin")

    registry = load(registry_path)
    required_model_fields = set(manifest["required_model_fields"])
    for model in registry.get("models", []):
        missing = required_model_fields - set(model)
        if missing:
            errors.append(f"{model.get('model_id','<unknown>')}: missing fields {sorted(missing)}")
        if not str(model.get("applicability", "")).strip():
            errors.append(f"{model.get('model_id')}: empty applicability")
        if not str(model.get("parameter_provenance", "")).strip():
            errors.append(f"{model.get('model_id')}: empty parameter provenance")
        if not str(model.get("calibration_state", "")).strip():
            errors.append(f"{model.get('model_id')}: empty calibration state")

    activation = registry.get("activation_gate", {})
    missing_activation = set(manifest["required_activation_fields"]) - set(activation.get("required_before_project_use", []))
    if missing_activation:
        errors.append(f"activation gate missing requirements: {sorted(missing_activation)}")

    temp_gate = a.output.with_suffix(".engine.json")
    subprocess.run(
        [sys.executable, str(engine_path), "--registry", str(registry_path), "--output", str(temp_gate)],
        text=True,
        capture_output=True,
        check=True,
    )
    gate = load(temp_gate)
    if gate.get("eligible_model_count") != 0:
        errors.append("uncalibrated degradation model became eligible")
    if gate.get("blocked_model_count") != gate.get("model_count"):
        errors.append("not every scaffold degradation model is blocked")
    for model in gate.get("models", []):
        if model.get("scenario_output_authorized"):
            errors.append(f"{model.get('model_id')}: scenario output incorrectly authorized")
    forbidden_output_keys = {"property_overlay", "evidence_updates", "smart_property_updates", "solver_properties"}
    present_forbidden = forbidden_output_keys & set(gate)
    if present_forbidden:
        errors.append(f"safety gate emitted forbidden property/evidence payloads: {sorted(present_forbidden)}")

    result = {
        "schema_version": "0.1.0",
        "work_item_id": "DEG-001",
        "status": "PASS" if not errors else "FAIL",
        "validated_origin": origin,
        "model_count": gate.get("model_count"),
        "blocked_model_count": gate.get("blocked_model_count"),
        "eligible_model_count": gate.get("eligible_model_count"),
        "model_states": [
            {
                "model_id": x.get("model_id"),
                "mechanism": x.get("mechanism"),
                "activation_state": x.get("activation_state"),
                "scenario_output_authorized": x.get("scenario_output_authorized"),
                "missing_activation_requirements": x.get("missing_activation_requirements", []),
            }
            for x in gate.get("models", [])
        ],
        "evidence_mutation": "NOT_EMITTED",
        "project_degradation_values": "NOT_EXECUTED",
        "canonical_promotion": "DISABLED",
        "errors": errors,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
