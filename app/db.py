from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import Feedback

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "teachercoach.db"


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
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
            """
        )


def get_or_create_teacher(name: str) -> dict[str, Any]:
    clean = name.strip()
    if not clean:
        raise ValueError("Teacher name is required")
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM teachers WHERE name = ? COLLATE NOCASE", (clean,)
        ).fetchone()
        if row:
            return dict(row)
        now = utcnow()
        cur = conn.execute(
            "INSERT INTO teachers (name, created_at) VALUES (?, ?)", (clean, now)
        )
        return {"id": cur.lastrowid, "name": clean, "created_at": now}


def get_teacher_by_name(name: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM teachers WHERE name = ? COLLATE NOCASE", (name.strip(),)
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
        cur = conn.execute(
            """
            INSERT INTO materials (
                teacher_id, material_type, subject, grade, language, text, filename, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (teacher_id, material_type, subject, grade, language, text, filename, utcnow()),
        )
        return int(cur.lastrowid)


def insert_analysis(
    teacher_id: int,
    material_id: int,
    language: str,
    feedback: Feedback,
) -> int:
    with connect() as conn:
        cur = conn.execute(
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
        return int(cur.lastrowid)


def get_recent_analyses(teacher_id: int, limit: int = 3) -> list[dict[str, Any]]:
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
