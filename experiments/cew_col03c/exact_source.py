from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from experiments.cew_col03c.cross_document import (
    QUALIFIED_COL03B_SHA,
    build_cross_document_bundles,
    build_cross_document_closure,
    build_cross_document_reconciliation,
)
from experiments.cew_col03c.derived_reference_quality import (
    FROZEN_ARCHIVE_COMMIT,
    audit_candidate_matrix_reference,
    audit_topology_reference,
    materialize_reference_descriptor,
)
from experiments.cew_col03c.historical_inventory import (
    classify_historical_artifact,
    parse_historical_inventory,
)
from experiments.cew_col03c.predecessor import validate_col03b_predecessor
from experiments.cew_col03c.source_materialization import (
    TAV07_SOURCE,
    build_pdf_source_metadata,
)
from experiments.cew_col03c.tav07_observations import (
    build_tav07_observation_inventory,
    normalize_tav07_text_observations,
)


HISTORICAL_REGISTRATION_COMMIT = "643dc8934ec0c8ac37613ec2880cf9e02f5a9df2"
HISTORICAL_INVENTORY_PATH = "archive/ARTEFATTI_STORICI.md"
DERIVED_REFERENCE_PATHS = {
    "nodes": "data/canonical/tav5_topology_nodes_57.csv",
    "connections": "data/canonical/tav5_topology_connections_v07.csv",
    "candidate_matrix": "data/canonical/telaio5_tav5_candidate_matrix_v1.csv",
}
REQUIRED_HISTORICAL_ARTIFACTS = (
    "TAV7_PILASTRI.dxf",
    "ABACO_TOPOLOGICO_TAV5_v11.csv",
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
    "MATRICE_PILASTRI_27x5_v22.csv",
    "TABELLA_CORRISPONDENZE_TRAVI_v25.csv",
)


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _pretty_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_show_bytes(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _parse_csv_bytes(data: bytes, *, delimiter: str) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("derived reference CSV has no header")
    return [
        {str(key): str(value or "") for key, value in row.items()}
        for row in reader
    ]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_tav07(temp_root: Path) -> tuple[Path, dict[str, Any]]:
    data = _git_show_bytes(FROZEN_ARCHIVE_COMMIT, TAV07_SOURCE["path"])
    path = temp_root / "cew-col03c-tavola7.pdf"
    path.write_bytes(data)
    return path, build_pdf_source_metadata(path, TAV07_SOURCE)


def _tesseract_version() -> str:
    completed = subprocess.run(
        ["tesseract", "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout.splitlines()[0].strip()


def _ocr_pdf(
    path: Path,
    source_metadata: dict[str, Any],
    temp_root: Path,
) -> tuple[list[dict[str, Any]], str]:
    import pypdfium2 as pdfium

    version = _tesseract_version()
    raw: list[dict[str, Any]] = []
    document = pdfium.PdfDocument(str(path))
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            try:
                bitmap = page.render(scale=300.0 / 72.0, grayscale=True)
                try:
                    image = bitmap.to_pil().convert("L")
                finally:
                    bitmap.close()
            finally:
                page.close()

            image_path = temp_root / f"cew-col03c-tav07-page-{page_index:03d}.png"
            image.save(image_path, format="PNG")
            width, height = image.size
            completed = subprocess.run(
                ["tesseract", str(image_path), "stdout", "--psm", "11", "tsv"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            reader = csv.DictReader(io.StringIO(completed.stdout), delimiter="\t")
            for row in reader:
                text = str(row.get("text") or "").strip()
                if not text:
                    continue
                try:
                    left = int(row.get("left") or 0)
                    top = int(row.get("top") or 0)
                    token_width = int(row.get("width") or 0)
                    token_height = int(row.get("height") or 0)
                    confidence = float(row.get("conf") or -1)
                except ValueError:
                    continue
                if token_width <= 0 or token_height <= 0 or width <= 0 or height <= 0:
                    continue
                raw.append(
                    {
                        "page_index": page_index,
                        "raw_text": text,
                        "bbox": {
                            "x": left / width,
                            "y": top / height,
                            "width": token_width / width,
                            "height": token_height / height,
                        },
                        "confidence": confidence,
                    }
                )
    finally:
        document.close()

    return (
        normalize_tav07_text_observations(raw, source_metadata=source_metadata),
        version,
    )


def _historical_artifacts() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inventory_bytes = _git_show_bytes(
        HISTORICAL_REGISTRATION_COMMIT,
        HISTORICAL_INVENTORY_PATH,
    )
    parsed = parse_historical_inventory(
        inventory_bytes.decode("utf-8"),
        source_ref=(
            f"commit:{HISTORICAL_REGISTRATION_COMMIT}:"
            f"{HISTORICAL_INVENTORY_PATH}"
        ),
    )
    by_name = {str(row.get("artifact_name") or ""): row for row in parsed}
    classified: list[dict[str, Any]] = []
    for name in REQUIRED_HISTORICAL_ARTIFACTS:
        record = (
            deepcopy(by_name[name])
            if name in by_name
            else {
                "artifact_name": name,
                "inventory_source_ref": (
                    f"commit:{HISTORICAL_REGISTRATION_COMMIT}:"
                    f"{HISTORICAL_INVENTORY_PATH}"
                ),
                "historical_package_refs": [],
                "inventory_notes": [],
                "authority": "REFERENCE_ONLY",
            }
        )
        classified.append(
            classify_historical_artifact(
                record,
                materialized_path=None,
                sha256=None,
            )
        )

    manifest = {
        "registration_commit": HISTORICAL_REGISTRATION_COMMIT,
        "inventory_path": HISTORICAL_INVENTORY_PATH,
        "inventory_sha256": _sha256(inventory_bytes),
        "required_artifact_names": sorted(REQUIRED_HISTORICAL_ARTIFACTS),
        "required_artifact_count": len(REQUIRED_HISTORICAL_ARTIFACTS),
    }
    return (
        sorted(classified, key=lambda row: str(row["artifact_name"])),
        manifest,
    )


def _derived_reference_quality() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    node_bytes = _git_show_bytes(
        FROZEN_ARCHIVE_COMMIT,
        DERIVED_REFERENCE_PATHS["nodes"],
    )
    connection_bytes = _git_show_bytes(
        FROZEN_ARCHIVE_COMMIT,
        DERIVED_REFERENCE_PATHS["connections"],
    )
    matrix_bytes = _git_show_bytes(
        FROZEN_ARCHIVE_COMMIT,
        DERIVED_REFERENCE_PATHS["candidate_matrix"],
    )
    nodes = _parse_csv_bytes(node_bytes, delimiter=";")
    connections = _parse_csv_bytes(connection_bytes, delimiter=";")
    matrix = _parse_csv_bytes(matrix_bytes, delimiter=",")

    node_descriptor = materialize_reference_descriptor(
        path=DERIVED_REFERENCE_PATHS["nodes"],
        archive_commit=FROZEN_ARCHIVE_COMMIT,
        bytes_sha256=_sha256(node_bytes),
        rows=nodes,
    )
    connection_descriptor = materialize_reference_descriptor(
        path=DERIVED_REFERENCE_PATHS["connections"],
        archive_commit=FROZEN_ARCHIVE_COMMIT,
        bytes_sha256=_sha256(connection_bytes),
        rows=connections,
    )
    matrix_descriptor = materialize_reference_descriptor(
        path=DERIVED_REFERENCE_PATHS["candidate_matrix"],
        archive_commit=FROZEN_ARCHIVE_COMMIT,
        bytes_sha256=_sha256(matrix_bytes),
        rows=matrix,
    )

    topology = audit_topology_reference(
        nodes=nodes,
        connections=connections,
        provenance={
            "node_source": node_descriptor,
            "connection_source": connection_descriptor,
        },
        historical_inventory_claim={
            "node_count": 57,
            "connection_count": 38,
            "component_count": 10,
        },
    )
    candidate_matrix = audit_candidate_matrix_reference(
        rows=matrix,
        provenance=matrix_descriptor,
    )
    quality = {
        "schema": "CEW_COL03C_DERIVED_REFERENCE_QUALITY_v1",
        "topology_reference": topology,
        "candidate_matrix_reference": candidate_matrix,
    }
    return quality, [
        node_descriptor,
        connection_descriptor,
        matrix_descriptor,
    ]


def write_col03c_artifacts(
    output_dir: Path,
    *,
    source_manifest: dict[str, Any],
    quality: dict[str, Any],
    ledger: dict[str, Any],
    reconciliation: dict[str, Any],
    closure: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "source-materialization-manifest.json": deepcopy(source_manifest),
        "derived-reference-quality.json": deepcopy(quality),
        "cross-document-evidence-ledger.json": deepcopy(ledger),
        "cross-document-reconciliation.json": deepcopy(reconciliation),
        "cross-document-evidence-closure.json": deepcopy(closure),
    }
    digests: dict[str, str] = {}
    for name, payload in sorted(payloads.items()):
        data = _pretty_bytes(payload)
        (output_dir / name).write_bytes(data)
        digests[name] = _sha256(data)
    return digests


def _canonical_observation_inventory(
    observation_inventory: dict[str, Any],
) -> dict[str, Any]:
    result = deepcopy(observation_inventory)
    observations = result.get("observations")
    if not isinstance(observations, list):
        raise ValueError("COL-03C observation inventory lacks observations")
    result["observations"] = sorted(
        (deepcopy(row) for row in observations),
        key=lambda row: str(row.get("observation_id") or ""),
    )
    return result


def _build_payloads(
    *,
    predecessor_occurrences: list[dict[str, Any]],
    tav07_metadata: dict[str, Any],
    observation_inventory: dict[str, Any],
    historical_artifacts: list[dict[str, Any]],
    historical_manifest: dict[str, Any],
    quality: dict[str, Any],
    derived_descriptors: list[dict[str, Any]],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    canonical_inventory = _canonical_observation_inventory(observation_inventory)
    canonical_history = sorted(
        (deepcopy(row) for row in historical_artifacts),
        key=lambda row: str(row.get("artifact_name") or ""),
    )
    canonical_descriptors = sorted(
        (deepcopy(row) for row in derived_descriptors),
        key=lambda row: str(row.get("path") or ""),
    )

    bundles = build_cross_document_bundles(
        predecessor_occurrences=predecessor_occurrences,
        tav07_source=tav07_metadata,
        tav07_observations=canonical_inventory["observations"],
        historical_artifacts=canonical_history,
        derived_reference_quality=quality,
    )
    reconciliation = build_cross_document_reconciliation(
        bundles=bundles,
        historical_artifacts=canonical_history,
        derived_reference_quality=quality,
        tav07_source=tav07_metadata,
    )
    closure = build_cross_document_closure(
        bundles=bundles,
        reconciliation=reconciliation,
        qualified_col03b_sha=QUALIFIED_COL03B_SHA,
    )

    source_manifest = {
        "schema": "CEW_COL03C_SOURCE_MATERIALIZATION_MANIFEST_v1",
        "qualified_col03b_sha": QUALIFIED_COL03B_SHA,
        "primary_sources": [deepcopy(tav07_metadata)],
        "historical_inventory": deepcopy(historical_manifest),
        "historical_derived_artifacts": canonical_history,
        "derived_reference_sources": canonical_descriptors,
        "tav07_observation_inventory": {
            key: deepcopy(value)
            for key, value in canonical_inventory.items()
            if key != "observations"
        },
    }
    ledger = {
        "schema": "CEW_COL03C_CROSS_DOCUMENT_EVIDENCE_LEDGER_v1",
        "occurrence_count": len(bundles),
        "occurrences": bundles,
        "tav07_observation_inventory": canonical_inventory,
    }
    reconciliation = {
        "schema": "CEW_COL03C_CROSS_DOCUMENT_RECONCILIATION_v1",
        **reconciliation,
    }
    closure = {
        "schema": "CEW_COL03C_CROSS_DOCUMENT_EVIDENCE_CLOSURE_v1",
        **closure,
    }
    return source_manifest, deepcopy(quality), ledger, reconciliation, closure


def main() -> None:
    predecessor_root = Path("evidence/cew-col03b")
    ledger_b = _load_json(
        predecessor_root / "documentary-identity-evidence-ledger.json"
    )
    reconciliation_b = _load_json(
        predecessor_root / "documentary-identity-reconciliation.json"
    )
    closure_b = _load_json(
        predecessor_root / "documentary-identity-evidence-closure.json"
    )
    predecessor_occurrences = validate_col03b_predecessor(
        ledger=ledger_b,
        reconciliation=reconciliation_b,
        closure=closure_b,
        expected_sha=QUALIFIED_COL03B_SHA,
    )

    temp_root = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "cew-col03c"
    temp_root.mkdir(parents=True, exist_ok=True)
    tav07_path, tav07_metadata = _materialize_tav07(temp_root)
    observations_a, tesseract_version_a = _ocr_pdf(
        tav07_path,
        tav07_metadata,
        temp_root,
    )
    observations_b, tesseract_version_b = _ocr_pdf(
        tav07_path,
        tav07_metadata,
        temp_root,
    )
    if (
        tesseract_version_a != tesseract_version_b
        or _canonical_bytes(observations_a) != _canonical_bytes(observations_b)
    ):
        raise ValueError("COL-03C TAV.7 OCR replay is not deterministic")

    observation_inventory = build_tav07_observation_inventory(
        observations_a,
        extraction_method="TESSERACT_PSM11_300DPI",
        extraction_version=tesseract_version_a,
    )
    historical_artifacts, historical_manifest = _historical_artifacts()
    quality, derived_descriptors = _derived_reference_quality()

    payloads_a = _build_payloads(
        predecessor_occurrences=predecessor_occurrences,
        tav07_metadata=tav07_metadata,
        observation_inventory=observation_inventory,
        historical_artifacts=historical_artifacts,
        historical_manifest=historical_manifest,
        quality=quality,
        derived_descriptors=derived_descriptors,
    )
    payloads_b = _build_payloads(
        predecessor_occurrences=list(reversed(deepcopy(predecessor_occurrences))),
        tav07_metadata=deepcopy(tav07_metadata),
        observation_inventory={
            **deepcopy(observation_inventory),
            "observations": list(
                reversed(deepcopy(observation_inventory["observations"]))
            ),
        },
        historical_artifacts=list(reversed(deepcopy(historical_artifacts))),
        historical_manifest=deepcopy(historical_manifest),
        quality=deepcopy(quality),
        derived_descriptors=list(reversed(deepcopy(derived_descriptors))),
    )
    if any(
        _canonical_bytes(left) != _canonical_bytes(right)
        for left, right in zip(payloads_a, payloads_b)
    ):
        raise ValueError("COL-03C payload replay is not deterministic")

    source_manifest, quality_payload, ledger, reconciliation, closure = payloads_a
    if closure["available_cross_document_evidence_evaluated"] is not True:
        raise ValueError(
            f"COL-03C closure blocked: {closure['blocking_reasons']}"
        )

    digests = write_col03c_artifacts(
        Path("evidence/cew-col03c"),
        source_manifest=source_manifest,
        quality=quality_payload,
        ledger=ledger,
        reconciliation=reconciliation,
        closure=closure,
    )
    print(
        json.dumps(
            {
                "status": "CEW_COL03C_AVAILABLE_CROSS_DOCUMENT_EVIDENCE_EVALUATED",
                "occurrence_count": ledger["occurrence_count"],
                "tav07_observation_count": observation_inventory["observation_count"],
                "tav07_sha256": tav07_metadata["sha256"],
                "topology_identity_use_state": quality["topology_reference"][
                    "identity_use_state"
                ],
                "topology_unresolved_endpoint_count": len(
                    quality["topology_reference"]["unresolved_endpoint_ids"]
                ),
                "historical_derived_artifact_recovery_complete": closure[
                    "historical_derived_artifact_recovery_complete"
                ],
                "all_occurrences_cross_document_resolved": closure[
                    "all_occurrences_cross_document_resolved"
                ],
                "human_review_required": reconciliation["human_review_required"],
                "tesseract_version": tesseract_version_a,
                "digests": digests,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
