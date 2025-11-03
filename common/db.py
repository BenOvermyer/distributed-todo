# common/db.py
import sqlite3
from datetime import datetime
from pathlib import Path

def get_conn(DB_PATH):
    """
    Return a SQLite connection to app.db.
    This also enables foreign key support (future-proof for relationships).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(DB_PATH):
    """
    Ensure the tasks table exists.
    Task schema (from Initial Design and Structure):
        id            INTEGER PRIMARY KEY AUTOINCREMENT
        username      TEXT NOT NULL
        content       TEXT NOT NULL
        is_completed  INTEGER NOT NULL DEFAULT 0
        due_date      TEXT
        created_at    TEXT NOT NULL
        updated_at    TEXT NOT NULL
    """
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            is_completed INTEGER NOT NULL DEFAULT 0,
            due_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()

def create_task(content: str, username: str, DB_PATH: str) -> int:
    """
    Insert a new task into the tasks table.

    Args:
        content: text of the task (e.g. "Finish report")
        username: owner/creator of task. default stub for now.
        due_date: optional due date string (e.g. "2025-11-01"), can be None.

    Returns:
        The new task's integer id.
    """
    # make sure table exists before insert
    init_db(DB_PATH)

    now = datetime.now().isoformat(timespec="seconds")

    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tasks (
            username,
            content,
            is_completed,
            due_date,
            created_at,
            updated_at
        )
        VALUES (?, ?, 0, ?, ?, ?)
        """,
        (username, content, None, now, now),
    )

    task_id = cur.lastrowid
    conn.commit()
    conn.close()

    return task_id
