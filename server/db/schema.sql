-- Reference schema for InvariantEval platform (SQLite via SQLAlchemy creates tables automatically)

CREATE TABLE IF NOT EXISTS organizations (
  id INTEGER PRIMARY KEY,
  name VARCHAR(200) UNIQUE NOT NULL,
  created_at DATETIME
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  email VARCHAR(200) UNIQUE NOT NULL,
  password_hash VARCHAR(200) NOT NULL,
  created_at DATETIME
);

CREATE TABLE IF NOT EXISTS memberships (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  role VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS api_keys (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  name VARCHAR(100) NOT NULL,
  key_hash VARCHAR(200) NOT NULL,
  created_at DATETIME
);

CREATE TABLE IF NOT EXISTS suites (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  name VARCHAR(200) NOT NULL,
  yaml_content TEXT NOT NULL,
  updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  suite_name VARCHAR(200) NOT NULL,
  run_id VARCHAR(50) UNIQUE NOT NULL,
  provider_mode VARCHAR(20) NOT NULL,
  payload JSON NOT NULL,
  invariant_failures INTEGER DEFAULT 0,
  passed_cases INTEGER DEFAULT 0,
  total_cases INTEGER DEFAULT 0,
  created_at DATETIME
);

CREATE TABLE IF NOT EXISTS online_eval_queue (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  fixture_payload JSON NOT NULL,
  suite_name VARCHAR(200) NOT NULL,
  processed BOOLEAN DEFAULT 0,
  invariant_failed BOOLEAN DEFAULT 0,
  result_detail TEXT,
  created_at DATETIME
);

CREATE TABLE IF NOT EXISTS online_eval_config (
  id INTEGER PRIMARY KEY,
  org_id INTEGER UNIQUE NOT NULL REFERENCES organizations(id),
  sample_rate REAL DEFAULT 0.05,
  mode VARCHAR(20) DEFAULT 'warn',
  alert_threshold INTEGER DEFAULT 3
);
