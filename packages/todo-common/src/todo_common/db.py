# common/db.py
import sqlite3
from datetime import datetime

from todo_common.task import Task


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
    Task schema:
        id            INTEGER PRIMARY KEY AUTOINCREMENT
        username      TEXT NOT NULL
        content       TEXT NOT NULL
        is_completed  INTEGER NOT NULL DEFAULT 0
        is_deleted    INTEGER NOT NULL DEFAULT 0
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
            is_deleted INTEGER NOT NULL DEFAULT 0,
            due_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()


def add_full_task(task: Task, DB_PATH: str, use_existing_id: bool = True) -> None:
    """
    Insert a full Task object into the tasks table.
    Used for syncing tasks from server to client or vice versa.
    """
    init_db(DB_PATH)

    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    if use_existing_id:
        cur.execute(
            """
            INSERT INTO tasks (
                id,
                username,
                content,
                is_completed,
                is_deleted,
                due_date,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.username,
                task.content,
                int(task.is_completed),
                int(task.is_deleted),
                task.due_date,
                task.created_at,
                task.updated_at,
            ),
        )
    else:
        cur.execute(
            """
            INSERT INTO tasks (
                username,
                content,
                is_completed,
                is_deleted,
                due_date,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.username,
                task.content,
                int(task.is_completed),
                int(task.is_deleted),
                task.due_date,
                task.created_at,
                task.updated_at,
            ),
        )

    conn.commit()
    conn.close()


def complete_task(task_id: int, DB_PATH: str) -> None:
    """
    Mark the given task as completed in the database.

    NOTE: the original plan was to delete completed tasks after a
    certain number were reached, but that was a performance optimization
    that may be premature. Leaving that feature out for now.
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        UPDATE tasks
        SET is_completed = 1,
            updated_at = ?
        WHERE id = ?
        """,
        (now, task_id),
    )
    conn.commit()
    conn.close()


def create_task(content: str, username: str, DB_PATH: str) -> Task:
    """
    Insert a new task into the tasks table.

    Args:
        content: text of the task (e.g. "Finish report")
        username: owner/creator of task. default stub for now.

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
            is_deleted,
            due_date,
            created_at,
            updated_at
        )
        VALUES (?, ?, 0, 0, ?, ?, ?)
        """,
        (username, content, None, now, now),
    )

    task_id = cur.lastrowid
    conn.commit()
    conn.close()

    return Task(
        id=task_id,
        username=username,
        content=content,
        is_completed=False,
        is_deleted=False,
        due_date=None,
        created_at=now,
        updated_at=now,
    )


def create_tasks_from_rows(rows: list[tuple]) -> list[Task]:
    """
    Convert a list of database rows into a list of Task objects.
    Each row is expected to be a tuple in the order:
    (id, username, content, is_completed, due_date, created_at, updated_at)
    """
    tasks = []
    for (
        task_id,
        username,
        content,
        is_completed,
        is_deleted,
        due_date,
        created_at,
        updated_at,
    ) in rows:
        tasks.append(
            Task(
                id=task_id,
                username=username,
                content=content,
                is_completed=bool(is_completed),
                is_deleted=bool(is_deleted),
                due_date=due_date,
                created_at=created_at,
                updated_at=updated_at,
            )
        )
    return tasks


