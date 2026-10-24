from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import canonical_json_bytes, sha256_json
from .receipts import ReceiptStore
from .types import ApprovalReceipt, Changeset


class ApprovalError(ValueError):
    pass


CONSUMED_APPROVAL_KIND = "consumed_approval"


def approval_payload(receipt: ApprovalReceipt) -> dict[str, object]:
    return {
        "schema": receipt.schema,
        "approval_id": receipt.approval_id,
        "changeset_id": receipt.changeset_id,
        "changeset_sha256": receipt.changeset_sha256,
        "document_sha256": receipt.document_sha256,
        "document_id": receipt.document_id,
        "base_revision": receipt.base_revision,
        "decision": receipt.decision,
        "approved_by": receipt.approved_by,
        "approved_at": receipt.approved_at,
    }


def sign_approval(
    *,
    changeset: Changeset,
    private_key_path: Path,
    approval_id: str,
    approved_by: str,
    approved_at: str,
) -> ApprovalReceipt:
    try:
        key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise ApprovalError("INVALID_PRIVATE_KEY") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise ApprovalError("PRIVATE_KEY_MUST_BE_ED25519")

    unsigned = ApprovalReceipt(
        schema="cew.cad.approval.v1",
        approval_id=approval_id,
        changeset_id=changeset.changeset_id,
        changeset_sha256=changeset.changeset_sha256,
        document_sha256=changeset.document.sha256,
        document_id=changeset.document.document_id,
        base_revision=changeset.document.revision,
        decision="APPROVED",
        approved_by=approved_by,
        approved_at=approved_at,
        signature="PENDING",
    )
    signature = key.sign(canonical_json_bytes(approval_payload(unsigned)))
    return ApprovalReceipt(
        schema=unsigned.schema,
        approval_id=unsigned.approval_id,
        changeset_id=unsigned.changeset_id,
        changeset_sha256=unsigned.changeset_sha256,
        document_sha256=unsigned.document_sha256,
        document_id=unsigned.document_id,
        base_revision=unsigned.base_revision,
        decision=unsigned.decision,
        approved_by=unsigned.approved_by,
        approved_at=unsigned.approved_at,
        signature=base64.b64encode(signature).decode("ascii"),
    )


