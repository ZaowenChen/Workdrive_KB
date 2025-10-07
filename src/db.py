import os
import sqlite3
import pathlib
from typing import Dict, Iterable, Optional

DB_PATH = os.getenv("DB_PATH", "data/workdrive.db")
_SCHEMA_ENSURED = False
_LABEL_COLUMNS = (
    "doc_type",
    "product_line",
    "model",
    "software_version",
    "software_version_other",
    "hardware_version",
    "hardware_version_other",
    "subsystem",
    "audience",
    "priority",
    "lifecycle",
    "confidentiality",
    "keywords",
)

_DEFAULTS = {
    "priority": "Medium",
    "lifecycle": "Active",
    "confidentiality": "Internal",
}


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
    _ensure_column(conn, "labels", "doc_type", "TEXT")
    _ensure_column(conn, "labels", "product_line", "TEXT")
    _ensure_column(conn, "labels", "model", "TEXT")
    _ensure_column(conn, "labels", "software_version", "TEXT")
    _ensure_column(conn, "labels", "software_version_other", "TEXT")
    _ensure_column(conn, "labels", "hardware_version", "TEXT")
    _ensure_column(conn, "labels", "hardware_version_other", "TEXT")
    _ensure_column(conn, "labels", "subsystem", "TEXT")
    _ensure_column(conn, "labels", "audience", "TEXT")
    _ensure_column(conn, "labels", "priority", "TEXT")
    _ensure_column(conn, "labels", "lifecycle", "TEXT")
    _ensure_column(conn, "labels", "confidentiality", "TEXT")
    _ensure_column(conn, "labels", "keywords", "TEXT")
    _ensure_column(conn, "labels", "source", "TEXT")
    _ensure_column(conn, "labels", "confidence", "REAL")
    _ensure_column(conn, "labels", "needs_review", "INTEGER DEFAULT 1")
    _ensure_column(conn, "labels", "updated_at", "TEXT")
    _SCHEMA_ENSURED = True


def _clean(value: Optional[str]) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _prepare_labels(payload: Dict) -> Dict:
    data = {field: _clean(payload.get(field)) for field in _LABEL_COLUMNS}

    for key, default in _DEFAULTS.items():
        if not data[key]:
            data[key] = default

    if data["keywords"]:
        normalized_keywords = []
        seen = set()
        for part in data["keywords"].split(","):
            cleaned = part.strip().lower()
            if not cleaned:
                continue
            if cleaned not in seen:
                seen.add(cleaned)
                normalized_keywords.append(cleaned)
        data["keywords"] = ", ".join(normalized_keywords)

    if data["software_version"] == "Other" and not data["software_version_other"]:
        raise ValueError("software_version_other is required when software_version is Other")
    if data["hardware_version"] == "Other" and not data["hardware_version_other"]:
        raise ValueError("hardware_version_other is required when hardware_version is Other")
    if data["doc_type"] == "Other" and not data["keywords"]:
        raise ValueError("keywords are required when doc_type is Other")

    return data


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
        data = _prepare_labels(labels)
        conn.execute(
            """
            INSERT INTO labels(
                file_id, doc_type, product_line, model,
                software_version, software_version_other,
                hardware_version, hardware_version_other,
                subsystem, audience, priority, lifecycle,
                confidentiality, keywords, source, confidence,
                needs_review, updated_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(file_id) DO UPDATE SET
              doc_type=excluded.doc_type,
              product_line=excluded.product_line,
              model=excluded.model,
              software_version=excluded.software_version,
              software_version_other=excluded.software_version_other,
              hardware_version=excluded.hardware_version,
              hardware_version_other=excluded.hardware_version_other,
              subsystem=excluded.subsystem,
              audience=excluded.audience,
              priority=excluded.priority,
              lifecycle=excluded.lifecycle,
              confidentiality=excluded.confidentiality,
              keywords=excluded.keywords,
              source=excluded.source,
              confidence=excluded.confidence,
              needs_review=excluded.needs_review,
              updated_at=datetime('now')
            """,
            (
                file_id,
                data["doc_type"],
                data["product_line"],
                data["model"],
                data["software_version"],
                data["software_version_other"],
                data["hardware_version"],
                data["hardware_version_other"],
                data["subsystem"],
                data["audience"],
                data["priority"],
                data["lifecycle"],
                data["confidentiality"],
                data["keywords"],
                source,
                confidence,
                needs_review,
            ),
        )


def iter_needs_llm() -> Iterable[Dict]:
    with _conn() as conn:
        _ensure_schema(conn)
        query = """
        SELECT d.file_id, d.name, d.excerpt, l.doc_type, l.product_line, l.model
        FROM documents d JOIN labels l ON l.file_id=d.file_id
        WHERE l.source='heuristic' AND (
            l.doc_type IS NULL OR l.doc_type='' OR
            l.product_line IS NULL OR l.product_line='' OR
            l.model IS NULL OR l.model='' OR
            l.confidence < 0.8
        )
        """
        for row in conn.execute(query):
            yield dict(file_id=row[0], name=row[1], excerpt=row[2])


def iter_for_sync() -> Iterable[Dict]:
    with _conn() as conn:
        _ensure_schema(conn)
        query = """
        SELECT d.file_id, d.name, l.doc_type, l.product_line, l.model,
               l.software_version, l.software_version_other,
               l.hardware_version, l.hardware_version_other,
               l.subsystem, l.audience, l.priority,
               l.lifecycle, l.confidentiality, l.keywords
        FROM documents d JOIN labels l ON l.file_id=d.file_id
        WHERE l.needs_review=0
        """
        for row in conn.execute(query):
            yield dict(
                file_id=row[0],
                name=row[1],
                doc_type=row[2],
                product_line=row[3],
                model=row[4],
                software_version=row[5],
                software_version_other=row[6],
                hardware_version=row[7],
                hardware_version_other=row[8],
                subsystem=row[9],
                audience=row[10],
                priority=row[11],
                lifecycle=row[12],
                confidentiality=row[13],
                keywords=row[14],
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
               l.doc_type, l.product_line, l.model,
               l.software_version, l.software_version_other,
               l.hardware_version, l.hardware_version_other,
               l.subsystem, l.audience, l.priority,
               l.lifecycle, l.confidentiality, l.keywords,
               l.source, l.needs_review, l.updated_at
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
        data = _prepare_labels(row)
        conn.execute(
            """
            UPDATE labels
            SET doc_type=?, product_line=?, model=?,
                software_version=?, software_version_other=?,
                hardware_version=?, hardware_version_other=?,
                subsystem=?, audience=?, priority=?,
                lifecycle=?, confidentiality=?, keywords=?,
                source=?, needs_review=?, updated_at=datetime('now')
            WHERE file_id=?
            """,
            (
                data["doc_type"],
                data["product_line"],
                data["model"],
                data["software_version"],
                data["software_version_other"],
                data["hardware_version"],
                data["hardware_version_other"],
                data["subsystem"],
                data["audience"],
                data["priority"],
                data["lifecycle"],
                data["confidentiality"],
                data["keywords"],
                "human",
                0,
                row["file_id"],
            ),
        )
