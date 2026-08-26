from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable

MIGRATION_LEDGER_SCHEMA = '''
CREATE TABLE IF NOT EXISTS cew_schema_migrations(
  scope TEXT NOT NULL,
  version INTEGER NOT NULL,
  migration_id TEXT NOT NULL,
  applied_at TEXT NOT NULL,
  PRIMARY KEY(scope, version),
  UNIQUE(migration_id)
);
'''

CORE_SCOPE = 'docintel-core'
CORE_VERSION = 1
GRAPHIC_SCOPE = 'graphic-conventions'
GRAPHIC_VERSION = 2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def table_exists(c: sqlite3.Connection, table: str) -> bool:
    return c.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def table_columns(c: sqlite3.Connection, table: str) -> set[str]:
    if not table_exists(c, table):
        return set()
    return {row[1] for row in c.execute(f'PRAGMA table_info({table})').fetchall()}


def ensure_ledger(c: sqlite3.Connection) -> None:
    c.executescript(MIGRATION_LEDGER_SCHEMA)


def record(c: sqlite3.Connection, scope: str, version: int, migration_id: str) -> None:
    c.execute(
        '''INSERT OR IGNORE INTO cew_schema_migrations(scope,version,migration_id,applied_at)
           VALUES(?,?,?,?)''',
        (scope, version, migration_id, now()),
    )


def current_version(c: sqlite3.Connection, scope: str) -> int:
    ensure_ledger(c)
    row = c.execute(
        'SELECT COALESCE(MAX(version),0) FROM cew_schema_migrations WHERE scope=?',
        (scope,),
    ).fetchone()
    return int(row[0])


def ensure_core_schema(c: sqlite3.Connection, schema: str) -> None:
    """Create/validate the current core schema and record its version.

    Existing tables are preserved. Future core migrations must be explicit steps
    before CORE_VERSION is advanced; merely changing CREATE TABLE statements is
    not considered a migration.
    """
    ensure_ledger(c)
    version = current_version(c, CORE_SCOPE)
    if version > CORE_VERSION:
        raise RuntimeError(
            f'database {CORE_SCOPE} schema v{version} is newer than supported v{CORE_VERSION}'
        )
    c.executescript(schema)
    required = {
        'sources', 'source_versions', 'processing_generations',
        'source_version_processing', 'observations',
        'observation_generation_bindings', 'conventions', 'proposals',
    }
    missing = sorted(t for t in required if not table_exists(c, t))
    if missing:
        raise RuntimeError(f'core schema incomplete after initialization: {missing}')
    if version == 0:
        record(c, CORE_SCOPE, CORE_VERSION, 'DOCINTEL_CORE_BASELINE_v1')
    c.commit()


