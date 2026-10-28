from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .command_plan import BenchmarkFixture


_CATEGORY_BY_COMMAND = {
    "structural_column": "structuralcolumn",
    "beam": "beam",
    "footing": "footing",
    "floor": "floor",
}


@dataclass(frozen=True)
class ReconciliationDifference:
    code: str
    object_id: str
    field: str | None
    expected: Any
    observed: Any


@dataclass(frozen=True)
class ReconciliationResult:
    status: str
    expected_count: int
    observed_count: int
    differences: tuple[ReconciliationDifference, ...]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _elements(query: Any) -> list[Mapping[str, Any]]:
    if not isinstance(query, Mapping):
        return []
    values = query.get("elements")
    if not isinstance(values, list):
        return []
    return [item for item in values if isinstance(item, Mapping)]


def normalize_bimcraft_queries(
    fixture: BenchmarkFixture,
    queries: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Translate BIMCraft's live element shape back to the fixture's semantic fields."""
    level_names: dict[str, str] = {}
    for level in _elements(queries.get("level")):
        guid = level.get("guid")
        name = level.get("name")
        if isinstance(guid, str) and isinstance(name, str):
            level_names[guid] = name

    expected_by_id = {obj.object_id: obj for obj in fixture.objects}
    observations: list[dict[str, Any]] = []

    for category in ("structuralcolumn", "beam", "footing", "floor"):
        for element in _elements(queries.get(category)):
            provenance = dict(_mapping(element.get("params")))
            object_id = provenance.get("CEW_OBJECT_ID")
            observed_id = object_id if isinstance(object_id, str) and object_id else None
            expected = expected_by_id.get(observed_id or "")

            params: dict[str, Any]
            if category == "structuralcolumn":
                params = {
                    "at": element.get("at"),
                    "type": element.get("type"),
                    "level": level_names.get(str(element.get("level")), element.get("level")),
                    "top_level": level_names.get(str(element.get("top_level")), element.get("top_level")),
                }
            elif category == "beam":
                params = {
                    "points": [element.get("start"), element.get("end")],
                    "type": element.get("type"),
                    "level": level_names.get(str(element.get("level")), element.get("level")),
                    "justify": element.get("justify"),
                }
            elif category == "footing":
                height = element.get("height")
                base_offset = element.get("base_offset")
                offset = None
                if isinstance(height, (int, float)) and not isinstance(height, bool) and isinstance(base_offset, (int, float)) and not isinstance(base_offset, bool):
                    offset = height + base_offset
                params = {
                    "at": element.get("at"),
                    "type": element.get("type"),
                    "thickness": height,
                    "level": level_names.get(str(element.get("level")), element.get("level")),
                    "offset": offset,
                }
            else:
                params = {
                    "boundary": element.get("boundary"),
                    "level": level_names.get(str(element.get("level")), element.get("level")),
                    "structural": element.get("structural"),
                }

            # Compare only fields the governed fixture explicitly requested. This keeps
            # BIMCraft's derived fields visible in raw evidence without mistaking them
            # for additional CEW input authority.
            if expected is not None:
                params = {key: params.get(key) for key in expected.params}

            observations.append(
                {
                    "object_id": observed_id,
                    "category": element.get("category", category),
                    "params": params,
                    "provenance": provenance,
                    "bimcraft_id": element.get("id"),
                    "bimcraft_guid": element.get("guid"),
                }
            )

    return observations


def reconcile_fixture(
    fixture: BenchmarkFixture,
    observations: Sequence[Mapping[str, Any]],
) -> ReconciliationResult:
    differences: list[ReconciliationDifference] = []
    expected = {obj.object_id: obj for obj in fixture.objects}
    observed: dict[str, Mapping[str, Any]] = {}

    for item in observations:
        object_id = item.get("object_id") if isinstance(item, Mapping) else None
        if not isinstance(object_id, str) or not object_id:
            differences.append(
                ReconciliationDifference(
                    code="INVALID_OBSERVATION",
                    object_id="<unknown>",
                    field="object_id",
                    expected="non-empty CEW object id",
                    observed=object_id,
                )
            )
            continue
        if object_id in observed:
            differences.append(
                ReconciliationDifference(
                    code="DUPLICATE_OBSERVATION",
                    object_id=object_id,
                    field=None,
                    expected="single observation",
                    observed="duplicate",
                )
            )
            continue
        observed[object_id] = item

    for object_id, obj in expected.items():
        item = observed.get(object_id)
        if item is None:
            differences.append(
                ReconciliationDifference(
                    code="MISSING_OBJECT",
                    object_id=object_id,
                    field=None,
                    expected="present",
                    observed="missing",
                )
            )
            continue

        expected_category = _CATEGORY_BY_COMMAND[obj.command]
        observed_category = item.get("category")
        if observed_category != expected_category:
            differences.append(
                ReconciliationDifference(
                    code="CATEGORY_MISMATCH",
                    object_id=object_id,
                    field="category",
                    expected=expected_category,
                    observed=observed_category,
                )
            )

        observed_params = dict(_mapping(item.get("params")))
        if observed_params != dict(obj.params):
            differences.append(
                ReconciliationDifference(
                    code="PARAM_MISMATCH",
                    object_id=object_id,
                    field="params",
                    expected=dict(obj.params),
                    observed=observed_params,
                )
            )

        observed_provenance = dict(_mapping(item.get("provenance")))
        if observed_provenance != dict(obj.provenance):
            differences.append(
                ReconciliationDifference(
                    code="PROVENANCE_MISMATCH",
                    object_id=object_id,
                    field="provenance",
                    expected=dict(obj.provenance),
                    observed=observed_provenance,
                )
            )

    for object_id, item in observed.items():
        if object_id not in expected:
            differences.append(
                ReconciliationDifference(
                    code="EXTRA_OBJECT",
                    object_id=object_id,
                    field=None,
                    expected="absent",
                    observed=dict(item),
                )
            )

    return ReconciliationResult(
        status="PASS" if not differences else "REWORK",
        expected_count=len(expected),
        observed_count=len(observed),
        differences=tuple(differences),
    )