def get_task(task_id: int, DB_PATH: str) -> Task | None:
    """
    Return a Task object for the given task_id, or None if not found.
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, content, is_completed, is_deleted, due_date, created_at, updated_at
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    (
        task_id,
        username,
        content,
        is_completed,
        is_deleted,
        due_date,
        created_at,
        updated_at,
    ) = row
    return Task(
        id=task_id,
        username=username,
        content=content,
        is_completed=bool(is_completed),
        is_deleted=bool(is_deleted),
        due_date=due_date,
        created_at=created_at,
        updated_at=updated_at,
    )


def get_tasks_for_user(username: str, DB_PATH: str) -> list[Task]:
    """
    Return all tasks for a given username as a list of Task objects.
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, content, is_completed, is_deleted, due_date, created_at, updated_at
        FROM tasks
        WHERE username = ?
        ORDER BY created_at ASC
        """,
        (username,),
    )
    rows = cur.fetchall()
    conn.close()

    return create_tasks_from_rows(rows)


def get_tasks_for_user_filtered(
    username: str, DB_PATH: str, only_completed: bool = False, only_today: bool = False
) -> list[Task]:
    """
    Return tasks for a given username as a list of Task objects, filtered by completion status and/or due date.

    Args:
        username: the username whose tasks to retrieve
        DB_PATH: path to the SQLite database file
        only_completed: if True, return only completed tasks
        only_today: if True, return only tasks due today (or, if combined with only_completed, tasks completed today)
    """

    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    # Build WHERE clause
    where = ["username = ?"]
    params = [username]

    # Unless the user wants to see completed tasks, filter them out
    if only_completed:
        where.append("is_completed = 1")
    else:
        where.append("is_completed = 0")

    # Handle today/due date filtering
    if only_today and only_completed:
        # Completed *today* — ignore due date
        where.append("DATE(updated_at) = DATE('now','localtime')")
    elif only_today:
        # Due today (due_date must match today's date)
        where.append("due_date IS NOT NULL")
        where.append("DATE(due_date) = DATE('now','localtime')")

    where.append("is_deleted = 0")
    where_sql = " AND ".join(where)

    cur.execute(
        f"""
        SELECT id, username, content, is_completed, is_deleted, due_date, created_at, updated_at
        FROM tasks
        WHERE {where_sql}
        ORDER BY created_at ASC
        """,
        tuple(params),
    )
    rows = cur.fetchall()
    conn.close()

    return create_tasks_from_rows(rows)


def get_users(DB_PATH: str) -> list[str]:
    """
    Return a list of all usernames in the tasks database.
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT DISTINCT username
        FROM tasks
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [row[0] for row in rows]


def sync_task(task: Task, DB_PATH: str) -> None:
    """
    Insert or update a task in the database based on its ID.
    If the task with the given ID exists, update it; otherwise, insert it.
    """
    # Check if task with given ID exists
    existing_task = get_task(task.id, DB_PATH)

    if existing_task is None:
        add_full_task(task, DB_PATH)
        return

    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    # If the existing task has been updated more recently, skip updating
    if existing_task.updated_at >= task.updated_at:
        return

    # If the created_at timestamps differ, then these are divergent tasks and we want to keep both
    if (
        existing_task.created_at != task.created_at
        and existing_task.content != task.content
    ):
        add_full_task(task, DB_PATH, use_existing_id=False)
        return

    # Update existing task
    cur.execute(
        """
        UPDATE tasks
        SET username = ?,
            content = ?,
            is_completed = ?,
            is_deleted = ?,
            due_date = ?,
            created_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            task.username,
            task.content,
            int(task.is_completed),
            int(task.is_deleted),
            task.due_date,
            task.created_at,
            task.updated_at,
            task.id,
        ),
    )

    conn.commit()
    conn.close()


def uncomplete_task(task_id: int, DB_PATH: str) -> None:
    """
    Mark the given task as not completed in the database.
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        UPDATE tasks
        SET is_completed = 0,
            updated_at = ?
        WHERE id = ?
        """,
        (now, task_id),
    )
    conn.commit()
    conn.close()


def update_task_content(task_id: int, new_content: str, DB_PATH: str) -> None:
    """
    Update the content of the given task in the database.

    Args:
        task_id: ID of the task to update
        new_content: new text content for the task
        DB_PATH: path to the SQLite database file
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        UPDATE tasks
        SET content = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (new_content, now, task_id),
    )
    conn.commit()
    conn.close()


def set_due_date(task_id: int, due_date: str, DB_PATH: str) -> None:
    """
    Set the due date for the given task in the database.

    Args:
        task_id: ID of the task to update
        due_date: Date string in YYYY-MM-DD format
        DB_PATH: path to the SQLite database file
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        UPDATE tasks
        SET due_date = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (due_date, now, task_id),
    )
    conn.commit()
    conn.close()


def remove_due_date(task_id: int, DB_PATH: str) -> None:
    """
    Remove the due date from the given task in the database.

    Args:
        task_id: ID of the task to update
        DB_PATH: path to the SQLite database file
    """
    init_db(DB_PATH)
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        UPDATE tasks
        SET due_date = NULL,
            updated_at = ?
        WHERE id = ?
        """,
        (now, task_id),
    )
    conn.commit()
    conn.close()
