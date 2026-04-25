from __future__ import annotations
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_DB = Path(__file__).parent / "data" / "projects.db"


class ProjectStorage:
    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self._path = str(db_path)

    def init(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(self._path)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.close()
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
            cols = {row[1] for row in conn.execute("PRAGMA table_info(projects)").fetchall()}
            if "share_token" not in cols:
                conn.execute("ALTER TABLE projects ADD COLUMN share_token TEXT")
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_share_token ON projects(share_token)")

    def save(self, name: str, result: dict) -> int:
        content_type = result.get("type", "")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, type, result_json) VALUES (?, ?, ?)",
                (name, content_type, json.dumps(result)),
            )
            row_id = cur.lastrowid
            if row_id is None:
                raise RuntimeError("INSERT succeeded but returned no row ID")
            return row_id

    def list_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, type, created_at FROM projects ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [{"id": r[0], "name": r[1], "type": r[2], "created_at": r[3]} for r in rows]

    def get(self, project_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, type, created_at, result_json, share_token FROM projects WHERE id = ?",
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
            "share_token": row[5],
        }

    def delete(self, project_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cur.rowcount > 0

    def share(self, project_id: int) -> str | None:
        """Generate or return existing share token. Returns None if project not found."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT share_token FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if row is None:
                return None
            existing = row[0]
            if existing:
                return existing
            token = secrets.token_urlsafe(16)
            conn.execute(
                "UPDATE projects SET share_token = ? WHERE id = ?",
                (token, project_id),
            )
            return token

    def get_by_token(self, token: str) -> dict | None:
        if not token:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, type, created_at, result_json FROM projects WHERE share_token = ?",
                (token,),
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

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


_store = ProjectStorage()
try:
    _store.init()
except Exception as exc:
    import logging
    logging.getLogger(__name__).error("Failed to initialize project storage: %s", exc)
    raise


def get_storage() -> ProjectStorage:
    return _store
