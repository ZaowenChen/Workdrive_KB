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
  model_type TEXT,
  subsystem TEXT,
  language TEXT,
  hardware_version TEXT,
  software_version TEXT,
  priority TEXT,
  audience_level TEXT,
  source TEXT,        -- heuristic | llm | human
  confidence REAL,    -- 0..1
  needs_review INTEGER DEFAULT 1,
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
