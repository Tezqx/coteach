"""Persistence for teachers, materials, analyses, and growth programs.

SQLite is the default (zero setup). When DATABASE_URL is set to a
postgres:// or postgresql:// URL (e.g. free Neon or Supabase), the same
queries run on PostgreSQL via psycopg 3. Tables are created on startup.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import Feedback


def database_url() -> str:
    return (os.environ.get("DATABASE_URL") or "").strip()


def using_postgres() -> bool:
    return database_url().startswith(("postgres://", "postgresql://"))


def resolve_db_path() -> Path:
    """SQLite location: DB_PATH env, else a writable default.

    Hugging Face Spaces run as uid 1000. The container filesystem may be
    read-only except /tmp and, when present, /data.
    """
    raw = os.environ.get("DB_PATH", "").strip()
    if raw:
        path = Path(raw)
    else:
        data_dir = Path("/data")
        if data_dir.is_dir() and os.access(data_dir, os.W_OK):
            path = data_dir / "coteach.db"
        elif Path("/.dockerenv").exists() or os.environ.get("SPACE_ID"):
            path = Path("/tmp/coteach.db")
        else:
            path = Path(__file__).resolve().parent.parent / "data" / "teachercoach.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# Resolved on first use so a .env loaded after import still applies.
DB_PATH: Path | None = None


def get_db_path() -> Path:
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = resolve_db_path()
    return DB_PATH


def backend_name() -> str:
    return "postgres" if using_postgres() else "sqlite"


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Connection:
    """Tiny adapter so the same SQL (with `?` placeholders) runs on both backends."""

    def __init__(self) -> None:
        self.pg = using_postgres()
        if self.pg:
            import psycopg
            from psycopg.rows import dict_row

            self.raw = psycopg.connect(database_url(), row_factory=dict_row)
        else:
            path = get_db_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            self.raw = sqlite3.connect(path)
            self.raw.row_factory = sqlite3.Row
            self.raw.execute("PRAGMA foreign_keys = ON")

    def execute(self, sql: str, params: tuple | list = ()):
        if self.pg:
            sql = sql.replace("?", "%s")
        return self.raw.execute(sql, tuple(params))

    def insert(self, sql: str, params: tuple | list = ()) -> int:
        """Run an INSERT and return the new row id on either backend."""
        if self.pg:
            row = self.execute(sql.rstrip().rstrip(";") + " RETURNING id", params).fetchone()
            return int(row["id"])
        return int(self.execute(sql, params).lastrowid)

    def name_match(self, column: str = "name") -> str:
        """Case-insensitive name comparison clause."""
        if self.pg:
            return f"lower({column}) = lower(?)"
        return f"{column} = ? COLLATE NOCASE"

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self.raw.commit()
            else:
                self.raw.rollback()
        finally:
            self.raw.close()


def connect() -> Connection:
    return Connection()


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE,
    created_at TEXT NOT NULL,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    material_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    language TEXT NOT NULL,
    text TEXT NOT NULL,
    filename TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    language TEXT NOT NULL,
    result_json TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    average_score REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analyses_teacher
    ON analyses(teacher_id, created_at);

CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    language TEXT NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    weeks INTEGER NOT NULL,
    goal TEXT NOT NULL DEFAULT '',
    focus_json TEXT NOT NULL,
    focus_source TEXT NOT NULL DEFAULT 'teacher',
    plan_json TEXT NOT NULL,
    baseline_json TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    report_json TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_programs_teacher
    ON programs(teacher_id, created_at);

CREATE TABLE IF NOT EXISTS program_weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL REFERENCES programs(id),
    week_number INTEGER NOT NULL,
    task_json TEXT NOT NULL,
    material_text TEXT NOT NULL,
    filenames TEXT,
    reflection TEXT NOT NULL DEFAULT '',
    result_json TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    average_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(program_id, week_number)
);
"""


def _postgres_schema() -> str:
    # Same tables, PostgreSQL types. Case-insensitive uniqueness via lower(name).
    sql = SQLITE_SCHEMA
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace("name TEXT NOT NULL COLLATE NOCASE,", "name TEXT NOT NULL,")
    sql = sql.replace("REAL NOT NULL", "DOUBLE PRECISION NOT NULL")
    sql += "\nCREATE UNIQUE INDEX IF NOT EXISTS ux_teachers_lower_name ON teachers (lower(name));\n"
    return sql


def _statements(script: str) -> list[str]:
    return [part.strip() for part in script.split(";") if part.strip()]


