"""
models.py - Database schema definition and connection management.

Uses SQLite with WAL mode for better concurrency.
All schema changes live here; run init_db() once on startup.
"""

import sqlite3
import os
from config import config


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """
    Return a new SQLite connection with row_factory set so results look
    like dictionaries.  The caller is responsible for closing it.

    Reads DATABASE_URL fresh from the environment each call so test
    overrides (os.environ["DATABASE_URL"] = ":memory:") are respected.
    """
    db_url = os.environ.get("DATABASE_URL", config.DATABASE_URL)
    conn = sqlite3.connect(db_url)
    conn.row_factory = sqlite3.Row        # dict-like access: row["column"]
    conn.execute("PRAGMA foreign_keys = ON")   # enforce FK constraints
    conn.execute("PRAGMA journal_mode = WAL")  # better concurrency
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT    UNIQUE NOT NULL,
    email        TEXT    UNIQUE NOT NULL,
    password_hash TEXT   NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS profiles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER UNIQUE NOT NULL,
    bio           TEXT,
    avatar_url    TEXT,
    avg_looks     REAL    DEFAULT 0.0,
    avg_style     REAL    DEFAULT 0.0,
    avg_vibe      REAL    DEFAULT 0.0,
    avg_overall   REAL    DEFAULT 0.0,
    review_count  INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

CREATE_REVIEWS_TABLE = """
CREATE TABLE IF NOT EXISTS reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    reviewer_user_id    INTEGER NOT NULL,
    reviewed_profile_id INTEGER NOT NULL,
    looks_rating        INTEGER NOT NULL CHECK(looks_rating >= 1 AND looks_rating <= 10),
    style_rating        INTEGER NOT NULL CHECK(style_rating >= 1 AND style_rating <= 10),
    vibe_rating         INTEGER NOT NULL CHECK(vibe_rating  >= 1 AND vibe_rating  <= 10),
    feedback_text       TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (reviewer_user_id, reviewed_profile_id),
    FOREIGN KEY (reviewer_user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (reviewed_profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
"""


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables if they don't already exist.
    Safe to call on every startup – idempotent.
    """
    # Ensure the directory for the DB file exists
    db_dir = os.path.dirname(os.path.abspath(config.DATABASE_URL))
    os.makedirs(db_dir, exist_ok=True)

    with get_db() as conn:
        conn.execute(CREATE_USERS_TABLE)
        conn.execute(CREATE_PROFILES_TABLE)
        conn.execute(CREATE_REVIEWS_TABLE)
        conn.commit()


def recalculate_profile_ratings(conn: sqlite3.Connection, profile_id: int) -> None:
    """
    Recompute and persist the cached average ratings for *profile_id*.
    Called after any review insert / update / delete to keep the profile
    row in sync without relying on expensive sub-queries at read time.
    """
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                          AS cnt,
            COALESCE(AVG(CAST(looks_rating AS REAL)), 0.0)   AS avg_looks,
            COALESCE(AVG(CAST(style_rating AS REAL)), 0.0)   AS avg_style,
            COALESCE(AVG(CAST(vibe_rating  AS REAL)), 0.0)   AS avg_vibe
        FROM reviews
        WHERE reviewed_profile_id = ?
        """,
        (profile_id,),
    ).fetchone()

    avg_overall = round((row["avg_looks"] + row["avg_style"] + row["avg_vibe"]) / 3, 2)

    conn.execute(
        """
        UPDATE profiles
        SET avg_looks    = ?,
            avg_style    = ?,
            avg_vibe     = ?,
            avg_overall  = ?,
            review_count = ?,
            updated_at   = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            round(row["avg_looks"], 2),
            round(row["avg_style"], 2),
            round(row["avg_vibe"], 2),
            avg_overall,
            row["cnt"],
            profile_id,
        ),
    )
