import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript(
    """
CREATE TABLE IF NOT EXISTS footprints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  temp TEXT DEFAULT '--',
  sunrise TEXT DEFAULT '--',
  sunset TEXT DEFAULT '--'
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diary (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  day INTEGER NOT NULL,
  content TEXT NOT NULL,
  image_url TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(year, month, day)
);

INSERT OR IGNORE INTO footprints (name, temp, sunrise, sunset) VALUES
  ('北京', '18°C', '05:12', '19:30'),
  ('广州', '28°C', '06:05', '18:50'),
  ('杭州', '22°C', '05:40', '18:55'),
  ('深圳', '27°C', '06:08', '18:48');
"""
)

conn.commit()
conn.close()
print(f"数据库已创建: {DB_PATH}")