def _add_column_if_missing(c: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if column not in table_columns(c, table):
        c.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')


def _legacy_training_rows(c: sqlite3.Connection) -> list[sqlite3.Row]:
    return c.execute('''
        SELECT gt.rowid AS legacy_rowid,
               gt.observation_id,
               gt.observation_kind AS kind,
               gt.value_text,
               gt.page,gt.x0,gt.y0,gt.x1,gt.y1,
               o.detector,
               sv.sha256 AS source_sha256
        FROM graphic_training_examples gt
        LEFT JOIN observations o ON o.id=gt.observation_id
        LEFT JOIN source_versions sv ON sv.id=gt.source_version_id
        WHERE gt.candidate_fingerprint IS NULL OR gt.source_sha256 IS NULL
    ''').fetchall()


def _legacy_proposal_rows(c: sqlite3.Connection) -> list[sqlite3.Row]:
    return c.execute('''
        SELECT gp.rowid AS legacy_rowid,
               gp.observation_id,
               o.kind,o.value_text,o.page,o.x0,o.y0,o.x1,o.y1,o.detector,
               sv.sha256 AS source_sha256
        FROM graphic_meaning_proposals gp
        LEFT JOIN observations o ON o.id=gp.observation_id
        LEFT JOIN source_versions sv ON sv.id=o.source_version_id
        WHERE gp.candidate_fingerprint IS NULL OR gp.source_sha256 IS NULL
    ''').fetchall()


def _row_as_fingerprint_input(row: sqlite3.Row) -> dict[str, Any]:
    required = ('source_sha256', 'page', 'kind', 'detector')
    missing = [name for name in required if row[name] is None]
    if missing:
        raise RuntimeError(
            'cannot migrate graphic review identity because legacy evidence lineage is incomplete: '
            + ','.join(missing)
        )
    return {
        'source_sha256': row['source_sha256'],
        'page': row['page'],
        'x0': row['x0'],
        'y0': row['y0'],
        'x1': row['x1'],
        'y1': row['y1'],
        'kind': row['kind'],
        'value_text': row['value_text'],
        'detector': row['detector'],
    }


def ensure_graphic_schema(
    c: sqlite3.Connection,
    schema: str,
    fingerprint_builder: Callable[[dict[str, Any]], str],
) -> None:
    """Upgrade Graphic Convention storage to stable source-bound review identity.

    The v1 prototype keyed review rows mainly by ephemeral observation ids. v2
    introduces candidate_fingerprint + source_sha256. Existing rows are
    backfilled only if their original Observation -> SourceVersion lineage is
    reconstructible; otherwise migration fails closed and leaves the transaction
    uncommitted.
    """
    ensure_ledger(c)
    version = current_version(c, GRAPHIC_SCOPE)
    if version > GRAPHIC_VERSION:
        raise RuntimeError(
            f'database {GRAPHIC_SCOPE} schema v{version} is newer than supported v{GRAPHIC_VERSION}'
        )

    training_exists = table_exists(c, 'graphic_training_examples')
    proposal_exists = table_exists(c, 'graphic_meaning_proposals')

    if not training_exists and not proposal_exists:
        c.executescript(schema)
        record(c, GRAPHIC_SCOPE, GRAPHIC_VERSION, 'GRAPHIC_CONVENTION_STABLE_IDENTITY_v2')
        c.commit()
        return

    try:
        c.execute('BEGIN IMMEDIATE')

        if training_exists:
            _add_column_if_missing(c, 'graphic_training_examples', 'candidate_fingerprint', 'candidate_fingerprint TEXT')
            _add_column_if_missing(c, 'graphic_training_examples', 'source_sha256', 'source_sha256 TEXT')
            for row in _legacy_training_rows(c):
                fp = fingerprint_builder(_row_as_fingerprint_input(row))
                c.execute(
                    '''UPDATE graphic_training_examples
                       SET candidate_fingerprint=?,source_sha256=?
                       WHERE rowid=?''',
                    (fp, row['source_sha256'], row['legacy_rowid']),
                )
            unresolved = c.execute('''
                SELECT COUNT(*) FROM graphic_training_examples
                WHERE candidate_fingerprint IS NULL OR source_sha256 IS NULL
            ''').fetchone()[0]
            if unresolved:
                raise RuntimeError(f'{unresolved} graphic training rows could not be migrated')

        if proposal_exists:
            _add_column_if_missing(c, 'graphic_meaning_proposals', 'candidate_fingerprint', 'candidate_fingerprint TEXT')
            _add_column_if_missing(c, 'graphic_meaning_proposals', 'source_sha256', 'source_sha256 TEXT')
            for row in _legacy_proposal_rows(c):
                fp = fingerprint_builder(_row_as_fingerprint_input(row))
                c.execute(
                    '''UPDATE graphic_meaning_proposals
                       SET candidate_fingerprint=?,source_sha256=?
                       WHERE rowid=?''',
                    (fp, row['source_sha256'], row['legacy_rowid']),
                )
            unresolved = c.execute('''
                SELECT COUNT(*) FROM graphic_meaning_proposals
                WHERE candidate_fingerprint IS NULL OR source_sha256 IS NULL
            ''').fetchone()[0]
            if unresolved:
                raise RuntimeError(f'{unresolved} graphic proposal rows could not be migrated')

        # Now CREATE INDEX statements that depend on v2 columns are safe.
        c.executescript(schema)
        c.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_graphic_training_stable_review
                     ON graphic_training_examples(candidate_fingerprint,meaning,reviewer)''')
        record(c, GRAPHIC_SCOPE, GRAPHIC_VERSION, 'GRAPHIC_CONVENTION_STABLE_IDENTITY_v2')
        c.commit()
    except Exception:
        c.rollback()
        raise
