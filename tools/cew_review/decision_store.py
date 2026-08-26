from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS review_cases(
 id TEXT PRIMARY KEY,
 title TEXT NOT NULL,
 question TEXT NOT NULL,
 candidate_summary TEXT NOT NULL,
 source_fingerprint TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('PENDING','APPROVED','CORRECTED','REJECTED','DEFERRED','STALE_REVIEW')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_evidence(
 case_id TEXT NOT NULL REFERENCES review_cases(id),
 evidence_id TEXT NOT NULL,
 label TEXT NOT NULL,
 summary TEXT NOT NULL,
 locator TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('SUPPORTING','COUNTER','CONTEXT')),
 PRIMARY KEY(case_id,evidence_id)
);
CREATE TABLE IF NOT EXISTS review_decisions(
 id TEXT PRIMARY KEY,
 case_id TEXT NOT NULL REFERENCES review_cases(id),
 decision TEXT NOT NULL CHECK(decision IN ('APPROVE','CORRECT','REJECT','DEFER')),
 reviewer TEXT NOT NULL,
 rationale TEXT NOT NULL,
 correction_json TEXT,
 source_fingerprint TEXT NOT NULL,
 decided_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_review_case_state ON review_cases(state);
CREATE INDEX IF NOT EXISTS idx_review_decision_case ON review_decisions(case_id,decided_at);
'''


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def create_case(path: Path, title: str, question: str, candidate_summary: str, source_fingerprint: str, evidence: list[dict[str, str]]) -> str:
    if not title.strip() or not question.strip() or not candidate_summary.strip():
        raise ValueError('human-facing title, question and candidate_summary are required')
    if not evidence:
        raise ValueError('review case requires evidence')
    cid = 'REV-' + uuid.uuid4().hex[:12]
    ts = now()
    with connect(path) as c:
        c.execute('INSERT INTO review_cases VALUES(?,?,?,?,?,?,?,?)',(cid,title,question,candidate_summary,source_fingerprint,'PENDING',ts,ts))
        for e in evidence:
            for k in ('evidence_id','label','summary','locator'):
                if not e.get(k): raise ValueError(f'evidence missing {k}')
            c.execute('INSERT INTO review_evidence VALUES(?,?,?,?,?,?)',(cid,e['evidence_id'],e['label'],e['summary'],e['locator'],e.get('role','SUPPORTING')))
        c.commit()
    return cid


def decision_state(decision: str) -> str:
    return {'APPROVE':'APPROVED','CORRECT':'CORRECTED','REJECT':'REJECTED','DEFER':'DEFERRED'}[decision]


def decide(path: Path, case_id: str, decision: str, reviewer: str, rationale: str, source_fingerprint: str, correction: dict[str, Any] | None = None) -> str:
    if decision not in {'APPROVE','CORRECT','REJECT','DEFER'}:
        raise ValueError('invalid decision')
    if not reviewer.strip() or not rationale.strip():
        raise ValueError('reviewer and rationale are required')
    if decision == 'CORRECT' and not correction:
        raise ValueError('CORRECT requires correction payload')
    with connect(path) as c:
        case = c.execute('SELECT * FROM review_cases WHERE id=?',(case_id,)).fetchone()
        if not case: raise KeyError(case_id)
        if case['source_fingerprint'] != source_fingerprint:
            c.execute("UPDATE review_cases SET state='STALE_REVIEW',updated_at=? WHERE id=?",(now(),case_id)); c.commit()
            raise ValueError('source fingerprint drift: review invalidated')
        rid='DEC-'+uuid.uuid4().hex[:12]
        ts=now()
        c.execute('INSERT INTO review_decisions VALUES(?,?,?,?,?,?,?,?)',(rid,case_id,decision,reviewer,rationale,json.dumps(correction,sort_keys=True) if correction else None,source_fingerprint,ts))
        c.execute('UPDATE review_cases SET state=?,updated_at=? WHERE id=?',(decision_state(decision),ts,case_id)); c.commit()
    return rid


def invalidate_on_source_drift(path: Path, case_id: str, current_source_fingerprint: str) -> bool:
    with connect(path) as c:
        case=c.execute('SELECT source_fingerprint,state FROM review_cases WHERE id=?',(case_id,)).fetchone()
        if not case: raise KeyError(case_id)
        if case['source_fingerprint']==current_source_fingerprint:
            return False
        if case['state']!='STALE_REVIEW':
            c.execute("UPDATE review_cases SET state='STALE_REVIEW',updated_at=? WHERE id=?",(now(),case_id)); c.commit()
        return True


def package(path: Path, case_id: str) -> dict[str, Any]:
    with connect(path) as c:
        case=c.execute('SELECT * FROM review_cases WHERE id=?',(case_id,)).fetchone()
        if not case: raise KeyError(case_id)
        evidence=[dict(r) for r in c.execute('SELECT evidence_id,label,summary,locator,role FROM review_evidence WHERE case_id=? ORDER BY role,evidence_id',(case_id,))]
        decisions=[dict(r) for r in c.execute('SELECT id,decision,reviewer,rationale,correction_json,source_fingerprint,decided_at FROM review_decisions WHERE case_id=? ORDER BY decided_at',(case_id,))]
    return {
        'title':case['title'],
        'question':case['question'],
        'candidate_summary':case['candidate_summary'],
        'state':case['state'],
        'evidence':evidence,
        'provenance':{'case_id':case_id,'source_fingerprint':case['source_fingerprint']},
        'decision_history':decisions,
    }


def validate_store(path: Path) -> dict[str, Any]:
    with connect(path) as c:
        fk=c.execute('PRAGMA foreign_key_check').fetchall()
        empty_evidence=c.execute('''SELECT COUNT(*) n FROM review_cases rc LEFT JOIN review_evidence re ON re.case_id=rc.id GROUP BY rc.id HAVING COUNT(re.evidence_id)=0''').fetchall()
        bad_decisions=c.execute("SELECT COUNT(*) n FROM review_decisions WHERE reviewer='' OR rationale=''").fetchone()['n']
    ok=not fk and not empty_evidence and not bad_decisions
    return {'status':'PASS' if ok else 'FAIL','foreign_key_errors':len(fk),'cases_without_evidence':len(empty_evidence),'invalid_decisions':bad_decisions}
