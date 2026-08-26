from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRAINING_SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS graphic_training_examples(
 id TEXT PRIMARY KEY,
 observation_id TEXT NOT NULL,
 candidate_fingerprint TEXT NOT NULL,
 source_version_id TEXT NOT NULL,
 source_sha256 TEXT NOT NULL,
 generation_id TEXT NOT NULL,
 page INTEGER NOT NULL,
 x0 REAL,
 y0 REAL,
 x1 REAL,
 y1 REAL,
 observation_kind TEXT NOT NULL,
 value_text TEXT,
 meaning TEXT NOT NULL,
 verdict TEXT NOT NULL CHECK(verdict IN ('POSITIVE','NEGATIVE','UNCERTAIN')),
 feature_signature TEXT NOT NULL,
 context_json TEXT NOT NULL,
 reviewer TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(candidate_fingerprint,meaning,reviewer)
);
CREATE INDEX IF NOT EXISTS idx_graphic_training_meaning ON graphic_training_examples(meaning,verdict);
CREATE INDEX IF NOT EXISTS idx_graphic_training_feature ON graphic_training_examples(feature_signature);
CREATE INDEX IF NOT EXISTS idx_graphic_training_candidate ON graphic_training_examples(candidate_fingerprint);
CREATE TABLE IF NOT EXISTS graphic_meaning_proposals(
 id TEXT PRIMARY KEY,
 observation_id TEXT NOT NULL,
 candidate_fingerprint TEXT NOT NULL,
 source_sha256 TEXT NOT NULL,
 meaning TEXT NOT NULL,
 calibrated_score REAL NOT NULL,
 decisive_support REAL NOT NULL,
 positive_weight REAL NOT NULL,
 negative_weight REAL NOT NULL,
 uncertain_weight REAL NOT NULL,
 calibration_method TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('PROPOSED','HUMAN_VALIDATED','HUMAN_REJECTED')),
 reviewer TEXT,
 rationale TEXT,
 created_at TEXT NOT NULL,
 reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_graphic_proposal_obs ON graphic_meaning_proposals(observation_id,state);
