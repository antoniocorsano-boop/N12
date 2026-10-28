from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .contracts import BIMCraftContractError


REQUIRED_PROVENANCE = (
    "CEW_OBJECT_ID",
    "CEW_EVIDENCE_ID",
    "CEW_SOURCE_SHA256",
    "CEW_EPISTEMIC_STATE",
    "CEW_REVISION",
    "CEW_AUTHORITY",
)
PARAMETER_CATEGORIES = ("structuralcolumn", "beam", "footing", "floor")
OBJECT_COMMANDS = frozenset({"structural_column", "beam", "footing", "floor"})
ALLOWED_COMMANDS = frozenset({"parameter", "level", "type", *OBJECT_COMMANDS, "modify"})
_ALLOWED_EPISTEMIC_STATES = frozenset({"DOC", "MIS", "RIF", "INF", "INC", "ND"})


class BIMCraftFixtureError(BIMCraftContractError):
    """Raised when a benchmark fixture violates the CEW authority boundary."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BIMCraftFixtureError(f"{name} must be a mapping")
    return value


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BIMCraftFixtureError(f"{name} must be a non-empty string")
    return value.strip()


def _false(value: Any, name: str) -> bool:
    if value is not False:
        raise BIMCraftFixtureError("FIXTURE_AUTHORITY_FORBIDDEN")
    return False


def _number(value: Any, name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BIMCraftFixtureError(f"{name} must be numeric")
    return value


def _sha256(value: Any, name: str) -> str:
    text = _text(value, name).lower()
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise BIMCraftFixtureError(f"{name} must be 64-character lowercase hex")
    return text


@dataclass(frozen=True)
class BenchmarkLevel:
    name: str
    elevation: int | float


@dataclass(frozen=True)
class BenchmarkType:
    category: str
    name: str
    params: Mapping[str, Any]


@dataclass(frozen=True)
class BenchmarkObject:
    object_id: str
    command: str
    params: Mapping[str, Any]
    provenance: Mapping[str, str]


@dataclass(frozen=True)
class BenchmarkFixture:
    schema_id: str
    schema_version: int
    project: str
    authority: str
    canonical: bool
    structural_identity_authorized: bool
    units: str
    source_kind: str
    source_ref: str
    source_sha256: str
    levels: tuple[BenchmarkLevel, ...]
    types: tuple[BenchmarkType, ...]
    objects: tuple[BenchmarkObject, ...]


@dataclass(frozen=True)
class BIMCraftCommand:
    command: str
    params: Mapping[str, Any]
    bind: str | None = None
    ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"command": self.command, "params": dict(self.params)}
        if self.bind is not None:
            data["bind"] = self.bind
        if self.ref is not None:
            data["ref"] = self.ref
        return data


@dataclass(frozen=True)
class BIMCraftCommandPlan:
    schema_id: str
    schema_version: int
    project: str
    authority: str
    commands: tuple[BIMCraftCommand, ...]
    canonical_json: str
    sha256: str


def load_benchmark_fixture(path: str | Path) -> BenchmarkFixture:
    source_path = Path(path)
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BIMCraftFixtureError("BIMCRAFT_FIXTURE_UNREADABLE") from exc

    root = _mapping(raw, "fixture")
    if root.get("schema_id") != "CEW_BIMCRAFT_STAGE_A_FIXTURE" or root.get("schema_version") != 1:
        raise BIMCraftFixtureError("BIMCRAFT_FIXTURE_SCHEMA_MISMATCH")

    project = _text(root.get("project"), "project")
    authority = _text(root.get("authority"), "authority")
    if authority != "BENCHMARK_ONLY" or root.get("canonical") is not False or root.get("structural_identity_authorized") is not False:
        raise BIMCraftFixtureError("FIXTURE_AUTHORITY_FORBIDDEN")
    if project != "CEW-BIMCRAFT-01-STAGE-A" or "N12" in project.upper():
        raise BIMCraftFixtureError("FIXTURE_PROJECT_FORBIDDEN")
    units = _text(root.get("units"), "units")
    if units != "mm":
        raise BIMCraftFixtureError("BIMCRAFT_FIXTURE_UNITS_MUST_BE_MM")

    source = _mapping(root.get("source"), "source")
    source_kind = _text(source.get("kind"), "source.kind")
    source_ref = _text(source.get("source_ref"), "source.source_ref")
    source_sha = _sha256(source.get("sha256"), "source.sha256")
    if source_kind != "synthetic_fixture":
        raise BIMCraftFixtureError("STAGE_A_SOURCE_MUST_BE_SYNTHETIC")

    raw_levels = root.get("levels")
    if not isinstance(raw_levels, list) or not raw_levels:
        raise BIMCraftFixtureError("fixture.levels must be a non-empty list")
    levels: list[BenchmarkLevel] = []
    level_names: set[str] = set()
    for index, item in enumerate(raw_levels):
        value = _mapping(item, f"levels[{index}]")
        name = _text(value.get("name"), f"levels[{index}].name")
        if name in level_names:
            raise BIMCraftFixtureError("DUPLICATE_LEVEL")
        level_names.add(name)
        levels.append(BenchmarkLevel(name=name, elevation=_number(value.get("elevation"), f"levels[{index}].elevation")))

    raw_types = root.get("types")
    if not isinstance(raw_types, list):
        raise BIMCraftFixtureError("fixture.types must be a list")
    types: list[BenchmarkType] = []
    for index, item in enumerate(raw_types):
        value = dict(_mapping(item, f"types[{index}]"))
        category = _text(value.pop("category", None), f"types[{index}].category")
        name = _text(value.pop("name", None), f"types[{index}].name")
        if category not in PARAMETER_CATEGORIES:
            raise BIMCraftFixtureError("UNSUPPORTED_TYPE_CATEGORY")
        types.append(BenchmarkType(category=category, name=name, params=value))

    raw_objects = root.get("objects")
    if not isinstance(raw_objects, list) or not raw_objects:
        raise BIMCraftFixtureError("fixture.objects must be a non-empty list")
    objects: list[BenchmarkObject] = []
    object_ids: set[str] = set()
    for index, item in enumerate(raw_objects):
        value = _mapping(item, f"objects[{index}]")
        object_id = _text(value.get("object_id"), f"objects[{index}].object_id")
        if object_id in object_ids:
            raise BIMCraftFixtureError("DUPLICATE_OBJECT_ID")
        object_ids.add(object_id)
        command = _text(value.get("command"), f"objects[{index}].command")
        if command not in OBJECT_COMMANDS:
            raise BIMCraftFixtureError("UNSUPPORTED_OBJECT_COMMAND")
        params = dict(_mapping(value.get("params"), f"objects[{index}].params"))
        provenance_raw = _mapping(value.get("provenance"), f"objects[{index}].provenance")
        if set(provenance_raw) != set(REQUIRED_PROVENANCE):
            raise BIMCraftFixtureError("PROVENANCE_FIELDS_MISMATCH")
        provenance = {key: _text(provenance_raw.get(key), f"objects[{index}].provenance.{key}") for key in REQUIRED_PROVENANCE}
        if provenance["CEW_AUTHORITY"] != "BENCHMARK_ONLY":
            raise BIMCraftFixtureError("FIXTURE_AUTHORITY_FORBIDDEN")
        if provenance["CEW_OBJECT_ID"] != object_id:
            raise BIMCraftFixtureError("PROVENANCE_OBJECT_ID_MISMATCH")
        if provenance["CEW_SOURCE_SHA256"] != source_sha:
            raise BIMCraftFixtureError("PROVENANCE_SOURCE_SHA256_MISMATCH")
        epistemic_state = provenance["CEW_EPISTEMIC_STATE"]
        if epistemic_state not in _ALLOWED_EPISTEMIC_STATES:
            raise BIMCraftFixtureError("INVALID_EPISTEMIC_STATE")
        if source_kind == "synthetic_fixture" and epistemic_state == "DOC":
            raise BIMCraftFixtureError("SYNTHETIC_DOC_FORBIDDEN")
        objects.append(BenchmarkObject(object_id=object_id, command=command, params=params, provenance=provenance))

    return BenchmarkFixture(
        schema_id="CEW_BIMCRAFT_STAGE_A_FIXTURE",
        schema_version=1,
        project=project,
        authority=authority,
        canonical=_false(root.get("canonical"), "canonical"),
        structural_identity_authorized=_false(root.get("structural_identity_authorized"), "structural_identity_authorized"),
        units=units,
        source_kind=source_kind,
        source_ref=source_ref,
        source_sha256=source_sha,
        levels=tuple(levels),
        types=tuple(types),
        objects=tuple(objects),
    )


def compile_command_plan(fixture: BenchmarkFixture) -> BIMCraftCommandPlan:
    if fixture.authority != "BENCHMARK_ONLY" or fixture.canonical or fixture.structural_identity_authorized:
        raise BIMCraftFixtureError("FIXTURE_AUTHORITY_FORBIDDEN")

    commands: list[BIMCraftCommand] = []

    for name in REQUIRED_PROVENANCE:
        commands.append(
            BIMCraftCommand(
                command="parameter",
                params={
                    "name": name,
                    "kind": "text",
                    "categories": list(PARAMETER_CATEGORIES),
                },
            )
        )

    for level in fixture.levels:
        commands.append(
            BIMCraftCommand(
                command="level",
                params={"name": level.name, "elevation": level.elevation},
            )
        )

    for item in fixture.types:
        params = {"category": item.category, "name": item.name, **dict(item.params)}
        commands.append(BIMCraftCommand(command="type", params=params))

    for obj in fixture.objects:
        bind = f"element:{obj.object_id}"
        commands.append(
            BIMCraftCommand(
                command=obj.command,
                params=dict(obj.params),
                bind=bind,
            )
        )
        commands.append(
            BIMCraftCommand(
                command="modify",
                params={"params": dict(obj.provenance)},
                ref=bind,
            )
        )

    for command in commands:
        if command.command not in ALLOWED_COMMANDS:
            raise BIMCraftFixtureError("COMMAND_NOT_ALLOWLISTED")

    payload = {
        "schema_id": "CEW_BIMCRAFT_COMMAND_PLAN",
        "schema_version": 1,
        "project": fixture.project,
        "authority": fixture.authority,
        "commands": [command.as_dict() for command in commands],
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return BIMCraftCommandPlan(
        schema_id="CEW_BIMCRAFT_COMMAND_PLAN",
        schema_version=1,
        project=fixture.project,
        authority=fixture.authority,
        commands=tuple(commands),
        canonical_json=canonical_json,
        sha256=digest,
    )