def init_db() -> None:
    with connect() as conn:
        script = _postgres_schema() if conn.pg else SQLITE_SCHEMA
        if conn.pg:
            for statement in _statements(script):
                conn.raw.execute(statement)
        else:
            conn.raw.executescript(script)


def get_or_create_teacher(name: str) -> dict[str, Any]:
    clean = name.strip()
    if not clean:
        raise ValueError("Teacher name is required")
    with connect() as conn:
        row = conn.execute(
            f"SELECT * FROM teachers WHERE {conn.name_match()}", (clean,)
        ).fetchone()
        if row:
            return dict(row)
        now = utcnow()
        new_id = conn.insert(
            "INSERT INTO teachers (name, created_at) VALUES (?, ?)", (clean, now)
        )
        return {"id": new_id, "name": clean, "created_at": now}


def get_teacher_by_name(name: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            f"SELECT * FROM teachers WHERE {conn.name_match()}", (name.strip(),)
        ).fetchone()
        return dict(row) if row else None


def insert_material(
    teacher_id: int,
    material_type: str,
    subject: str,
    grade: str,
    language: str,
    text: str,
    filename: str | None,
) -> int:
    with connect() as conn:
        return conn.insert(
            """
            INSERT INTO materials (
                teacher_id, material_type, subject, grade, language, text, filename, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (teacher_id, material_type, subject, grade, language, text, filename, utcnow()),
        )


def insert_analysis(
    teacher_id: int,
    material_id: int,
    language: str,
    feedback: Feedback,
) -> int:
    with connect() as conn:
        return conn.insert(
            """
            INSERT INTO analyses (
                teacher_id, material_id, language, result_json, scores_json,
                average_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                teacher_id,
                material_id,
                language,
                feedback.model_dump_json(),
                json.dumps(feedback.scores_dict(), ensure_ascii=False),
                feedback.average_score(),
                utcnow(),
            ),
        )


def get_recent_analyses(teacher_id: int, limit: int = 3) -> list[dict[str, Any]]:
    """Most recent first, used as compact memory for the next coaching prompt."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.language, a.result_json, a.scores_json, a.average_score,
                   a.created_at, m.subject, m.grade, m.material_type
            FROM analyses a
            JOIN materials m ON m.id = a.material_id
            WHERE a.teacher_id = ?
            ORDER BY a.created_at DESC, a.id DESC
            LIMIT ?
            """,
            (teacher_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_analysis(analysis_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT a.*, m.subject, m.grade, m.material_type, m.filename, m.text,
                   t.name AS teacher_name
            FROM analyses a
            JOIN materials m ON m.id = a.material_id
            JOIN teachers t ON t.id = a.teacher_id
            WHERE a.id = ?
            """,
            (analysis_id,),
        ).fetchone()
    if not row:
        return None
    return _enrich(dict(row), include_text=True)


def get_progress(teacher_name: str) -> dict[str, Any] | None:
    teacher = get_teacher_by_name(teacher_name)
    if not teacher:
        return None
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.language, a.result_json, a.scores_json, a.average_score,
                   a.created_at, m.subject, m.grade, m.material_type, m.filename
            FROM analyses a
            JOIN materials m ON m.id = a.material_id
            WHERE a.teacher_id = ?
            ORDER BY a.created_at ASC, a.id ASC
            """,
            (teacher["id"],),
        ).fetchall()
    analyses = [_enrich(dict(r), include_text=False) for r in rows]
    return {"teacher": teacher, "analyses": analyses}


def _enrich(row: dict[str, Any], include_text: bool) -> dict[str, Any]:
    feedback = json.loads(row["result_json"])
    scores = json.loads(row["scores_json"])
    out = {
        "id": row["id"],
        "created_at": row["created_at"],
        "language": row["language"],
        "subject": row["subject"],
        "grade": row["grade"],
        "material_type": row["material_type"],
        "filename": row.get("filename"),
        "average_score": row["average_score"],
        "scores": scores,
        "summary": feedback.get("summary", ""),
        "micro_actions": feedback.get("micro_actions", []),
        "progress_note": feedback.get("progress_note", ""),
        "feedback": feedback,
    }
    if include_text:
        out["text"] = row.get("text")
        out["teacher_name"] = row.get("teacher_name")
    return out


# ---------------------------------------------------------------------------
# Growth Program
# ---------------------------------------------------------------------------


def get_latest_analysis(teacher_id: int) -> dict[str, Any] | None:
    rows = get_recent_analyses(teacher_id, limit=1)
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "subject": row["subject"],
        "grade": row["grade"],
        "average_score": row["average_score"],
        "scores": json.loads(row["scores_json"]),
        "feedback": json.loads(row["result_json"]),
    }


