from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from typing import Any

from .authority import DocumentContract, FrozenAuthority
from .candidate_reader import CandidateReader
from .replay import ReplayResult
from .types import AuthorityIdentity, CandidateIdentity, ControlPlaneIdentity, GateCoreIdentity, InvariantResult, OperationalIdentity, QualificationReceipt

ROOT = "qualification/cew-contract-01/n12/"
Q = ROOT + "qualification.json"
MATRIX = ROOT + "conformance-matrix.csv"
INDEX = ROOT + "evidence-index.json"
MINIMALITY = ROOT + "structural-type-minimality.csv"
SUFFICIENCY = ROOT + "source-sufficiency.md"
REG = ROOT + "registration-uncertainty.json"
MODEL = ROOT + "model-generation.json"
MODEL_RECEIPT = ROOT + "model-generation-receipt.json"
EXPECTED_IDS = tuple(f"C01-T{i:02d}" for i in range(1, 12))
EXPECTED_INV = tuple(f"I{i:02d}" for i in range(1, 18))
BOUNDARY_KEYS = {"solver_authorized", "calculation_model_ready", "synthetic_solver_result", "solver_run", "result_entity_created"}


class PayloadError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise PayloadError("CANDIDATE_JSON_DUPLICATE_KEY")
        value[key] = child
    return value


def _reject_nonfinite_constant(_value: str) -> None:
    raise PayloadError("CANDIDATE_JSON_INVALID")


def _numbers_finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_numbers_finite(child) for child in value.values())
    if isinstance(value, list):
        return all(_numbers_finite(child) for child in value)
    return True


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((_depth(v) for v in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_depth(v) for v in value), default=0)
    return 0


def _json(reader: CandidateReader, path: str, max_depth: int) -> dict[str, Any]:
    try:
        text = reader.read_text(path)
    except ValueError as exc:
        if "UTF-8" in str(exc):
            raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
        raise
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite_constant,
        )
    except json.JSONDecodeError as exc:
        raise PayloadError("CANDIDATE_JSON_INVALID") from exc
    if not _numbers_finite(value):
        raise PayloadError("CANDIDATE_JSON_INVALID")
    if _depth(value) > max_depth:
        raise PayloadError("CANDIDATE_JSON_DEPTH_EXCEEDED")
    if not isinstance(value, dict):
        raise PayloadError("CANDIDATE_JSON_INVALID")
    return value


def _contract(authority: FrozenAuthority, path: str, expected_format: str) -> DocumentContract:
    contracts = {contract.path: contract for contract in authority.document_contracts}
    contract = contracts.get(path)
    if contract is None or contract.format != expected_format:
        raise PayloadError("CANDIDATE_DOCUMENT_CONTRACT_MISSING")
    return contract


def _json_contract(reader: CandidateReader, authority: FrozenAuthority, path: str) -> dict[str, Any]:
    contract = _contract(authority, path, "json")
    value = _json(reader, path, authority.limits.max_json_depth)
    if set(value) != set(contract.allowed_fields):
        if path == Q:
            raise PayloadError("CANDIDATE_SCHEMA_UNEXPECTED_FIELD")
        raise PayloadError("CANDIDATE_DOCUMENT_UNEXPECTED_FIELD")
    for key, expected in contract.schema_identity:
        actual = value.get(key)
        if type(actual) is not type(expected) or actual != expected:
            if path == Q:
                raise PayloadError("CANDIDATE_QUALIFICATION_SCHEMA_UNSUPPORTED")
            raise PayloadError("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED")
    return value


