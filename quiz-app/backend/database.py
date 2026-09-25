"""Database initialization and connection helper for QuizArc."""

import sqlite3
import os

# On Render, use /data (persistent disk). Locally, use the backend dir.
_DATA_DIR = os.environ.get("RENDER_DISK_PATH", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_DATA_DIR, "quiz.db")


def get_connection():
    """Return a new SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables (idempotent) and perform safe migrations."""
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY,
            key  TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            icon TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id            INTEGER PRIMARY KEY,
            category_id   INTEGER NOT NULL,
            question      TEXT NOT NULL,
            option_0      TEXT NOT NULL,
            option_1      TEXT NOT NULL,
            option_2      TEXT NOT NULL,
            option_3      TEXT NOT NULL,
            correct_index INTEGER NOT NULL CHECK(correct_index BETWEEN 0 AND 3),
            difficulty    TEXT NOT NULL CHECK(difficulty IN ('easy','medium','hard')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        /* ── Players (auth + progression) ── */
        CREATE TABLE IF NOT EXISTS players (
            id               INTEGER PRIMARY KEY,
            username         TEXT UNIQUE NOT NULL COLLATE NOCASE,
            pin_hash         TEXT NOT NULL,
            xp               INTEGER NOT NULL DEFAULT 0,
            current_streak   INTEGER NOT NULL DEFAULT 0,
            best_streak      INTEGER NOT NULL DEFAULT 0,
            last_active_date TEXT DEFAULT '',
            created_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        /* ── Auth tokens (7-day sessions) ── */
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT PRIMARY KEY,
            player_id  INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (player_id) REFERENCES players(id)
        );

        /* ── Quiz sessions (anti-tamper single-use tokens) ── */
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            token        TEXT PRIMARY KEY,
            category_id  INTEGER,         -- NULL for daily mixed challenge
            difficulty   TEXT NOT NULL,
            is_daily     INTEGER NOT NULL DEFAULT 0,
            question_ids TEXT NOT NULL,   -- JSON array: [1, 3, 7, ...]
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at   TEXT NOT NULL,
            used         INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        /* ── Scores (verified flag for authenticated players) ── */
        CREATE TABLE IF NOT EXISTS scores (
            id              INTEGER PRIMARY KEY,
            player_name     TEXT NOT NULL,
            player_id       INTEGER,
            category_id     INTEGER,       -- NULL for daily challenge
            difficulty      TEXT NOT NULL,
            score           INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            xp_earned       INTEGER NOT NULL DEFAULT 0,
            is_daily        INTEGER NOT NULL DEFAULT 0,
            verified        INTEGER NOT NULL DEFAULT 0,
            session_token   TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (category_id)   REFERENCES categories(id),
            FOREIGN KEY (player_id)     REFERENCES players(id),
            FOREIGN KEY (session_token) REFERENCES quiz_sessions(token)
        );

        /* ── Daily Challenge completion log ── */
        CREATE TABLE IF NOT EXISTS daily_challenges (
            id             INTEGER PRIMARY KEY,
            player_id      INTEGER NOT NULL,
            completed_date TEXT NOT NULL,
            score          INTEGER NOT NULL,
            xp_earned      INTEGER NOT NULL,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE (player_id, completed_date)
        );
    """)

    # Safe migrations for existing DB
    migrations = [
        "ALTER TABLE players ADD COLUMN xp INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE players ADD COLUMN current_streak INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE players ADD COLUMN best_streak INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE players ADD COLUMN last_active_date TEXT DEFAULT ''",
        "ALTER TABLE quiz_sessions ADD COLUMN is_daily INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE scores ADD COLUMN xp_earned INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE scores ADD COLUMN is_daily INTEGER NOT NULL DEFAULT 0",
    ]
    for m in migrations:
        try:
            conn.execute(m)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