CREATE INDEX IF NOT EXISTS idx_graphic_proposal_candidate ON graphic_meaning_proposals(candidate_fingerprint,state);
'''

CALIBRATION_METHOD = 'BETA_1_1_WITH_UNCERTAINTY_DAMPING_V1'
CANDIDATE_FINGERPRINT_VERSION = 'CEW-GRAPHIC-CANDIDATE-v1'


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.executescript(TRAINING_SCHEMA)
    return c


def canonical_context(context: dict[str, Any]) -> str:
    return json.dumps(context, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def normalized_text(value: str | None) -> str:
    return ' '.join((value or '').strip().upper().split())


def _stable_number(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def candidate_fingerprint(row: sqlite3.Row | dict[str, Any]) -> str:
    payload = {
        'version': CANDIDATE_FINGERPRINT_VERSION,
        'source_sha256': row['source_sha256'],
        'page': int(row['page']),
        'bbox_native': [_stable_number(row[k]) for k in ('x0', 'y0', 'x1', 'y1')],
        'kind': row['kind'],
        'value_text': normalized_text(row['value_text']),
        'detector': row['detector'],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return 'GCFP-' + hashlib.sha256(raw).hexdigest()


def feature_signature(kind: str, value_text: str | None, context: dict[str, Any]) -> str:
    stable_context = {
        k: context[k]
        for k in ('drawing_type', 'document_family', 'neighbourhood_class', 'line_family', 'symbol_family')
        if k in context
    }
    return canonical_context({
        'kind': kind,
        'text': normalized_text(value_text),
        'context': stable_context,
    })


def current_observation(c: sqlite3.Connection, observation_id: str) -> sqlite3.Row:
    row = c.execute('''
        SELECT o.*, b.generation_id, sv.sha256 AS source_sha256
        FROM observations o
        JOIN source_versions sv ON sv.id=o.source_version_id
        JOIN observation_generation_bindings b ON b.observation_id=o.id
        JOIN processing_generations g ON g.id=b.generation_id AND g.state='SUCCEEDED'
        JOIN source_version_processing sp
          ON sp.source_version_id=o.source_version_id
         AND sp.current_generation_id=b.generation_id
        WHERE o.id=?
    ''', (observation_id,)).fetchone()
    if not row:
        raise ValueError('observation is unknown, stale, or not bound to the current successful generation')
    return row


def label_example(
    db: Path,
    observation_id: str,
    meaning: str,
    verdict: str,
    reviewer: str,
    context: dict[str, Any],
) -> str:
    if verdict not in {'POSITIVE', 'NEGATIVE', 'UNCERTAIN'}:
        raise ValueError('verdict must be POSITIVE, NEGATIVE or UNCERTAIN')
    if not meaning.strip() or not reviewer.strip():
        raise ValueError('meaning and reviewer are required')
    with connect(db) as c:
        row = current_observation(c, observation_id)
        eid = 'GT-' + uuid.uuid4().hex[:12]
        sig = feature_signature(row['kind'], row['value_text'], context)
        fp = candidate_fingerprint(row)
        c.execute('''
            INSERT OR REPLACE INTO graphic_training_examples(
              id,observation_id,candidate_fingerprint,source_version_id,source_sha256,generation_id,
              page,x0,y0,x1,y1,observation_kind,value_text,meaning,verdict,
              feature_signature,context_json,reviewer,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            eid, observation_id, fp, row['source_version_id'], row['source_sha256'], row['generation_id'], row['page'],
            row['x0'], row['y0'], row['x1'], row['y1'], row['kind'], row['value_text'],
            meaning.strip(), verdict, sig, canonical_context(context), reviewer.strip(), now()
        ))
        c.commit()
    return eid


def _weight(example: sqlite3.Row, candidate_kind: str, candidate_signature: str) -> float:
    if example['feature_signature'] == candidate_signature:
        return 3.0
    if example['observation_kind'] == candidate_kind:
        return 1.0
    return 0.5


def score_meaning(db: Path, observation_id: str, meaning: str, context: dict[str, Any]) -> dict[str, Any]:
    with connect(db) as c:
        candidate = current_observation(c, observation_id)
        sig = feature_signature(candidate['kind'], candidate['value_text'], context)
        examples = c.execute(
            'SELECT * FROM graphic_training_examples WHERE meaning=? ORDER BY created_at',
            (meaning,),
        ).fetchall()

    positive = negative = uncertain = 0.0
    for example in examples:
        weight = _weight(example, candidate['kind'], sig)
        if example['verdict'] == 'POSITIVE':
            positive += weight
        elif example['verdict'] == 'NEGATIVE':
            negative += weight
        else:
            uncertain += weight

    decisive = positive + negative
    raw = (1.0 + positive) / (2.0 + decisive)
    certainty = decisive / (decisive + uncertain + 1.0) if (decisive + uncertain) else 0.0
    calibrated = 0.5 + (raw - 0.5) * certainty
    return {
        'observation_id': observation_id,
        'candidate_fingerprint': candidate_fingerprint(candidate),
        'source_sha256': candidate['source_sha256'],
        'meaning': meaning,
        'calibrated_score': round(calibrated, 6),
        'decisive_support': round(decisive, 6),
        'positive_weight': round(positive, 6),
        'negative_weight': round(negative, 6),
        'uncertain_weight': round(uncertain, 6),
        'calibration_method': CALIBRATION_METHOD,
        'semantic_authority': 'NONE_UNTIL_HUMAN_VALIDATION',
    }


def known_meanings(db: Path) -> list[str]:
    with connect(db) as c:
        return [r['meaning'] for r in c.execute('SELECT DISTINCT meaning FROM graphic_training_examples ORDER BY meaning')]


