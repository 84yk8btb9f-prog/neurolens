from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path

_DEFAULT_DB = Path(__file__).parent / "data" / "projects.db"


class ProjectStorage:
    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self._path = str(db_path)

    def init(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    result_json TEXT NOT NULL
                )
            """)

    def save(self, name: str, result: dict) -> int:
        content_type = result.get("type", "")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, type, result_json) VALUES (?, ?, ?)",
                (name, content_type, json.dumps(result)),
            )
            return cur.lastrowid

    def list_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, type, created_at FROM projects ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [{"id": r[0], "name": r[1], "type": r[2], "created_at": r[3]} for r in rows]

    def get(self, project_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, type, created_at, result_json FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "created_at": row[3],
            "result": json.loads(row[4]),
        }

    def delete(self, project_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cur.rowcount > 0

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn


_store = ProjectStorage()
_store.init()


def get_storage() -> ProjectStorage:
    return _store