def insert_program(
    *,
    teacher_id: int,
    language: str,
    subject: str,
    grade: str,
    weeks: int,
    goal: str,
    focus: list[str],
    focus_source: str,
    plan: dict[str, Any],
    baseline: dict[str, Any] | None,
) -> int:
    with connect() as conn:
        return conn.insert(
            """
            INSERT INTO programs (
                teacher_id, language, subject, grade, weeks, goal, focus_json,
                focus_source, plan_json, baseline_json, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (
                teacher_id,
                language,
                subject,
                grade,
                weeks,
                goal,
                json.dumps(focus),
                focus_source,
                json.dumps(plan, ensure_ascii=False),
                json.dumps(baseline, ensure_ascii=False) if baseline else None,
                utcnow(),
            ),
        )


def insert_program_week(
    *,
    program_id: int,
    week_number: int,
    task: dict[str, Any],
    material_text: str,
    filenames: list[str],
    reflection: str,
    result: dict[str, Any],
    scores: dict[str, int],
    average_score: float,
) -> int:
    with connect() as conn:
        return conn.insert(
            """
            INSERT INTO program_weeks (
                program_id, week_number, task_json, material_text, filenames,
                reflection, result_json, scores_json, average_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                program_id,
                week_number,
                json.dumps(task, ensure_ascii=False),
                material_text,
                json.dumps(filenames, ensure_ascii=False),
                reflection,
                json.dumps(result, ensure_ascii=False),
                json.dumps(scores),
                average_score,
                utcnow(),
            ),
        )


def complete_program(program_id: int, report: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE programs SET status = 'completed', report_json = ?, completed_at = ? WHERE id = ?",
            (json.dumps(report, ensure_ascii=False), utcnow(), program_id),
        )


def _program_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "teacher_id": row["teacher_id"],
        "teacher_name": row.get("teacher_name"),
        "language": row["language"],
        "subject": row["subject"],
        "grade": row["grade"],
        "weeks": int(row["weeks"]),
        "goal": row.get("goal") or "",
        "focus_criteria": json.loads(row["focus_json"]),
        "focus_source": row.get("focus_source") or "teacher",
        "plan": json.loads(row["plan_json"]),
        "baseline": json.loads(row["baseline_json"]) if row.get("baseline_json") else None,
        "status": row["status"],
        "report": json.loads(row["report_json"]) if row.get("report_json") else None,
        "created_at": row["created_at"],
        "completed_at": row.get("completed_at"),
    }


def get_program(program_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT p.*, t.name AS teacher_name
            FROM programs p JOIN teachers t ON t.id = p.teacher_id
            WHERE p.id = ?
            """,
            (program_id,),
        ).fetchone()
        if not row:
            return None
        week_rows = conn.execute(
            "SELECT * FROM program_weeks WHERE program_id = ? ORDER BY week_number ASC",
            (program_id,),
        ).fetchall()
    program = _program_row(dict(row))
    program["submissions"] = [_week_row(dict(r)) for r in week_rows]
    return program


def _week_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "week_number": int(row["week_number"]),
        "task": json.loads(row["task_json"]),
        "material_text": row["material_text"],
        "filenames": json.loads(row["filenames"]) if row.get("filenames") else [],
        "reflection": row.get("reflection") or "",
        "feedback": json.loads(row["result_json"]),
        "scores": json.loads(row["scores_json"]),
        "average_score": row["average_score"],
        "created_at": row["created_at"],
    }


def list_programs(teacher_name: str) -> list[dict[str, Any]] | None:
    teacher = get_teacher_by_name(teacher_name)
    if not teacher:
        return None
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT p.*, t.name AS teacher_name,
                   (SELECT COUNT(*) FROM program_weeks w WHERE w.program_id = p.id) AS submitted
            FROM programs p JOIN teachers t ON t.id = p.teacher_id
            WHERE p.teacher_id = ?
            ORDER BY p.created_at DESC, p.id DESC
            """,
            (teacher["id"],),
        ).fetchall()
    out = []
    for r in rows:
        item = _program_row(dict(r))
        item["submitted"] = int(dict(r)["submitted"])
        item.pop("plan", None)
        item.pop("report", None)
        item["title"] = json.loads(dict(r)["plan_json"]).get("title", "")
        out.append(item)
    return out
