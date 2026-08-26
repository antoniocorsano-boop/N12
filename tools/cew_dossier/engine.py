from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "CEW-DOSSIER-MANIFEST-v1"
VALID_SECTION_STATES = {"AVAILABLE", "UNAVAILABLE_BLOCKED"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _validate_binding(binding: dict[str, Any], where: str) -> list[str]:
    errors: list[str] = []
    for field in ("kind", "id", "generation_id", "fingerprint"):
        if not str(binding.get(field, "")).strip():
            errors.append(f"{where}: binding missing {field}")
    if binding.get("fingerprint") and not str(binding["fingerprint"]).startswith("sha256:"):
        errors.append(f"{where}: fingerprint must be sha256:...")
    return errors


def normalize_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not str(spec.get("project_id", "")).strip():
        raise ValueError("project_id is required")
    sections = spec.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("at least one dossier section is required")
    normalized_sections: list[dict[str, Any]] = []
    for raw in sections:
        state = raw.get("state")
        if state not in VALID_SECTION_STATES:
            raise ValueError(f"invalid dossier section state: {state}")
        item = {
            "section_id": str(raw.get("section_id", "")).strip(),
            "title": str(raw.get("title", "")).strip(),
            "state": state,
            "bindings": sorted(raw.get("bindings", []), key=lambda x: (x.get("kind", ""), x.get("id", ""), x.get("generation_id", ""))),
            "blockers": sorted(str(x) for x in raw.get("blockers", [])),
            "artifact_refs": sorted(str(x) for x in raw.get("artifact_refs", [])),
        }
        if not item["section_id"] or not item["title"]:
            raise ValueError("section_id and title are required")
        if state == "AVAILABLE" and not item["bindings"]:
            raise ValueError(f"AVAILABLE section {item['section_id']} requires exact generation bindings")
        if state == "UNAVAILABLE_BLOCKED" and not item["blockers"]:
            raise ValueError(f"UNAVAILABLE_BLOCKED section {item['section_id']} requires blockers")
        if state == "UNAVAILABLE_BLOCKED" and item["artifact_refs"]:
            raise ValueError(f"blocked section {item['section_id']} cannot expose fabricated report artifacts")
        normalized_sections.append(item)
    normalized_sections.sort(key=lambda x: x["section_id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": str(spec["project_id"]).strip(),
        "supersedes": spec.get("supersedes"),
        "global_bindings": sorted(spec.get("global_bindings", []), key=lambda x: (x.get("kind", ""), x.get("id", ""), x.get("generation_id", ""))),
        "sections": normalized_sections,
        "authority": "GENERATION_BOUND_MANIFEST_NOT_ENGINEERING_AUTHORITY",
        "canonical_promotion": "DISABLED",
        "rendering_policy": "RENDERERS_ARE_PROJECTIONS_OF_THIS_MANIFEST",
    }


def build_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    body = normalize_spec(spec)
    errors: list[str] = []
    for i, binding in enumerate(body["global_bindings"]):
        errors.extend(_validate_binding(binding, f"global_bindings[{i}]"))
    for section in body["sections"]:
        for i, binding in enumerate(section["bindings"]):
            errors.extend(_validate_binding(binding, f"section {section['section_id']} bindings[{i}]"))
    if errors:
        raise ValueError("; ".join(errors))
    content_fingerprint = digest(body)
    return {
        **body,
        "generation_id": "DOSGEN-" + content_fingerprint.split(":", 1)[1][:16],
        "content_fingerprint": content_fingerprint,
    }


def validate_manifest(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported dossier schema")
    try:
        body = {k: manifest[k] for k in ("schema_version", "project_id", "supersedes", "global_bindings", "sections", "authority", "canonical_promotion", "rendering_policy")}
    except KeyError as exc:
        return False, [f"manifest missing {exc.args[0]}"]
    expected = digest(body)
    if manifest.get("content_fingerprint") != expected:
        errors.append("dossier content fingerprint mismatch")
    if manifest.get("generation_id") != "DOSGEN-" + expected.split(":", 1)[1][:16]:
        errors.append("dossier generation identity mismatch")
    if manifest.get("canonical_promotion") != "DISABLED":
        errors.append("dossier cannot promote canonical engineering truth")
    try:
        rebuilt = build_manifest({
            "project_id": manifest.get("project_id"),
            "supersedes": manifest.get("supersedes"),
            "global_bindings": manifest.get("global_bindings", []),
            "sections": manifest.get("sections", []),
        })
        if rebuilt["content_fingerprint"] != manifest.get("content_fingerprint"):
            errors.append("dossier normalization differs from stored manifest")
    except ValueError as exc:
        errors.append(str(exc))
    return not errors, errors


def write_immutable(path: Path, manifest: dict[str, Any]) -> str:
    ok, errors = validate_manifest(manifest)
    if not ok:
        raise ValueError("; ".join(errors))
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != text:
            raise FileExistsError("immutable dossier generation path already contains different content")
        return "ALREADY_PRESENT_IDENTICAL"
    path.write_text(text, encoding="utf-8")
    return "WRITTEN"


def render_html(manifest: dict[str, Any]) -> str:
    ok, errors = validate_manifest(manifest)
    if not ok:
        raise ValueError("; ".join(errors))
    rows: list[str] = []
    for section in manifest["sections"]:
        if section["state"] == "AVAILABLE":
            detail = "<ul>" + "".join(
                f"<li>{html.escape(str(b['kind']))}: {html.escape(str(b['id']))} — generation {html.escape(str(b['generation_id']))} — {html.escape(str(b['fingerprint']))}</li>"
                for b in section["bindings"]
            ) + "</ul>"
        else:
            detail = "<p>Blocked: " + html.escape("; ".join(section["blockers"])) + "</p>"
        rows.append(f"<section><h2>{html.escape(section['title'])}</h2><p>State: {section['state']}</p>{detail}</section>")
    return "<!doctype html><html><head><meta charset='utf-8'><title>CEW Dossier</title></head><body>" \
        "<header><strong>CEW DOSSIER PROJECTION — NOT ENGINEERING AUTHORITY</strong></header>" \
        f"<h1>{html.escape(manifest['project_id'])}</h1><p>Generation: {manifest['generation_id']}</p>" \
        + "".join(rows) + "</body></html>"


def main() -> None:
    p = argparse.ArgumentParser(description="CEW generation-bound dossier manifest engine")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--spec", type=Path, required=True)
    b.add_argument("--output", type=Path, required=True)
    b.add_argument("--html")
    v = sub.add_parser("validate")
    v.add_argument("--manifest", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "build":
        manifest = build_manifest(json.loads(a.spec.read_text(encoding="utf-8")))
        print(write_immutable(a.output, manifest))
        if a.html:
            hp = Path(a.html)
            hp.parent.mkdir(parents=True, exist_ok=True)
            hp.write_text(render_html(manifest), encoding="utf-8")
        print(json.dumps({"status": "PASS", "generation_id": manifest["generation_id"], "content_fingerprint": manifest["content_fingerprint"]}, indent=2))
    else:
        manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
        ok, errors = validate_manifest(manifest)
        print(json.dumps({"status": "PASS" if ok else "FAIL", "errors": errors}, indent=2))
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
