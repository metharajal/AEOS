"""
AEOS Brain — local sovereign Project Brain backed by SQLite.

One .db file per project. Zero external dependencies (stdlib sqlite3 only).
Offline-first. Portable: the .db file is the entire Brain.
Schema is versioned from v1 — migrate-on-open pattern.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from aeos.brain.models import (
    BrainStatus,
    Decision,
    InteractionRecord,
    KnowledgeFact,
    ProjectIdentity,
    VocabularyTerm,
)

SCHEMA_VERSION: int = 1

DEFAULT_BRAIN_DIR: Path = Path.home() / ".aeos" / "brain"

# ---------------------------------------------------------------------------
# SQL schema — base tables (always created)
# ---------------------------------------------------------------------------

_SCHEMA_BASE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER NOT NULL,
    applied_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS project_identity (
    project_name TEXT PRIMARY KEY,
    project_path TEXT NOT NULL,
    project_type TEXT,
    stack        TEXT NOT NULL DEFAULT '[]',
    languages    TEXT NOT NULL DEFAULT '[]',
    description  TEXT,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_facts (
    id            TEXT PRIMARY KEY,
    fact_type     TEXT NOT NULL,
    dimension     TEXT NOT NULL,
    severity      TEXT,
    summary       TEXT NOT NULL,
    detail        TEXT,
    source_record TEXT,
    source_date   TEXT,
    resolved_at   TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    rationale    TEXT,
    alternatives TEXT NOT NULL DEFAULT '[]',
    impact       TEXT,
    decided_at   TEXT NOT NULL,
    decided_by   TEXT NOT NULL DEFAULT 'human'
);

CREATE TABLE IF NOT EXISTS vocabulary (
    term       TEXT PRIMARY KEY,
    definition TEXT NOT NULL,
    aliases    TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS interaction_log (
    id               TEXT PRIMARY KEY,
    question         TEXT NOT NULL,
    brain_version    TEXT NOT NULL,
    dimensions       TEXT NOT NULL DEFAULT '[]',
    token_budget     INTEGER,
    provider         TEXT,
    model            TEXT,
    response_summary TEXT,
    asked_at         TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# SQL schema — FTS5 virtual table + triggers (optional, degrades gracefully)
# ---------------------------------------------------------------------------

_SCHEMA_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
    summary,
    detail,
    content='knowledge_facts',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON knowledge_facts BEGIN
    INSERT INTO facts_fts(rowid, summary, detail)
    VALUES (new.rowid, new.summary, new.detail);
END;

CREATE TRIGGER IF NOT EXISTS facts_ad BEFORE DELETE ON knowledge_facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, summary, detail)
    VALUES ('delete', old.rowid, old.summary, old.detail);
END;

CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON knowledge_facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, summary, detail)
    VALUES ('delete', old.rowid, old.summary, old.detail);
    INSERT INTO facts_fts(rowid, summary, detail)
    VALUES (new.rowid, new.summary, new.detail);
END;
"""