def parse_csv_limited(text: str, max_rows: int, expected_header: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    if expected_header is not None and tuple(reader.fieldnames or ()) != expected_header:
        raise ValueError("CANDIDATE_CSV_HEADER_UNSUPPORTED")
    rows: list[dict[str, str]] = []
    for row in reader:
        if expected_header is not None and (
            tuple(row.keys()) != expected_header
            or any(row[field] is None or row[field] == "" for field in expected_header)
        ):
            raise ValueError("CANDIDATE_CSV_ROW_INVALID")
        rows.append(dict(row))
        if len(rows) > max_rows:
            raise ValueError("CANDIDATE_CSV_ROWS_EXCEEDED")
    return rows


def _csv_contract(reader: CandidateReader, authority: FrozenAuthority, path: str) -> list[dict[str, str]]:
    contract = _contract(authority, path, "csv")
    try:
        text = reader.read_text(path)
    except ValueError as exc:
        if "UTF-8" in str(exc):
            raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
        raise
    try:
        return parse_csv_limited(text, authority.limits.max_csv_rows, contract.csv_header)
    except ValueError as exc:
        if str(exc) in {
            "CANDIDATE_CSV_ROWS_EXCEEDED",
            "CANDIDATE_CSV_HEADER_UNSUPPORTED",
            "CANDIDATE_CSV_ROW_INVALID",
        }:
            raise PayloadError(str(exc)) from exc
        raise


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _bundle_digest(reader: CandidateReader, paths: tuple[str, ...]) -> str:
    reader.verify_allowlisted_surface(paths)
    digest = hashlib.sha256()
    for path in sorted(paths):
        data = reader.read_blob(path)
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).hexdigest().encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _false_exact(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys and all(value[key] is False for key in keys)


def _boundary_claims_safe(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in BOUNDARY_KEYS and child is not False:
                return False
            if not _boundary_claims_safe(child):
                return False
    elif isinstance(value, list):
        return all(_boundary_claims_safe(child) for child in value)
    return True


def _result(ok: bool, code: str, failures: list[str]) -> InvariantResult:
    if ok:
        return InvariantResult.PASS
    failures.append(code)
    return InvariantResult.FAIL


def evaluate_qualification(
    reader: CandidateReader,
    authority: FrozenAuthority,
    replay: ReplayResult,
    control_plane: ControlPlaneIdentity,
    gate_core: GateCoreIdentity,
    candidate: CandidateIdentity,
    *,
    qualified_at: str,
) -> QualificationReceipt:
    failures: list[str] = []
    inv = {key: InvariantResult.NOT_APPLICABLE for key in EXPECTED_INV}
    try:
        digest = _bundle_digest(reader, authority.candidate_allowlist)
        q = _json_contract(reader, authority, Q)
        reg = _json_contract(reader, authority, REG)
        model = _json_contract(reader, authority, MODEL)
        mr = _json_contract(reader, authority, MODEL_RECEIPT)
        index = _json_contract(reader, authority, INDEX)
        matrix = _csv_contract(reader, authority, MATRIX)
        _csv_contract(reader, authority, MINIMALITY)
        try:
            reader.read_text(SUFFICIENCY)
        except ValueError as exc:
            if "UTF-8" in str(exc):
                raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
            raise
        for path in authority.candidate_allowlist:
            if path.endswith(".md"):
                try:
                    reader.read_text(path)
                except ValueError as exc:
                    if "UTF-8" in str(exc):
                        raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
                    raise
    except PayloadError as exc:
        failures.append(exc.code)
        digest = "0" * 64
        return _receipt(authority, replay, control_plane, gate_core, candidate, qualified_at, digest, inv, failures)
    except ValueError:
        failures.append("CANDIDATE_SURFACE_INVALID")
        digest = "0" * 64
        return _receipt(authority, replay, control_plane, gate_core, candidate, qualified_at, digest, inv, failures)

    inv["I01"] = _result(reader.head_sha == candidate.head_sha, "I01_CANDIDATE_HEAD_MISMATCH", failures)
    inv["I02"] = _result(gate_core.version == "G0" and bool(control_plane.base_commit_sha) and bool(authority.source_sha256), "I02_TRUSTED_INVOCATION_INVALID", failures)
    inv["I03"] = _result(
        q.get("operational_commit") == authority.operational_commit
        and model.get("builder", {}).get("source_commit") == authority.operational_commit
        and mr.get("source_commit") == authority.operational_commit,
        "I03_OPERATIONAL_AUTHORITY_MISMATCH",
        failures,
    )

    model_inputs = model.get("inputs") if isinstance(model.get("inputs"), list) else []
    actual_paths = [str(item.get("path")) for item in model_inputs if isinstance(item, dict)]
    expected_paths = [path for path, _ in authority.inputs]
    inv["I04"] = _result(actual_paths == expected_paths and len(set(actual_paths)) == 6, "I04_INPUT_SET_MISMATCH", failures)
    actual_input_map = {str(item.get("path")): str(item.get("sha256")) for item in model_inputs if isinstance(item, dict)}
    inv["I05"] = _result(actual_input_map == dict(authority.inputs), "I05_INPUT_DIGEST_MISMATCH", failures)

    builder = model.get("builder") if isinstance(model.get("builder"), dict) else {}
    inv["I06"] = _result(builder.get("path") == authority.builder.path and builder.get("git_blob_sha") == authority.builder.git_blob_sha, "I06_BUILDER_IDENTITY_MISMATCH", failures)
    inv["I07"] = _result(q.get("canonical_snapshot_id") == authority.canonical_snapshot_id and model.get("canonical_snapshot_id") == authority.canonical_snapshot_id, "I07_SNAPSHOT_IDENTITY_MISMATCH", failures)
    inv["I08"] = _result(replay.passed is True, "I08_REPLAY_FAILED", failures)
    inv["I09"] = _result(
        replay.output_identity == authority.output.identity
        and replay.output_sha256 == authority.output.sha256
        and replay.output_size_bytes == authority.output.size_bytes
        and replay.generated_at == authority.output.generated_at,
        "I09_OUTPUT_INTEGRITY_MISMATCH",
        failures,
    )

    model_output = model.get("output") if isinstance(model.get("output"), dict) else {}
    receipt_verification = mr.get("verification") if isinstance(mr.get("verification"), dict) else {}
    model_verification = model.get("verification") if isinstance(model.get("verification"), dict) else {}
    coherent = (
        model.get("model_generation_id") == authority.model_generation_id == mr.get("model_generation_id")
        and model_output.get("generation_id_inside_artifact") == authority.output.generation_id_inside_artifact == mr.get("generation_id_inside_artifact")
        and model_output.get("identity") == mr.get("output_file") == authority.output.identity
        and model_output.get("sha256") == mr.get("output_sha256") == authority.output.sha256
        and model_output.get("size_bytes") == mr.get("output_size_bytes") == authority.output.size_bytes
        and model.get("generated_at") == mr.get("generated_artifact_timestamp") == authority.output.generated_at
        and mr.get("input_sha256") == dict(authority.inputs)
        and mr.get("source_repository") == authority.source_repository
        and mr.get("builder_path") == authority.builder.path
        and model_verification.get("status") == receipt_verification.get("status") == "PASS"
    )
    inv["I10"] = _result(coherent, "I10_MANIFEST_RECEIPT_INCOHERENT", failures)

    source_ok = (
        reg.get("source_repository") == authority.source_repository
        and reg.get("source_commit") == authority.operational_commit
        and reg.get("source_path") == authority.registration.source_path
        and reg.get("source_git_blob_sha") == authority.registration.source_git_blob_sha
    )
    inv["I11"] = _result(source_ok, "I11_REGISTRATION_SOURCE_MISMATCH", failures)
    inv["I12"] = _result(_canonical(reg.get("examples")) == _canonical(list(authority.registration.examples)), "I12_REGISTRATION_EXAMPLES_MISMATCH", failures)

    qguards = q.get("epistemic_guards")
    rguards = reg.get("epistemic_guard")
    qkeys = {"new_measurement_allowed", "nd_promotion_allowed", "derived_promotable_to_doc", "unsourced_interval_allowed"}
    rkeys = {"residual_is_new_measurement", "residual_promotable_to_DOC", "residual_promotable_to_MIS", "unsourced_plus_minus_interval_allowed"}
    inv["I13"] = _result(_false_exact(qguards, qkeys) and _false_exact(rguards, rkeys), "I13_EPISTEMIC_GUARD_VIOLATION", failures)

    matrix_ids = [row.get("test_id") for row in matrix]
    matrix_ok = tuple(matrix_ids) == EXPECTED_IDS and len(set(matrix_ids)) == 11 and all(row.get("status") == "PASS" and row.get("evidence_id") == row.get("test_id") for row in matrix)
    inv["I14"] = _result(matrix_ok, "I14_GATE_MATRIX_INVALID", failures)

    evidence = index.get("evidence") if isinstance(index.get("evidence"), dict) else {}
    expected_evidence = dict(authority.evidence_bindings)
    evidence_ok = evidence == expected_evidence
    if evidence_ok:
        for key in EXPECTED_IDS:
            path = expected_evidence[key]
            try:
                if not reader.read_text(path).strip():
                    evidence_ok = False
                    break
            except ValueError:
                evidence_ok = False
                break
    inv["I15"] = _result(evidence_ok, "I15_EVIDENCE_INVALID", failures)

    structured_json = (q, index, reg, model, mr)
    boundary_ok = (
        all(_boundary_claims_safe(document) for document in structured_json)
        and _false_exact(q.get("authority_boundary"), BOUNDARY_KEYS)
        and mr.get("engineering_result") is False
    )
    inv["I16"] = _result(boundary_ok, "I16_AUTHORITY_BOUNDARY_VIOLATION", failures)
    inv["I17"] = _result(q.get("cew_fem_01_required") is True and q.get("cew_fem_chain") == "ModelGeneration → SolverRun → Result → Verification → Receipt", "I17_CEW_FEM_SEPARATION_VIOLATION", failures)

    if q.get("verification_status") != "PASS":
        failures.append("QUALIFICATION_VERIFICATION_NOT_PASS")
    return _receipt(authority, replay, control_plane, gate_core, candidate, qualified_at, digest, inv, failures)


def _receipt(authority, replay, control_plane, gate_core, candidate, qualified_at, digest, inv, failures):
    qualified = not failures and all(value is InvariantResult.PASS for value in inv.values())
    return QualificationReceipt(
        schema_id="CEW_QUALIFICATION_RECEIPT",
        schema_version=1,
        qualified_at=qualified_at,
        control_plane=control_plane,
        gate_core=gate_core,
        authority=AuthorityIdentity(authority.authority_id, authority.source_sha256),
        candidate=candidate,
        operational_authority=OperationalIdentity(authority.operational_commit),
        qualification_bundle_sha256=digest,
        replay={
            "output_identity": replay.output_identity,
            "output_sha256": replay.output_sha256,
            "output_size_bytes": replay.output_size_bytes,
            "historical_generated_at": replay.generated_at,
        },
        invariants=inv,
        failure_codes=tuple(failures),
        authority_boundary=dict(authority.authority_boundary),
        cew_fem_01_required=True,
        qualified=qualified,
    )