def propose_meanings(
    db: Path,
    observation_id: str,
    context: dict[str, Any],
    min_decisive_support: float = 1.0,
    limit: int = 5,
) -> list[dict[str, Any]]:
    scored = [score_meaning(db, observation_id, meaning, context) for meaning in known_meanings(db)]
    scored = [x for x in scored if x['decisive_support'] >= min_decisive_support]
    scored.sort(key=lambda x: (-x['calibrated_score'], -x['decisive_support'], x['meaning']))
    return scored[:limit]


def persist_proposal(db: Path, scored: dict[str, Any]) -> str:
    pid = 'GPROP-' + uuid.uuid4().hex[:12]
    with connect(db) as c:
        c.execute('''
            INSERT INTO graphic_meaning_proposals(
              id,observation_id,candidate_fingerprint,source_sha256,meaning,calibrated_score,decisive_support,
              positive_weight,negative_weight,uncertain_weight,calibration_method,state,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,'PROPOSED',?)
        ''', (
            pid, scored['observation_id'], scored['candidate_fingerprint'], scored['source_sha256'],
            scored['meaning'], scored['calibrated_score'], scored['decisive_support'], scored['positive_weight'],
            scored['negative_weight'], scored['uncertain_weight'], scored['calibration_method'], now()
        ))
        c.commit()
    return pid


def review_proposal(db: Path, proposal_id: str, decision: str, reviewer: str, rationale: str) -> None:
    if decision not in {'VALIDATE', 'REJECT'}:
        raise ValueError('decision must be VALIDATE or REJECT')
    if not reviewer.strip() or not rationale.strip():
        raise ValueError('reviewer and rationale are required')
    target = 'HUMAN_VALIDATED' if decision == 'VALIDATE' else 'HUMAN_REJECTED'
    with connect(db) as c:
        cur = c.execute('''
            UPDATE graphic_meaning_proposals
               SET state=?,reviewer=?,rationale=?,reviewed_at=?
             WHERE id=? AND state='PROPOSED'
        ''', (target, reviewer.strip(), rationale.strip(), now(), proposal_id))
        if cur.rowcount != 1:
            raise ValueError('proposal is unknown or already reviewed')
        c.commit()


def build_review_package(db: Path, limit: int = 12) -> dict[str, Any]:
    with connect(db) as c:
        rows = c.execute('''
            SELECT o.*, b.generation_id, sv.sha256 AS source_sha256
            FROM observations o
            JOIN source_versions sv ON sv.id=o.source_version_id
            JOIN observation_generation_bindings b ON b.observation_id=o.id
            JOIN processing_generations g ON g.id=b.generation_id AND g.state='SUCCEEDED'
            JOIN source_version_processing sp
              ON sp.source_version_id=o.source_version_id
             AND sp.current_generation_id=b.generation_id
            WHERE o.state IN ('CANDIDATE','SUPPORTED')
            ORDER BY
              o.kind,
              o.confidence DESC,
              o.page,
              o.x0,
              o.y0,
              o.x1,
              o.y1,
              COALESCE(o.value_text,''),
              o.detector
            LIMIT ?
        ''', (limit,)).fetchall()

    candidates = []
    for row in rows:
        context = {'drawing_type': 'UNKNOWN_REQUIRES_REVIEW'}
        suggestions = propose_meanings(db, row['id'], context, min_decisive_support=1.0, limit=3)
        candidates.append({
            'candidate_fingerprint': candidate_fingerprint(row),
            'observation_id': row['id'],
            'source_version_id': row['source_version_id'],
            'source_sha256': row['source_sha256'],
            'generation_id': row['generation_id'],
            'page': row['page'],
            'bbox_native': [row['x0'], row['y0'], row['x1'], row['y1']],
            'kind': row['kind'],
            'value_text': row['value_text'],
            'confidence': row['confidence'],
            'detector': row['detector'],
            'semantic_state': 'PROPOSALS_REQUIRE_HUMAN_REVIEW' if suggestions else 'UNASSIGNED_REQUIRES_HUMAN_LABEL',
            'suggested_meanings': suggestions,
            'allowed_training_verdicts': ['POSITIVE', 'NEGATIVE', 'UNCERTAIN'],
        })

    package_identity = {
        'fingerprint_version': CANDIDATE_FINGERPRINT_VERSION,
        'candidate_fingerprints': [c['candidate_fingerprint'] for c in candidates],
    }
    package_fingerprint = hashlib.sha256(
        json.dumps(package_identity, sort_keys=True, separators=(',', ':')).encode('utf-8')
    ).hexdigest()
    return {
        'schema_version': '0.2.0',
        'work_item_id': 'DOC-003',
        'status': 'BLOCKED_HUMAN_DECISION',
        'decision_required': 'Assign a candidate meaning and label it POSITIVE, NEGATIVE or UNCERTAIN; semantic validation remains an explicit human action.',
        'candidate_fingerprint_version': CANDIDATE_FINGERPRINT_VERSION,
        'review_package_fingerprint': 'sha256:' + package_fingerprint,
        'candidate_count': len(candidates),
        'candidates': candidates,
        'canonical_promotion': 'DISABLED',
        'semantic_promotion': 'HUMAN_ONLY',
        'training_preserves': [
            'candidate_fingerprint', 'source_sha256', 'source_version_id', 'generation_id',
            'page', 'native_bbox', 'context', 'counterexamples'
        ],
    }