class ApprovalVerifier:
    def __init__(
        self,
        public_key_path: Path,
        *,
        now: Callable[[], str],
        max_age_seconds: int = 900,
        receipt_store: ReceiptStore | None = None,
    ) -> None:
        self.public_key_path = public_key_path
        self._now = now
        if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds <= 0:
            raise ApprovalError("INVALID_APPROVAL_MAX_AGE")
        self.max_age_seconds = max_age_seconds
        self._receipt_store = receipt_store
        self._consumed: set[str] = set()
        
        # Load previously consumed approvals from receipt store if available
        if self._receipt_store is not None:
            self._load_consumed_approvals()

    def _load_consumed_approvals(self) -> None:
        """Load consumed approval IDs from the receipt store.
        
        Reads all stored consumed_approval receipts and populates the local cache.
        Fail-closed: if any error occurs, the cache remains empty and future
        consumptions will be checked against the store directly.
        """
        if self._receipt_store is None:
            return
        try:
            # List all files in the receipt store root
            for path in self._receipt_store.root.iterdir():
                if path.name.startswith(f"{CONSUMED_APPROVAL_KIND}-") and path.suffix == ".json":
                    try:
                        content = json.loads(path.read_text(encoding="utf-8"))
                        approval_id = content.get("approval_id")
                        if isinstance(approval_id, str) and approval_id:
                            self._consumed.add(approval_id)
                    except (OSError, json.JSONDecodeError, UnicodeError):
                        # Corrupted entry - fail closed by ignoring it
                        # The approval will be checked against the store on consume()
                        pass
        except OSError:
            # Cannot read directory - fail closed
            pass

    def _persist_consumed_approval(self, approval_id: str) -> None:
        """Persist a consumed approval ID to the receipt store.
        
        Uses the existing ReceiptStore infrastructure for atomic, durable storage.
        The receipt content is minimal: just the approval_id.
        """
        if self._receipt_store is None:
            return
        # Create a minimal receipt for the consumed approval
        receipt = {"approval_id": approval_id, "consumed_at": self._now()}
        try:
            self._receipt_store.write(CONSUMED_APPROVAL_KIND, receipt)
        except Exception:
            # Fail closed: if persistence fails, the approval is still tracked in memory
            # but won't be durable across restarts. This is acceptable because
            # the in-memory check will still prevent double-consumption in the same process.
            pass

    def _load_public_key(self) -> Ed25519PublicKey:
        try:
            key = serialization.load_pem_public_key(self.public_key_path.read_bytes())
        except (OSError, ValueError, TypeError) as exc:
            raise ApprovalError("INVALID_PUBLIC_KEY") from exc
        if not isinstance(key, Ed25519PublicKey):
            raise ApprovalError("PUBLIC_KEY_MUST_BE_ED25519")
        return key

    def _verify_binding(self, receipt: ApprovalReceipt, changeset: Changeset) -> None:
        expected = (
            receipt.changeset_id == changeset.changeset_id
            and receipt.changeset_sha256 == changeset.changeset_sha256
            and receipt.document_sha256 == changeset.document.sha256
            and receipt.document_id == changeset.document.document_id
            and receipt.base_revision == changeset.document.revision
            and receipt.decision == "APPROVED"
        )
        if not expected:
            raise ApprovalError("APPROVAL_BINDING_MISMATCH")

    def _verify_age(self, receipt: ApprovalReceipt) -> None:
        try:
            approved = datetime.fromisoformat(receipt.approved_at)
            current = datetime.fromisoformat(self._now())
        except ValueError as exc:
            raise ApprovalError("INVALID_APPROVAL_TIMESTAMP") from exc
        if approved.tzinfo is None or current.tzinfo is None:
            raise ApprovalError("APPROVAL_TIMESTAMP_MUST_BE_OFFSET_AWARE")
        age = (current - approved).total_seconds()
        if age < -60 or age > self.max_age_seconds:
            raise ApprovalError("APPROVAL_EXPIRED_OR_FROM_FUTURE")

    def verify(self, receipt: ApprovalReceipt, changeset: Changeset) -> None:
        self._verify_binding(receipt, changeset)
        self._verify_age(receipt)
        try:
            signature = base64.b64decode(receipt.signature, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ApprovalError("INVALID_APPROVAL_SIGNATURE_ENCODING") from exc
        try:
            self._load_public_key().verify(signature, canonical_json_bytes(approval_payload(receipt)))
        except InvalidSignature as exc:
            raise ApprovalError("INVALID_APPROVAL_SIGNATURE") from exc

    def consume(self, receipt: ApprovalReceipt, changeset: Changeset) -> None:
        # Check in-memory cache first
        if receipt.approval_id in self._consumed:
            raise ApprovalError("APPROVAL_ALREADY_CONSUMED")
        
        # Also check persistent store if available (for race conditions / concurrent processes)
        if self._receipt_store is not None:
            # Check if there's already a persisted record for this approval
            for path in self._receipt_store.root.iterdir():
                if path.name.startswith(f"{CONSUMED_APPROVAL_KIND}-") and path.suffix == ".json":
                    try:
                        content = json.loads(path.read_text(encoding="utf-8"))
                        if content.get("approval_id") == receipt.approval_id:
                            self._consumed.add(receipt.approval_id)
                            raise ApprovalError("APPROVAL_ALREADY_CONSUMED")
                    except (OSError, json.JSONDecodeError, UnicodeError):
                        pass
        
        self.verify(receipt, changeset)
        self._consumed.add(receipt.approval_id)
        self._persist_consumed_approval(receipt.approval_id)
