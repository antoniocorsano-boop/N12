from __future__ import annotations

import re
import unicodedata
from pathlib import Path, PurePosixPath

from .policy import GatewayPolicy
from .types import PathClass

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:[\\/]")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class WorkspaceError(ValueError):
    pass


_CLASS_TO_ZONE = {
    PathClass.SOURCE: "SOURCE",
    PathClass.BASELINE: "BASELINE",
    PathClass.WORKING: "WORKING",
    PathClass.VERIFIED: "VERIFIED",
    PathClass.ISSUED: "ISSUED",
}


class Workspace:
    def __init__(self, root: Path, policy: GatewayPolicy) -> None:
        self.root = root.resolve()
        self.policy = policy
        if not self.root.exists() or not self.root.is_dir():
            raise WorkspaceError("WORKSPACE_ROOT_MISSING")
        self._zones: dict[str, Path] = {}
        for key, relative in policy.zones.items():
            zone = (self.root / relative).resolve()
            if not zone.exists() or not zone.is_dir():
                raise WorkspaceError(f"WORKSPACE_ZONE_MISSING:{key}")
            if not zone.is_relative_to(self.root):
                raise WorkspaceError(f"WORKSPACE_ZONE_ESCAPE:{key}")
            self._zones[key] = zone

    def zone_path(self, zone_key: str) -> Path:
        try:
            return self._zones[zone_key]
        except KeyError as exc:
            raise WorkspaceError("UNKNOWN_WORKSPACE_ZONE") from exc

    def _canonical_ref(self, ref: str) -> tuple[str, ...]:
        if not isinstance(ref, str) or not ref:
            raise WorkspaceError("INVALID_REF")
        if ref != unicodedata.normalize("NFC", ref):
            raise WorkspaceError("NON_CANONICAL_UNICODE_REF")
        if ref.startswith(("/", "\\", "//")) or _DRIVE_PREFIX.match(ref):
            raise WorkspaceError("ABSOLUTE_REF_FORBIDDEN")
        if "\\" in ref:
            raise WorkspaceError("WINDOWS_SEPARATOR_FORBIDDEN")
        pure = PurePosixPath(ref)
        parts = pure.parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise WorkspaceError("TRAVERSAL_REF_FORBIDDEN")

        canonical_names = tuple(self.policy.zones.values())
        first = parts[0]
        if first not in canonical_names:
            folded = {name.casefold(): name for name in canonical_names}
            if first.casefold() in folded:
                raise WorkspaceError("NON_CANONICAL_CASE_REF")
            raise WorkspaceError("UNKNOWN_WORKSPACE_ZONE")
        return parts

    def _zone_for_parts(self, parts: tuple[str, ...]) -> tuple[str, Path]:
        relative = parts[0]
        for key, configured in self.policy.zones.items():
            if relative == configured:
                return key, self._zones[key]
        raise WorkspaceError("UNKNOWN_WORKSPACE_ZONE")

    def classify(self, path: Path) -> PathClass:
        resolved = path.resolve()
        for path_class, zone_key in _CLASS_TO_ZONE.items():
            zone = self._zones[zone_key]
            if resolved == zone or resolved.is_relative_to(zone):
                return path_class
        raise WorkspaceError("PATH_CLASS_NOT_EXPOSED")

    def resolve_ref(self, ref: str, expected: PathClass) -> Path:
        parts = self._canonical_ref(ref)
        zone_key, zone = self._zone_for_parts(parts)
        expected_zone = _CLASS_TO_ZONE.get(expected)
        if expected_zone is None or zone_key != expected_zone:
            raise WorkspaceError("PATH_CLASS_MISMATCH")
        candidate = (self.root.joinpath(*parts)).resolve()
        if not candidate.is_relative_to(zone):
            raise WorkspaceError("REALPATH_ESCAPE")
        return candidate

    def reference_for(self, path: Path, expected: PathClass) -> str:
        resolved = path.resolve()
        if self.classify(resolved) is not expected:
            raise WorkspaceError("PATH_CLASS_MISMATCH")
        try:
            relative = resolved.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise WorkspaceError("PATH_OUTSIDE_WORKSPACE") from exc
        checked = self.resolve_ref(relative, expected)
        if checked != resolved:
            raise WorkspaceError("REFERENCE_REALPATH_MISMATCH")
        return relative

    def verified_output(self, source_ref: str, changeset_id: str, suffix: str) -> Path:
        source = self.resolve_ref(source_ref, PathClass.WORKING)
        if not _SAFE_ID.fullmatch(changeset_id):
            raise WorkspaceError("INVALID_CHANGESET_ID")
        if not suffix.startswith(".") or "/" in suffix or "\\" in suffix:
            raise WorkspaceError("INVALID_OUTPUT_SUFFIX")
        verified_root = self._zones["VERIFIED"]
        output = (verified_root / f"{source.stem}__{changeset_id}{suffix}").resolve()
        if not output.is_relative_to(verified_root):
            raise WorkspaceError("VERIFIED_OUTPUT_ESCAPE")
        if output.exists():
            raise WorkspaceError("VERIFIED_OUTPUT_COLLISION")
        return output