def stats(db: Path) -> dict[str, Any]:
    with connect(db) as c:
        labels = {r['verdict']: r['n'] for r in c.execute('SELECT verdict,COUNT(*) n FROM graphic_training_examples GROUP BY verdict')}
        proposals = {r['state']: r['n'] for r in c.execute('SELECT state,COUNT(*) n FROM graphic_meaning_proposals GROUP BY state')}
    return {'labels': labels, 'proposals': proposals, 'canonical_promotion': 'DISABLED'}


def main() -> None:
    p = argparse.ArgumentParser(description='CEW graphic convention active-learning loop')
    p.add_argument('--db', type=Path, required=True)
    sub = p.add_subparsers(dest='cmd', required=True)

    x = sub.add_parser('package')
    x.add_argument('--limit', type=int, default=12)
    x.add_argument('--output', type=Path)

    x = sub.add_parser('label')
    x.add_argument('observation_id')
    x.add_argument('--meaning', required=True)
    x.add_argument('--verdict', choices=['POSITIVE', 'NEGATIVE', 'UNCERTAIN'], required=True)
    x.add_argument('--reviewer', required=True)
    x.add_argument('--context', default='{}')

    x = sub.add_parser('propose')
    x.add_argument('observation_id')
    x.add_argument('--context', default='{}')
    x.add_argument('--min-decisive-support', type=float, default=1.0)

    x = sub.add_parser('review')
    x.add_argument('proposal_id')
    x.add_argument('--decision', choices=['VALIDATE', 'REJECT'], required=True)
    x.add_argument('--reviewer', required=True)
    x.add_argument('--rationale', required=True)

    sub.add_parser('stats')
    a = p.parse_args()

    if a.cmd == 'package':
        payload = build_review_package(a.db, a.limit)
        text = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(text, encoding='utf-8')
        print(text, end='')
    elif a.cmd == 'label':
        print(label_example(a.db, a.observation_id, a.meaning, a.verdict, a.reviewer, json.loads(a.context)))
    elif a.cmd == 'propose':
        print(json.dumps(propose_meanings(a.db, a.observation_id, json.loads(a.context), a.min_decisive_support), indent=2, ensure_ascii=False))
    elif a.cmd == 'review':
        review_proposal(a.db, a.proposal_id, a.decision, a.reviewer, a.rationale)
        print('OK')
    else:
        print(json.dumps(stats(a.db), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
