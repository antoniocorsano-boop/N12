from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"
RESOLVER_VERSION = "AFFINITY_ENSEMBLE_V1"
PACK_VERSION = "CEW-GRAPHIC-KNOWLEDGE-PACK-v1"

DIMENSION_WEIGHTS = {
    "discipline": 2.0,
    "document_family": 2.5,
    "drawing_type": 3.0,
    "structural_system": 2.0,
    "drafting_era": 1.5,
    "authoring_office": 4.0,
    "notation_family": 2.5,
    "country": 1.0,
    "language": 0.5,
    "source_modality": 0.5,
}

FAMILY_DIMENSIONS = (
    "discipline",
    "document_family",
    "drawing_type",
    "structural_system",
    "drafting_era",
    "authoring_office",
    "notation_family",
    "country",
    "language",
)

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS gkf_meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gkf_examples(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  source_sha256 TEXT NOT NULL,
  candidate_fingerprint TEXT NOT NULL,
  meaning TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK(verdict IN ('POSITIVE','NEGATIVE','UNCERTAIN')),
  context_json TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  reviewed_at TEXT NOT NULL,
  UNIQUE(project_id,candidate_fingerprint,meaning,reviewer)
);
CREATE INDEX IF NOT EXISTS idx_gkf_examples_meaning ON gkf_examples(meaning,verdict);
CREATE INDEX IF NOT EXISTS idx_gkf_examples_project ON gkf_examples(project_id);
CREATE TABLE IF NOT EXISTS gkf_generalizations(
  id TEXT PRIMARY KEY,
  meaning TEXT NOT NULL,
  tier TEXT NOT NULL CHECK(tier IN ('FAMILY','GLOBAL')),
  scope_json TEXT NOT NULL,
  distinct_projects INTEGER NOT NULL,
  family_count INTEGER NOT NULL,
  positive_count INTEGER NOT NULL,
  negative_count INTEGER NOT NULL,
  uncertain_count INTEGER NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('PROPOSED','HUMAN_VALIDATED','HUMAN_REJECTED','IMPORTED_SUPPORTED')),
  reviewer TEXT,
  rationale TEXT,
  created_at TEXT NOT NULL,
  reviewed_at TEXT,
  UNIQUE(meaning,tier,scope_json)
);
CREATE INDEX IF NOT EXISTS idx_gkf_generalizations_state ON gkf_generalizations(state,tier,meaning);
CREATE TABLE IF NOT EXISTS gkf_imports(
  pack_fingerprint TEXT PRIMARY KEY,
  imported_at TEXT NOT NULL,
  source_namespace TEXT,
  item_count INTEGER NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(sorted(normalize_value(v) for v in value))
    return " ".join(str(value).strip().upper().split())


def normalize_context(context: dict[str, Any]) -> dict[str, str]:
    return {
        key: normalize_value(context.get(key))
        for key in DIMENSION_WEIGHTS
        if normalize_value(context.get(key))
    }


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    current = c.execute("SELECT value FROM gkf_meta WHERE key='schema_version'").fetchone()
    if current and current["value"] > SCHEMA_VERSION:
        c.close()
        raise RuntimeError(f"future Graphic Knowledge schema {current['value']} is not supported by {SCHEMA_VERSION}")
    c.execute(
        "INSERT INTO gkf_meta(key,value) VALUES('schema_version',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (SCHEMA_VERSION,),
    )
    c.commit()
    return c


def context_affinity(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    t = normalize_context(target)
    s = normalize_context(source)
    denominator = sum(DIMENSION_WEIGHTS[k] for k in t)
    if denominator == 0:
        return {"score": 0.0, "matched": [], "mismatched": [], "missing": list(DIMENSION_WEIGHTS)}
    matched: list[str] = []
    mismatched: list[str] = []
    missing: list[str] = []
    score = 0.0
    for key, target_value in t.items():
        source_value = s.get(key)
        if not source_value:
            missing.append(key)
        elif source_value == target_value:
            matched.append(key)
            score += DIMENSION_WEIGHTS[key]
        else:
            mismatched.append(key)
    return {
        "score": round(score / denominator, 6),
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
    }


def family_scope(context: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_context(context)
    return {k: normalized[k] for k in FAMILY_DIMENSIONS if k in normalized}


def family_signature(context: dict[str, Any]) -> str:
    return canonical_json(family_scope(context))


def stable_id(prefix: str, payload: dict[str, Any]) -> str:
    raw = canonical_json(payload).encode("utf-8")
    return prefix + hashlib.sha256(raw).hexdigest()


def add_example(
    db: Path,
    *,
    project_id: str,
    source_sha256: str,
    candidate_fingerprint: str,
    meaning: str,
    verdict: str,
    context: dict[str, Any],
    reviewer: str,
    reviewed_at: str | None = None,
) -> str:
    if verdict not in {"POSITIVE", "NEGATIVE", "UNCERTAIN"}:
        raise ValueError("verdict must be POSITIVE, NEGATIVE or UNCERTAIN")
    if not all(x.strip() for x in (project_id, source_sha256, candidate_fingerprint, meaning, reviewer)):
        raise ValueError("project_id, source_sha256, candidate_fingerprint, meaning and reviewer are required")
    if len(source_sha256) != 64:
        raise ValueError("source_sha256 must be a SHA-256 hex digest")
    if not candidate_fingerprint.startswith("GCFP-"):
        raise ValueError("candidate_fingerprint must use the GCFP stable identity")
    context_json = canonical_json(normalize_context(context))
    payload = {
        "project_id": project_id,
        "source_sha256": source_sha256,
        "candidate_fingerprint": candidate_fingerprint,
        "meaning": meaning.strip(),
        "reviewer": reviewer.strip(),
    }
    eid = stable_id("GKE-", payload)
    with connect(db) as c:
        c.execute(
            """INSERT INTO gkf_examples(
                 id,project_id,source_sha256,candidate_fingerprint,meaning,verdict,context_json,reviewer,reviewed_at
               ) VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(project_id,candidate_fingerprint,meaning,reviewer)
               DO UPDATE SET verdict=excluded.verdict,context_json=excluded.context_json,reviewed_at=excluded.reviewed_at""",
            (
                eid,
                project_id.strip(),
                source_sha256.lower(),
                candidate_fingerprint,
                meaning.strip(),
                verdict,
                context_json,
                reviewer.strip(),
                reviewed_at or now(),
            ),
        )
        c.commit()
    return eid


def _example_weight(project_id: str, target_project: str, affinity: float) -> float:
    if project_id == target_project:
        return 3.0
    if affinity < 0.25:
        return 0.0
    return 0.5 + 1.5 * affinity


def _validated_generalization_weight(tier: str, state: str, affinity: float) -> float:
    trust = 1.0 if state == "HUMAN_VALIDATED" else 0.45
    if tier == "GLOBAL":
        return 1.25 * trust
    if affinity < 0.25:
        return 0.0
    return (1.0 + 2.0 * affinity) * trust


def resolve(
    db: Path,
    *,
    project_id: str,
    context: dict[str, Any],
    min_affinity: float = 0.25,
    limit: int = 5,
) -> dict[str, Any]:
    target_context = normalize_context(context)
    support: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "positive": 0.0,
            "negative": 0.0,
            "uncertain": 0.0,
            "local_positive": 0.0,
            "local_negative": 0.0,
            "contributors": [],
            "layers": set(),
        }
    )
    with connect(db) as c:
        examples = c.execute("SELECT * FROM gkf_examples ORDER BY reviewed_at,id").fetchall()
        generalizations = c.execute(
            "SELECT * FROM gkf_generalizations WHERE state IN ('HUMAN_VALIDATED','IMPORTED_SUPPORTED') ORDER BY tier,meaning,id"
        ).fetchall()

    for row in examples:
        source_context = json.loads(row["context_json"])
        affinity_info = context_affinity(target_context, source_context)
        affinity = affinity_info["score"]
        weight = _example_weight(row["project_id"], project_id, affinity)
        if row["project_id"] != project_id and affinity < min_affinity:
            continue
        if weight <= 0:
            continue
        item = support[row["meaning"]]
        layer = "LOCAL" if row["project_id"] == project_id else "AFFINE"
        item["layers"].add(layer)
        if row["verdict"] == "POSITIVE":
            item["positive"] += weight
            if layer == "LOCAL":
                item["local_positive"] += weight
        elif row["verdict"] == "NEGATIVE":
            item["negative"] += weight
            if layer == "LOCAL":
                item["local_negative"] += weight
        else:
            item["uncertain"] += weight
        item["contributors"].append(
            {
                "layer": layer,
                "project_id": row["project_id"],
                "candidate_fingerprint": row["candidate_fingerprint"],
                "verdict": row["verdict"],
                "affinity": affinity,
                "weight": round(weight, 6),
            }
        )

    for row in generalizations:
        scope = json.loads(row["scope_json"])
        affinity = 1.0 if row["tier"] == "GLOBAL" else context_affinity(target_context, scope)["score"]
        weight = _validated_generalization_weight(row["tier"], row["state"], affinity)
        if weight <= 0:
            continue
        item = support[row["meaning"]]
        item["positive"] += weight
        item["layers"].add(row["tier"])
        item["contributors"].append(
            {
                "layer": row["tier"],
                "generalization_id": row["id"],
                "state": row["state"],
                "affinity": round(affinity, 6),
                "weight": round(weight, 6),
            }
        )

    ranked: list[dict[str, Any]] = []
    for meaning, item in support.items():
        positive = item["positive"]
        negative = item["negative"]
        uncertain = item["uncertain"]
        decisive = positive + negative
        raw = (1.0 + positive) / (2.0 + decisive)
        certainty = decisive / (decisive + uncertain + 1.0) if (decisive + uncertain) else 0.0
        calibrated = 0.5 + (raw - 0.5) * certainty
        local_conflict = item["local_positive"] > 0 and item["local_negative"] > 0
        transferred_conflict = positive > 0 and negative > 0 and abs(calibrated - 0.5) <= 0.15
        contributors = sorted(
            item["contributors"], key=lambda x: (-float(x["weight"]), x.get("project_id", ""), x.get("generalization_id", ""))
        )
        ranked.append(
            {
                "meaning": meaning,
                "calibrated_score": round(calibrated, 6),
                "decisive_support": round(decisive, 6),
                "positive_weight": round(positive, 6),
                "negative_weight": round(negative, 6),
                "uncertain_weight": round(uncertain, 6),
                "layers": sorted(item["layers"]),
                "conflict": bool(local_conflict or transferred_conflict),
                "contributors": contributors[:8],
            }
        )
    ranked.sort(key=lambda x: (-x["calibrated_score"], -x["decisive_support"], x["meaning"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "resolver": RESOLVER_VERSION,
        "project_id": project_id,
        "context": target_context,
        "status": "CANDIDATES_AVAILABLE" if ranked else "NO_TRANSFERABLE_MEANING",
        "candidates": ranked[:limit],
        "semantic_authority": "NONE_UNTIL_PROJECT_HUMAN_VALIDATION",
        "combination_policy": "LOCAL + AFFINITY_WEIGHTED_PROJECTS + FAMILY + GLOBAL",
    }


def _counts(rows: list[sqlite3.Row]) -> tuple[int, int, int]:
    return (
        sum(1 for r in rows if r["verdict"] == "POSITIVE"),
        sum(1 for r in rows if r["verdict"] == "NEGATIVE"),
        sum(1 for r in rows if r["verdict"] == "UNCERTAIN"),
    )


def propose_generalizations(
    db: Path,
    *,
    min_family_projects: int = 2,
    min_global_projects: int = 3,
    max_negative_ratio: float = 0.25,
) -> list[str]:
    with connect(db) as c:
        rows = c.execute("SELECT * FROM gkf_examples ORDER BY meaning,project_id,id").fetchall()
        by_meaning: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in rows:
            by_meaning[row["meaning"]].append(row)

        created: list[str] = []
        for meaning, meaning_rows in by_meaning.items():
            family_groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
            for row in meaning_rows:
                family_groups[family_signature(json.loads(row["context_json"]))].append(row)

            eligible_family_signatures: list[str] = []
            for signature, family_rows in family_groups.items():
                positive, negative, uncertain = _counts(family_rows)
                projects = {r["project_id"] for r in family_rows if r["verdict"] == "POSITIVE"}
                ratio = negative / max(1, positive + negative)
                if positive and len(projects) >= min_family_projects and ratio <= max_negative_ratio:
                    scope = json.loads(signature)
                    pid = stable_id("GKG-", {"meaning": meaning, "tier": "FAMILY", "scope": scope})
                    c.execute(
                        """INSERT INTO gkf_generalizations(
                             id,meaning,tier,scope_json,distinct_projects,family_count,positive_count,negative_count,uncertain_count,state,created_at
                           ) VALUES(?,?,?,?,?,?,?,?,?,'PROPOSED',?)
                           ON CONFLICT(meaning,tier,scope_json) DO NOTHING""",
                        (pid, meaning, "FAMILY", signature, len(projects), 1, positive, negative, uncertain, now()),
                    )
                    if c.total_changes:
                        created.append(pid)
                    eligible_family_signatures.append(signature)

            positive_rows = [r for r in meaning_rows if r["verdict"] == "POSITIVE"]
            negative_rows = [r for r in meaning_rows if r["verdict"] == "NEGATIVE"]
            projects = {r["project_id"] for r in positive_rows}
            families = {family_signature(json.loads(r["context_json"])) for r in positive_rows}
            global_ratio = len(negative_rows) / max(1, len(positive_rows) + len(negative_rows))
            if len(projects) >= min_global_projects and len(families) >= 2 and global_ratio <= max_negative_ratio:
                pid = stable_id("GKG-", {"meaning": meaning, "tier": "GLOBAL", "scope": {}})
                c.execute(
                    """INSERT INTO gkf_generalizations(
                         id,meaning,tier,scope_json,distinct_projects,family_count,positive_count,negative_count,uncertain_count,state,created_at
                       ) VALUES(?,?,?,?,?,?,?,?,?,'PROPOSED',?)
                       ON CONFLICT(meaning,tier,scope_json) DO NOTHING""",
                    (
                        pid,
                        meaning,
                        "GLOBAL",
                        "{}",
                        len(projects),
                        len(families),
                        len(positive_rows),
                        len(negative_rows),
                        sum(1 for r in meaning_rows if r["verdict"] == "UNCERTAIN"),
                        now(),
                    ),
                )
                if c.total_changes:
                    created.append(pid)
        c.commit()
    return sorted(set(created))


def review_generalization(db: Path, proposal_id: str, decision: str, reviewer: str, rationale: str) -> None:
    if decision not in {"APPROVE", "REJECT"}:
        raise ValueError("decision must be APPROVE or REJECT")
    if not reviewer.strip() or not rationale.strip():
        raise ValueError("reviewer and rationale are required")
    target = "HUMAN_VALIDATED" if decision == "APPROVE" else "HUMAN_REJECTED"
    with connect(db) as c:
        cur = c.execute(
            """UPDATE gkf_generalizations
               SET state=?,reviewer=?,rationale=?,reviewed_at=?
               WHERE id=? AND state IN ('PROPOSED','IMPORTED_SUPPORTED')""",
            (target, reviewer.strip(), rationale.strip(), now(), proposal_id),
        )
        if cur.rowcount != 1:
            raise ValueError("generalization is unknown or already locally reviewed")
        c.commit()


def _pack_body(c: sqlite3.Connection, namespace: str) -> dict[str, Any]:
    examples = [dict(r) for r in c.execute("SELECT * FROM gkf_examples ORDER BY id")]
    validated = [
        dict(r)
        for r in c.execute(
            "SELECT * FROM gkf_generalizations WHERE state='HUMAN_VALIDATED' ORDER BY tier,meaning,id"
        )
    ]
    return {
        "pack_version": PACK_VERSION,
        "source_namespace": namespace,
        "examples": examples,
        "validated_generalizations": validated,
    }


def export_pack(db: Path, namespace: str) -> dict[str, Any]:
    with connect(db) as c:
        body = _pack_body(c, namespace)
    fingerprint = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
    return {**body, "pack_fingerprint": "sha256:" + fingerprint}


def import_pack(db: Path, pack: dict[str, Any]) -> dict[str, Any]:
    if pack.get("pack_version") != PACK_VERSION:
        raise ValueError("unsupported knowledge pack version")
    body = {k: pack[k] for k in ("pack_version", "source_namespace", "examples", "validated_generalizations")}
    expected = "sha256:" + hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
    if pack.get("pack_fingerprint") != expected:
        raise ValueError("knowledge pack fingerprint mismatch")
    with connect(db) as c:
        if c.execute("SELECT 1 FROM gkf_imports WHERE pack_fingerprint=?", (expected,)).fetchone():
            return {"status": "ALREADY_IMPORTED", "pack_fingerprint": expected, "imported": 0}
        imported = 0
        for row in pack["examples"]:
            c.execute(
                """INSERT OR IGNORE INTO gkf_examples(
                     id,project_id,source_sha256,candidate_fingerprint,meaning,verdict,context_json,reviewer,reviewed_at
                   ) VALUES(?,?,?,?,?,?,?,?,?)""",
                tuple(row[k] for k in ("id", "project_id", "source_sha256", "candidate_fingerprint", "meaning", "verdict", "context_json", "reviewer", "reviewed_at")),
            )
            imported += c.execute("SELECT changes()").fetchone()[0]
        for row in pack["validated_generalizations"]:
            imported_id = row["id"]
            c.execute(
                """INSERT INTO gkf_generalizations(
                     id,meaning,tier,scope_json,distinct_projects,family_count,positive_count,negative_count,uncertain_count,
                     state,reviewer,rationale,created_at,reviewed_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,'IMPORTED_SUPPORTED',?,?,?,?)
                   ON CONFLICT(meaning,tier,scope_json) DO NOTHING""",
                (
                    imported_id,
                    row["meaning"],
                    row["tier"],
                    row["scope_json"],
                    row["distinct_projects"],
                    row["family_count"],
                    row["positive_count"],
                    row["negative_count"],
                    row["uncertain_count"],
                    row.get("reviewer"),
                    row.get("rationale"),
                    row["created_at"],
                    row.get("reviewed_at"),
                ),
            )
            imported += c.execute("SELECT changes()").fetchone()[0]
        c.execute(
            "INSERT INTO gkf_imports(pack_fingerprint,imported_at,source_namespace,item_count) VALUES(?,?,?,?)",
            (expected, now(), pack.get("source_namespace"), imported),
        )
        c.commit()
    return {"status": "IMPORTED_SUPPORTED", "pack_fingerprint": expected, "imported": imported}


def status(db: Path) -> dict[str, Any]:
    with connect(db) as c:
        examples = c.execute("SELECT COUNT(*) n FROM gkf_examples").fetchone()["n"]
        projects = c.execute("SELECT COUNT(DISTINCT project_id) n FROM gkf_examples").fetchone()["n"]
        generalizations = {
            r["state"]: r["n"]
            for r in c.execute("SELECT state,COUNT(*) n FROM gkf_generalizations GROUP BY state")
        }
        imports = c.execute("SELECT COUNT(*) n FROM gkf_imports").fetchone()["n"]
    return {
        "schema_version": SCHEMA_VERSION,
        "examples": examples,
        "projects": projects,
        "generalization_states": generalizations,
        "imports": imports,
        "semantic_authority": "HUMAN_REVIEW_REQUIRED",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="CEW cross-project Graphic Knowledge Fabric")
    p.add_argument("--db", type=Path, required=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    x = sub.add_parser("resolve")
    x.add_argument("--project-id", required=True)
    x.add_argument("--context", required=True)
    x.add_argument("--limit", type=int, default=5)

    x = sub.add_parser("generalize")
    x.add_argument("--min-family-projects", type=int, default=2)
    x.add_argument("--min-global-projects", type=int, default=3)

    x = sub.add_parser("review-generalization")
    x.add_argument("proposal_id")
    x.add_argument("--decision", choices=["APPROVE", "REJECT"], required=True)
    x.add_argument("--reviewer", required=True)
    x.add_argument("--rationale", required=True)

    x = sub.add_parser("export-pack")
    x.add_argument("--namespace", required=True)
    x.add_argument("--output", type=Path, required=True)

    x = sub.add_parser("import-pack")
    x.add_argument("path", type=Path)

    sub.add_parser("status")
    a = p.parse_args()

    if a.cmd == "init":
        connect(a.db).close()
        print(json.dumps({"status": "PASS", "db": str(a.db), "schema_version": SCHEMA_VERSION}))
    elif a.cmd == "resolve":
        print(json.dumps(resolve(a.db, project_id=a.project_id, context=json.loads(a.context), limit=a.limit), indent=2))
    elif a.cmd == "generalize":
        print(json.dumps({"created": propose_generalizations(a.db, min_family_projects=a.min_family_projects, min_global_projects=a.min_global_projects)}))
    elif a.cmd == "review-generalization":
        review_generalization(a.db, a.proposal_id, a.decision, a.reviewer, a.rationale)
        print("OK")
    elif a.cmd == "export-pack":
        payload = export_pack(a.db, a.namespace)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(payload["pack_fingerprint"])
    elif a.cmd == "import-pack":
        print(json.dumps(import_pack(a.db, json.loads(a.path.read_text(encoding="utf-8"))), indent=2))
    elif a.cmd == "status":
        print(json.dumps(status(a.db), indent=2))


if __name__ == "__main__":
    main()
