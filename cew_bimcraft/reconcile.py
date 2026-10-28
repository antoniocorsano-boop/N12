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