class BrainStore:
    """Local sovereign Project Brain backed by a single SQLite file.

    Usage:
        with BrainStore.open(brain_dir, "my-project") as brain:
            brain.insert_fact(fact)
            status = brain.get_status()
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._fts_available: bool = False
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._bootstrap()

    # ── construction ──────────────────────────────────────────────────────────

    @classmethod
    def open(cls, brain_dir: Path, project_name: str) -> BrainStore:
        """Open (or create) the Brain for a project. Never raises if dirs exist."""
        brain_dir.mkdir(parents=True, exist_ok=True)
        return cls(brain_dir / f"{project_name}.db")

    @staticmethod
    def exists(brain_dir: Path, project_name: str) -> bool:
        """Return True if a Brain file exists for this project."""
        return (brain_dir / f"{project_name}.db").exists()

    @staticmethod
    def db_path_for(brain_dir: Path, project_name: str) -> Path:
        """Return the expected .db path without opening the Brain."""
        return brain_dir / f"{project_name}.db"

    # ── schema lifecycle ──────────────────────────────────────────────────────

    def _bootstrap(self) -> None:
        """Create schema on first open; run migrations on upgrade."""
        row = self._conn.execute(
            "SELECT name FROM sqlite_master"
            " WHERE type='table' AND name='schema_version'"
        ).fetchone()
        if row is None:
            self._create_schema()
            return
        # Re-opening an existing Brain — check FTS availability
        fts_row = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='facts_fts'"
        ).fetchone()
        self._fts_available = fts_row is not None
        version_row = self._conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        if version_row is not None and int(version_row["version"]) < SCHEMA_VERSION:
            self._migrate(int(version_row["version"]))

    def _create_schema(self) -> None:
        """Create base tables, then attempt FTS5 (degrades gracefully if absent)."""
        self._conn.executescript(_SCHEMA_BASE)
        try:
            self._conn.executescript(_SCHEMA_FTS)
            self._fts_available = True
        except sqlite3.OperationalError:
            self._fts_available = False
        with self._conn:
            self._conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now(tz=UTC).isoformat()),
            )

    def _migrate(self, current_version: int) -> None:
        """Apply schema migrations. Placeholder — no migrations in v1."""

    # ── project identity ──────────────────────────────────────────────────────

    def upsert_identity(self, identity: ProjectIdentity) -> None:
        """Insert or update the project identity."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO project_identity
                    (project_name, project_path, project_type, stack,
                     languages, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_name) DO UPDATE SET
                    project_path = excluded.project_path,
                    project_type = excluded.project_type,
                    stack        = excluded.stack,
                    languages    = excluded.languages,
                    description  = excluded.description,
                    updated_at   = excluded.updated_at
                """,
                (
                    identity.project_name,
                    identity.project_path,
                    identity.project_type,
                    json.dumps(identity.stack),
                    json.dumps(identity.languages),
                    identity.description,
                    identity.updated_at,
                ),
            )

    def get_identity(self) -> ProjectIdentity | None:
        """Return the stored project identity, or None if not yet set."""
        row = self._conn.execute("SELECT * FROM project_identity LIMIT 1").fetchone()
        if row is None:
            return None
        return ProjectIdentity(
            project_name=str(row["project_name"]),
            project_path=str(row["project_path"]),
            project_type=str(row["project_type"]) if row["project_type"] else None,
            stack=json.loads(str(row["stack"])),
            languages=json.loads(str(row["languages"])),
            description=str(row["description"]) if row["description"] else None,
            updated_at=str(row["updated_at"]),
        )

    # ── knowledge facts ───────────────────────────────────────────────────────

    def insert_fact(self, fact: KnowledgeFact) -> None:
        """Insert a KnowledgeFact. Duplicate IDs are silently ignored."""
        with self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO knowledge_facts
                    (id, fact_type, dimension, severity, summary, detail,
                     source_record, source_date, resolved_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.id,
                    fact.fact_type,
                    fact.dimension,
                    fact.severity,
                    fact.summary,
                    fact.detail,
                    fact.source_record,
                    fact.source_date,
                    fact.resolved_at,
                    fact.created_at,
                ),
            )

    def get_fact(self, fact_id: str) -> KnowledgeFact | None:
        """Return a single KnowledgeFact by ID, or None."""
        row = self._conn.execute(
            "SELECT * FROM knowledge_facts WHERE id = ?", (fact_id,)
        ).fetchone()
        return _row_to_fact(row) if row is not None else None

    def get_facts(
        self,
        dimension: str | None = None,
        include_resolved: bool = False,
    ) -> list[KnowledgeFact]:
        """Return facts, optionally filtered by dimension and resolved status."""
        if dimension is not None and not include_resolved:
            rows = self._conn.execute(
                "SELECT * FROM knowledge_facts"
                " WHERE dimension = ? AND resolved_at IS NULL"
                " ORDER BY created_at DESC",
                (dimension,),
            ).fetchall()
        elif dimension is not None:
            rows = self._conn.execute(
                "SELECT * FROM knowledge_facts"
                " WHERE dimension = ?"
                " ORDER BY created_at DESC",
                (dimension,),
            ).fetchall()
        elif not include_resolved:
            rows = self._conn.execute(
                "SELECT * FROM knowledge_facts"
                " WHERE resolved_at IS NULL"
                " ORDER BY created_at DESC",
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM knowledge_facts ORDER BY created_at DESC",
            ).fetchall()
        return [_row_to_fact(r) for r in rows]

    def search_facts(self, query: str) -> list[KnowledgeFact]:
        """Full-text search over fact summaries and details.

        Falls back to LIKE search if FTS5 is unavailable.
        """
        if self._fts_available:
            rows = self._conn.execute(
                "SELECT kf.* FROM knowledge_facts kf"
                " JOIN facts_fts ON facts_fts.rowid = kf.rowid"
                " WHERE facts_fts MATCH ? ORDER BY rank",
                (query,),
            ).fetchall()
        else:
            pattern = f"%{query}%"
            rows = self._conn.execute(
                "SELECT * FROM knowledge_facts"
                " WHERE summary LIKE ? OR detail LIKE ?"
                " ORDER BY created_at DESC",
                (pattern, pattern),
            ).fetchall()
        return [_row_to_fact(r) for r in rows]

    # ── decisions ─────────────────────────────────────────────────────────────

    def insert_decision(self, decision: Decision) -> None:
        """Insert a Decision. Duplicate IDs are silently ignored."""
        with self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO decisions
                    (id, title, description, rationale, alternatives,
                     impact, decided_at, decided_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.id,
                    decision.title,
                    decision.description,
                    decision.rationale,
                    json.dumps(decision.alternatives),
                    decision.impact,
                    decision.decided_at,
                    decision.decided_by,
                ),
            )

    def get_decisions(self) -> list[Decision]:
        """Return all decisions, most recent first."""
        rows = self._conn.execute(
            "SELECT * FROM decisions ORDER BY decided_at DESC"
        ).fetchall()
        return [
            Decision(
                id=str(r["id"]),
                title=str(r["title"]),
                description=str(r["description"]),
                rationale=str(r["rationale"]) if r["rationale"] else None,
                alternatives=json.loads(str(r["alternatives"])),
                impact=str(r["impact"]) if r["impact"] else None,
                decided_at=str(r["decided_at"]),
                decided_by=str(r["decided_by"]),
            )
            for r in rows
        ]

    # ── vocabulary ────────────────────────────────────────────────────────────

    def upsert_vocabulary(self, term: VocabularyTerm) -> None:
        """Insert or update a vocabulary term."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO vocabulary (term, definition, aliases)
                VALUES (?, ?, ?)
                ON CONFLICT(term) DO UPDATE SET
                    definition = excluded.definition,
                    aliases    = excluded.aliases
                """,
                (term.term, term.definition, json.dumps(term.aliases)),
            )

    def get_vocabulary(self) -> list[VocabularyTerm]:
        """Return all vocabulary terms, sorted alphabetically."""
        rows = self._conn.execute("SELECT * FROM vocabulary ORDER BY term").fetchall()
        return [
            VocabularyTerm(
                term=str(r["term"]),
                definition=str(r["definition"]),
                aliases=json.loads(str(r["aliases"])),
            )
            for r in rows
        ]

    # ── interaction log ───────────────────────────────────────────────────────

    def log_interaction(self, record: InteractionRecord) -> None:
        """Persist an AI interaction record. Duplicate IDs are silently ignored."""
        with self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO interaction_log
                    (id, question, brain_version, dimensions, token_budget,
                     provider, model, response_summary, asked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.question,
                    record.brain_version,
                    json.dumps(record.dimensions),
                    record.token_budget,
                    record.provider,
                    record.model,
                    record.response_summary,
                    record.asked_at,
                ),
            )

    # ── status & version ──────────────────────────────────────────────────────

    def get_brain_version(self) -> str:
        """Return a 12-character hash of the Brain's current content.

        Same content → same hash. Changes when any fact, decision, or vocab
        term is added. Used to track which Brain state was used for each
        AI interaction.
        """
        fact_ids = sorted(
            str(r[0])
            for r in self._conn.execute(
                "SELECT id FROM knowledge_facts ORDER BY id"
            ).fetchall()
        )
        decision_ids = sorted(
            str(r[0])
            for r in self._conn.execute(
                "SELECT id FROM decisions ORDER BY id"
            ).fetchall()
        )
        vocab_terms = sorted(
            str(r[0])
            for r in self._conn.execute(
                "SELECT term FROM vocabulary ORDER BY term"
            ).fetchall()
        )
        payload = "|".join(fact_ids + decision_ids + vocab_terms)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    def get_status(self) -> BrainStatus:
        """Return a full status snapshot of this Brain."""
        schema_row = self._conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        schema_version = (
            int(schema_row["version"]) if schema_row is not None else SCHEMA_VERSION
        )
        facts_count = int(
            self._conn.execute("SELECT COUNT(*) FROM knowledge_facts").fetchone()[0]
        )
        decisions_count = int(
            self._conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        )
        vocabulary_count = int(
            self._conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
        )
        interactions_count = int(
            self._conn.execute("SELECT COUNT(*) FROM interaction_log").fetchone()[0]
        )
        last_row = self._conn.execute(
            "SELECT created_at FROM knowledge_facts ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        last_fact_at = str(last_row["created_at"]) if last_row is not None else None
        dim_rows = self._conn.execute(
            "SELECT dimension, COUNT(*) as cnt FROM knowledge_facts GROUP BY dimension"
        ).fetchall()
        dimension_counts = {str(r["dimension"]): int(r["cnt"]) for r in dim_rows}
        identity = self.get_identity()
        project_name = identity.project_name if identity is not None else ""
        return BrainStatus(
            project_name=project_name,
            db_path=str(self._db_path),
            schema_version=schema_version,
            facts_count=facts_count,
            decisions_count=decisions_count,
            vocabulary_count=vocabulary_count,
            interactions_count=interactions_count,
            last_fact_at=last_fact_at,
            dimension_counts=dimension_counts,
            brain_version=self.get_brain_version(),
        )

    # ── context manager ───────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()

    def __enter__(self) -> BrainStore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level helper (not a method — avoids mypy Row typing issues)
# ---------------------------------------------------------------------------


def _row_to_fact(row: sqlite3.Row) -> KnowledgeFact:
    """Convert a sqlite3.Row from knowledge_facts to a KnowledgeFact."""
    return KnowledgeFact(
        id=str(row["id"]),
        fact_type=str(row["fact_type"]),
        dimension=str(row["dimension"]),
        severity=str(row["severity"]) if row["severity"] else None,
        summary=str(row["summary"]),
        detail=str(row["detail"]) if row["detail"] else None,
        source_record=str(row["source_record"]) if row["source_record"] else None,
        source_date=str(row["source_date"]) if row["source_date"] else None,
        resolved_at=str(row["resolved_at"]) if row["resolved_at"] else None,
        created_at=str(row["created_at"]),
    )
