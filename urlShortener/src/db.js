const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_PATH = process.env.DB_PATH || './data/urls.db';

const dir = path.dirname(DB_PATH);
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL'); 

db.exec(`
  CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT UNIQUE NOT NULL,
    long_url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    creator_ip TEXT
  );

  CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code);

  CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT NOT NULL,
    clicked_at TEXT NOT NULL DEFAULT (datetime('now')),
    referrer TEXT,
    user_agent TEXT,
    ip_hash TEXT,
    country TEXT,
    city TEXT,
    FOREIGN KEY (short_code) REFERENCES urls(short_code)
  );

  CREATE INDEX IF NOT EXISTS idx_clicks_short_code ON clicks(short_code);
  CREATE INDEX IF NOT EXISTS idx_clicks_clicked_at ON clicks(clicked_at);
`);

module.exports = db;