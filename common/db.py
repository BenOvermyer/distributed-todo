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

def list_tasks(
    username: str,
    DB_PATH: str,
    only_today: bool = False,
    only_completed: bool = False,
) -> str:
    """
    Return tasks as a pretty ASCII table based on flags.

    Flags:
      --today       : due today (by due_date)
      --completed   : completed tasks
      both together : tasks completed today (ignores due_date)

    Author: awais
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    # Build WHERE clause
    where = ["username = ?"]
    params = [username]

    if only_today and only_completed:
        # Completed *today* — ignore due date
        where.append("is_completed = 1")
        # Compare the DATE portion of updated_at against local "today"
        where.append("DATE(updated_at) = DATE('now','localtime')")
    elif only_today:
        # Due today (due_date must match today's date)
        # If due_date is stored as 'YYYY-MM-DD' it will match; if ISO, DATE(...) will extract
        where.append("due_date IS NOT NULL")
        where.append("DATE(due_date) = DATE('now','localtime')")
    elif only_completed:
        where.append("is_completed = 1")

    where_sql = " AND ".join(where)

    cur.execute(
        f"""
        SELECT id, content, is_completed, COALESCE(due_date, ''), created_at, updated_at
        FROM tasks
        WHERE {where_sql}
        ORDER BY created_at ASC
        """,
        tuple(params),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        note = "No tasks found"
        if only_today and only_completed:
            note += " (completed today) ✅"
        elif only_today:
            note += " (due today) ✅"
        elif only_completed:
            note += " (completed) ✅"
        else:
            note += " ✅"
        return note

    # Header
    header = f"{'ID':<4} | {'Task':<40} | {'Due Date':<12} | {'Completed':<10} | {'Created'}"
    line   = "-" * len(header)
    table_lines = [header, line]

    for (task_id, content, is_completed, due_date, created_at, _updated_at) in rows:
        content_display = (content[:37] + "...") if len(content) > 40 else content
        is_done = "✅" if is_completed else "❌"
        due_display = due_date if due_date else "--"
        created_date = (created_at or "").split("T")[0] if created_at else ""
        table_lines.append(
            f"{task_id:<4} | {content_display:<40} | {due_display:<12} | {is_done:<10} | {created_date}"
        )

    return "\n".join(table_lines)

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
