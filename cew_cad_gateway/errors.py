from __future__ import annotations


class CewCadError(ValueError):
    """Stable fail-closed CEW-CAD error."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code


INVALID_SHA256 = "INVALID_SHA256"
INVALID_SCHEMA = "INVALID_SCHEMA"
INVALID_DOCUMENT_ID = "INVALID_DOCUMENT_ID"
INVALID_REVISION = "INVALID_REVISION"
INVALID_APPROVAL = "INVALID_APPROVAL"
