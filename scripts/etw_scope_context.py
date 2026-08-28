#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
SCOPE_MODEL = ROOT / "automation" / "ETW_PLATFORM_SCOPE_MODEL_v1.json"


class ScopeContextError(ValueError):
    pass


@dataclass(frozen=True)
class ScopeContext:
    project_id: str
    discipline_id: str
    scope_state: str
    module_state: str

    @property
    def identity(self) -> str:
        return f"{self.project_id}:{self.discipline_id}"

    @property
    def fingerprint(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def _read_model(path: Path = SCOPE_MODEL) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_scope_context(
    project_id: str | None,
    discipline_id: str | None,
    *,
    model_path: Path = SCOPE_MODEL,
) -> ScopeContext:
    if not project_id:
        raise ScopeContextError("MISSING_PROJECT")
    if not discipline_id:
        raise ScopeContextError("MISSING_DISCIPLINE")

    model = _read_model(model_path)
    projects = {item["project_id"] for item in model.get("projects", [])}
    disciplines = {item["discipline_id"] for item in model.get("disciplines", [])}
    if project_id not in projects:
        raise ScopeContextError("UNKNOWN_PROJECT")
    if discipline_id not in disciplines:
        raise ScopeContextError("UNKNOWN_DISCIPLINE")

    for scope in model.get("project_discipline_scopes", []):
        if scope.get("project_id") == project_id and scope.get("discipline_id") == discipline_id:
            return ScopeContext(
                project_id=project_id,
                discipline_id=discipline_id,
                scope_state=str(scope.get("scope_state")),
                module_state=str(scope.get("module_state")),
            )
    raise ScopeContextError("SCOPE_NOT_DECLARED")


def scoped_cache_key(namespace: str, context: ScopeContext, object_key: str) -> str:
    if not namespace or not object_key:
        raise ScopeContextError("CACHE_KEY_COMPONENT_REQUIRED")
    return f"etw:{namespace}:{context.project_id}:{context.discipline_id}:{context.fingerprint[:16]}:{object_key}"


def issue_async_token(context: ScopeContext, request_id: str) -> str:
    if not request_id:
        raise ScopeContextError("REQUEST_ID_REQUIRED")
    digest = hashlib.sha256(f"{context.fingerprint}:{request_id}".encode("utf-8")).hexdigest()
    return f"{context.identity}:{request_id}:{digest}"


def async_response_matches(token: str, current_context: ScopeContext, request_id: str) -> bool:
    try:
        expected = issue_async_token(current_context, request_id)
    except ScopeContextError:
        return False
    return token == expected


def deep_link(path: str, context: ScopeContext, extra_query: dict[str, str] | None = None) -> str:
    if not path.startswith("/"):
        raise ScopeContextError("ABSOLUTE_APP_PATH_REQUIRED")
    query = {
        "project": context.project_id,
        "discipline": context.discipline_id,
    }
    if extra_query:
        for key, value in extra_query.items():
            if key in {"project", "discipline"}:
                raise ScopeContextError("SCOPE_QUERY_OVERRIDE_FORBIDDEN")
            query[key] = value
    return f"{path}?{urlencode(query)}"


def restore_context_from_url(url_or_path: str, *, model_path: Path = SCOPE_MODEL) -> ScopeContext:
    parsed = urlparse(url_or_path)
    query = parse_qs(parsed.query, keep_blank_values=True)
    project = query.get("project", [None])[0]
    discipline = query.get("discipline", [None])[0]
    return resolve_scope_context(project, discipline, model_path=model_path)


def history_state(context: ScopeContext) -> dict[str, str]:
    return {
        "project_id": context.project_id,
        "discipline_id": context.discipline_id,
        "scope_fingerprint": context.fingerprint,
    }


def restore_context_from_history(state: dict[str, Any], *, model_path: Path = SCOPE_MODEL) -> ScopeContext:
    context = resolve_scope_context(
        state.get("project_id"),
        state.get("discipline_id"),
        model_path=model_path,
    )
    if state.get("scope_fingerprint") != context.fingerprint:
        raise ScopeContextError("STALE_SCOPE_HISTORY")
    return context


def validate_scope_runtime() -> list[str]:
    errors: list[str] = []
    n12_structures = resolve_scope_context("N12", "STRUCTURES")
    n12_architecture = resolve_scope_context("N12", "ARCHITECTURE")
    test_structures = resolve_scope_context("TEST_PROJECT", "STRUCTURES")

    if n12_structures.identity == n12_architecture.identity:
        errors.append("discipline is missing from ScopeContext identity")
    if n12_structures.identity == test_structures.identity:
        errors.append("project is missing from ScopeContext identity")

    key_a = scoped_cache_key("inventory", n12_structures, "root")
    key_b = scoped_cache_key("inventory", test_structures, "root")
    if key_a == key_b:
        errors.append("cache key leaks across projects")

    request_id = "inventory-load-1"
    token = issue_async_token(n12_structures, request_id)
    if not async_response_matches(token, n12_structures, request_id):
        errors.append("valid async response rejected")
    if async_response_matches(token, test_structures, request_id):
        errors.append("stale async response accepted after project switch")
    if async_response_matches(token, n12_architecture, request_id):
        errors.append("stale async response accepted after discipline switch")

    link = deep_link("/portfolio/scope", n12_architecture, {"view": "sources"})
    restored = restore_context_from_url(link)
    if restored != n12_architecture:
        errors.append("deep-link context did not restore exactly")

    state = history_state(n12_structures)
    if restore_context_from_history(state) != n12_structures:
        errors.append("history context did not restore exactly")
    stale = dict(state)
    stale["scope_fingerprint"] = "0" * 64
    try:
        restore_context_from_history(stale)
        errors.append("stale history state was accepted")
    except ScopeContextError as exc:
        if str(exc) != "STALE_SCOPE_HISTORY":
            errors.append(f"unexpected stale-history error: {exc}")

    invalid_cases = [
        (None, "STRUCTURES", "MISSING_PROJECT"),
        ("", "STRUCTURES", "MISSING_PROJECT"),
        ("UNKNOWN", "STRUCTURES", "UNKNOWN_PROJECT"),
        ("N12", None, "MISSING_DISCIPLINE"),
        ("N12", "", "MISSING_DISCIPLINE"),
        ("N12", "UNKNOWN", "UNKNOWN_DISCIPLINE"),
        ("TEST_PROJECT", "ARCHITECTURE", "SCOPE_NOT_DECLARED"),
    ]
    for project_id, discipline_id, expected in invalid_cases:
        try:
            resolve_scope_context(project_id, discipline_id)
            errors.append(f"invalid scope {project_id}/{discipline_id} did not fail closed")
        except ScopeContextError as exc:
            if str(exc) != expected:
                errors.append(f"invalid scope expected {expected}, got {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="eTwin fail-closed ScopeContext runtime")
    parser.add_argument("--project", default="N12")
    parser.add_argument("--discipline", default="STRUCTURES")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        errors = validate_scope_runtime()
        if errors:
            print("ETW_SCOPE_CONTEXT = FAIL")
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("ETW_SCOPE_CONTEXT = PASS")
        return 0

    try:
        context = resolve_scope_context(args.project, args.discipline)
    except ScopeContextError as exc:
        print(json.dumps({"state": "SCOPE_REJECTED", "reason": str(exc)}, indent=2))
        return 2
    print(json.dumps({**asdict(context), "identity": context.identity, "fingerprint": context.fingerprint}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
