PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
  file_id TEXT PRIMARY KEY,
  name TEXT,
  path TEXT,
  size INTEGER,
  created_time TEXT,
  modified_time TEXT,
  suffix TEXT,
  permalink TEXT,
  download_url TEXT,
  sha256 TEXT,
  excerpt TEXT,
  last_seen TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS labels (
  file_id TEXT PRIMARY KEY,
  doc_type TEXT,
  product_line TEXT,
  model TEXT,
  software_version TEXT,
  software_version_other TEXT,
  hardware_version TEXT,
  hardware_version_other TEXT,
  subsystem TEXT,
  audience TEXT,
  priority TEXT DEFAULT 'Medium',
  lifecycle TEXT DEFAULT 'Active',
  confidentiality TEXT DEFAULT 'Internal',
  keywords TEXT,
  source TEXT,        -- heuristic | llm | human
  confidence REAL,    -- 0..1
  needs_review INTEGER DEFAULT 1,
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(file_id) REFERENCES documents(file_id)
);

CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id TEXT,
  field TEXT,
  old_value TEXT,
  new_value TEXT,
  actor TEXT,         -- pipeline | reviewer:<user>
  at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS templates (
  id TEXT PRIMARY KEY,
  name TEXT,
  attached_count INTEGER DEFAULT 0
);
