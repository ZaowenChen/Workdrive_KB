import os
import sqlite3
import pathlib
from typing import Dict, Iterable

DB_PATH = os.getenv("DB_PATH", "data/workdrive.db")
_SCHEMA_ENSURED = False


def _conn():
    path = pathlib.Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as conn:
        conn.executescript(open("data/schema.sql").read())
        _ensure_schema(conn)


def _ensure_column(conn, table: str, column: str, definition: str) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _table_exists(conn, table: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cursor.fetchone() is not None


def _ensure_schema(conn) -> None:
    global _SCHEMA_ENSURED
    if _SCHEMA_ENSURED:
        return
    if not _table_exists(conn, "documents") or not _table_exists(conn, "labels"):
        return
    _ensure_column(conn, "documents", "permalink", "TEXT")
    _ensure_column(conn, "documents", "download_url", "TEXT")
    _ensure_column(conn, "labels", "hardware_version", "TEXT")
    _ensure_column(conn, "labels", "software_version", "TEXT")
    _ensure_column(conn, "labels", "priority", "TEXT")
    _ensure_column(conn, "labels", "audience_level", "TEXT")
    _SCHEMA_ENSURED = True


def upsert_document(row: Dict):
    with _conn() as conn:
        _ensure_schema(conn)
        suffix = os.path.splitext(row["name"])[1].lower()
        conn.execute(
            """
            INSERT INTO documents(file_id,name,path,size,created_time,modified_time,suffix,permalink,download_url,last_seen)
            VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(file_id) DO UPDATE SET
              name=excluded.name, path=excluded.path, size=excluded.size,
              created_time=excluded.created_time, modified_time=excluded.modified_time,
              suffix=excluded.suffix,
              permalink=excluded.permalink,
              download_url=excluded.download_url,
              last_seen=datetime('now');
            """,
            (
                row["file_id"],
                row["name"],
                row["path"],
                row["size"],
                row["created_time"],
                row["modified_time"],
                suffix,
                row.get("permalink", ""),
                row.get("download_url", ""),
            ),
        )


def mark_seen(file_id: str):
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            "UPDATE documents SET last_seen=datetime('now') WHERE file_id=?",
            (file_id,),
        )


def iter_documents_without_excerpt() -> Iterable[Dict]:
    with _conn() as conn:
        _ensure_schema(conn)
        for row in conn.execute(
            "SELECT file_id,name,suffix FROM documents WHERE excerpt IS NULL OR excerpt=''"
        ):
            yield dict(file_id=row[0], name=row[1], suffix=row[2])


def store_excerpt(file_id: str, excerpt: str, sha256: str):
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            "UPDATE documents SET excerpt=?, sha256=? WHERE file_id=?",
            (excerpt, sha256, file_id),
        )


def iter_documents_for_heuristics() -> Iterable[Dict]:
    with _conn() as conn:
        _ensure_schema(conn)
        query = """
        SELECT d.file_id, d.name, d.excerpt
        FROM documents d
        LEFT JOIN labels l ON l.file_id=d.file_id
        WHERE d.excerpt IS NOT NULL AND (l.file_id IS NULL OR l.source IS NULL)
        """
        for row in conn.execute(query):
            yield dict(file_id=row[0], name=row[1], excerpt=row[2])


def upsert_labels(file_id: str, labels: Dict, source: str, confidence: float, needs_review: int):
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO labels(file_id,doc_type,model_type,subsystem,language,hardware_version,software_version,priority,audience_level,source,confidence,needs_review)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(file_id) DO UPDATE SET
              doc_type=excluded.doc_type, model_type=excluded.model_type,
              subsystem=excluded.subsystem, language=excluded.language,
              hardware_version=excluded.hardware_version,
              software_version=excluded.software_version,
              priority=excluded.priority,
              audience_level=excluded.audience_level,
              source=excluded.source, confidence=excluded.confidence,
              needs_review=excluded.needs_review
            """,
            (
                file_id,
                labels.get("doc_type", ""),
                labels.get("model_type", ""),
                labels.get("subsystem", ""),
                labels.get("language", ""),
                labels.get("hardware_version", ""),
                labels.get("software_version", ""),
                labels.get("priority", ""),
                labels.get("audience_level", ""),
                source,
                confidence,
                needs_review,
            ),
        )


def iter_needs_llm() -> Iterable[Dict]:
    with _conn() as conn:
        _ensure_schema(conn)
        query = """
        SELECT d.file_id, d.name, d.excerpt, l.doc_type, l.model_type
        FROM documents d JOIN labels l ON l.file_id=d.file_id
        WHERE l.source='heuristic' AND (l.doc_type='' OR l.model_type='' OR l.confidence < 0.8)
        """
        for row in conn.execute(query):
            yield dict(file_id=row[0], name=row[1], excerpt=row[2])


def iter_for_sync() -> Iterable[Dict]:
    with _conn() as conn:
        _ensure_schema(conn)
        query = """
        SELECT d.file_id, d.name, l.doc_type, l.model_type, l.subsystem, l.language,
               l.hardware_version, l.software_version, l.priority, l.audience_level
        FROM documents d JOIN labels l ON l.file_id=d.file_id
        WHERE l.needs_review=0
        """
        for row in conn.execute(query):
            yield dict(
                file_id=row[0],
                name=row[1],
                doc_type=row[2],
                model_type=row[3],
                subsystem=row[4],
                language=row[5],
                hardware_version=row[6],
                software_version=row[7],
                priority=row[8],
                audience_level=row[9],
            )


def save_audit_change(file_id: str, field: str, old_value: str, new_value: str, actor: str = "pipeline"):
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            "INSERT INTO audit(file_id,field,old_value,new_value,actor) VALUES (?,?,?,?,?)",
            (file_id, field, old_value, new_value, actor),
        )


def all_for_csv():
    with _conn() as conn:
        _ensure_schema(conn)
        query = """
        SELECT d.file_id, d.path, d.name, d.size, d.modified_time,
               d.permalink, d.download_url, d.excerpt,
               l.doc_type, l.model_type, l.subsystem, l.language,
               l.hardware_version, l.software_version, l.priority, l.audience_level,
               l.source, l.needs_review
        FROM documents d LEFT JOIN labels l ON l.file_id=d.file_id
        ORDER BY d.path
        """
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor]
        return rows


def update_from_csv_row(row: Dict):
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            UPDATE labels
            SET doc_type=?, model_type=?, subsystem=?, language=?,
                hardware_version=?, software_version=?, priority=?, audience_level=?,
                source=?, needs_review=?
            WHERE file_id=?
            """,
            (
                row.get("doc_type", ""),
                row.get("model_type", ""),
                row.get("subsystem", ""),
                row.get("language", ""),
                row.get("hardware_version", ""),
                row.get("software_version", ""),
                row.get("priority", ""),
                row.get("audience_level", ""),
                "human",
                0,
                row["file_id"],
            ),
        )
