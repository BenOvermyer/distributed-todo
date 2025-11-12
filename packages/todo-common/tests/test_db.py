import pytest
import os
import tempfile
import sys
import time
from datetime import datetime, timedelta

# Ensure the project root is in sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from todo_common import db
from todo_common.task import Task

"""
These tests cover operations in common/db.py. 

We use a temporary database file in order to not pollute the real database
while still letting us test real database interactions.

NOTE: These tests were written with GitHub Copilot's help.
"""

# Fixtures for multiple test databases (server and two clients)
@pytest.fixture(scope="function")
def test_dbs():
    db_files = {}
    for who in ["server", "client1", "client2"]:
        tf = tempfile.NamedTemporaryFile(delete=False)
        db_files[who] = tf.name
        tf.close()
        db.init_db(db_files[who])
    yield db_files
    for f in db_files.values():
        os.remove(f)


# Test: syncing a new task from client1 to server
def test_sync_new_task_from_client_to_server(test_dbs):
    client_db = test_dbs["client1"]
    server_db = test_dbs["server"]

    # Client creates a new task
    task = db.create_task("Test sync task", "alice", client_db)
    # Simulate sync: push to server
    db.sync_task(task, server_db)

    # Server should now have the task
    server_task = db.get_task(task.id, server_db)
    assert server_task is not None
    assert server_task.content == "Test sync task"
    assert server_task.username == "alice"


# Test: syncing a task update from client to server
def test_sync_task_update_from_client_to_server(test_dbs):
    client_db = test_dbs["client1"]
    server_db = test_dbs["server"]

    # Client creates and syncs a task
    task = db.create_task("Initial content", "alice", client_db)
    time.sleep(1)  # Ensure updated_at will differ
    db.sync_task(task, server_db)

    # Client updates the task and persists the update
    updated_task = db.get_task(task.id, client_db)
    new_content = "Updated content"
    db.update_task_content(updated_task.id, new_content, client_db)
    time.sleep(1)  # Ensure updated_at will differ

    # Now fetch the updated task and sync to server
    updated_task = db.get_task(task.id, client_db)
    db.sync_task(updated_task, server_db)

    # Server should reflect the update
    server_task = db.get_task(task.id, server_db)
    assert server_task.content == "Updated content"


# Test: cross-client new task sync
def test_cross_client_new_task_sync(test_dbs):
    client1_db = test_dbs["client1"]
    client2_db = test_dbs["client2"]
    server_db = test_dbs["server"]

    # Client 1 creates a task
    task1 = db.create_task("Task from client1", "alice", client1_db)
    time.sleep(1) # Pause for a moment to ensure different timestamps

    # Client 2 creates a different task
    task2 = db.create_task("Task from client2", "alice", client2_db)
    time.sleep(1)  # Pause for a moment to ensure different timestamps

    client1_tasks = db.get_tasks_for_user("alice", client1_db)
    client2_tasks = db.get_tasks_for_user("alice", client2_db)

    # Client 1 syncs to server
    for t in client1_tasks:
        db.sync_task(t, server_db)

    time.sleep(1)  # Pause for a moment to ensure different timestamps

    # Client 2 syncs to server
    for t in client2_tasks:
        db.sync_task(t, server_db)

    time.sleep(1)  # Pause for a moment to ensure different timestamps

    server_tasks = db.get_tasks_for_user("alice", server_db)

    # Now client 1 syncs from server
    db.sync_tasks(server_tasks, client1_db, clear_first=True)

    # Now client 2 syncs from server
    db.sync_tasks(server_tasks, client2_db, clear_first=True)

    # Both clients should have both tasks
    client1_tasks = db.get_tasks_for_user("alice", client1_db)
    client2_tasks = db.get_tasks_for_user("alice", client2_db)
    assert any(t.content == "Task from client1" for t in client1_tasks)
    assert any(t.content == "Task from client2" for t in client1_tasks)
    assert any(t.content == "Task from client1" for t in client2_tasks)
    assert any(t.content == "Task from client2" for t in client2_tasks)


# Test: conflict scenario (two clients update same task differently before syncing)
def test_conflict_scenario(test_dbs):
    client1_db = test_dbs["client1"]
    client2_db = test_dbs["client2"]
    server_db = test_dbs["server"]

    # Client 1 creates and syncs a task
    task = db.create_task("Original", "alice", client1_db)
    db.sync_task(task, server_db)

    # Client 2 fetches the task from server
    db.sync_task(task, client2_db)

    # Both clients update the task differently
    t1 = db.get_task(task.id, client1_db)
    t2 = db.get_task(task.id, client2_db)

    t1.content = "Client1 update"
    db.update_task_content(t1.id, t1.content, client1_db)
    time.sleep(1)  # Pause for a moment to ensure client 2's update is newer

    t2.content = "Client2 update"
    db.update_task_content(t2.id, t2.content, client2_db)

    # Client 2 syncs to server
    t2_task = db.get_task(t2.id, client2_db)
    db.sync_task(t2_task, server_db)
    time.sleep(1)

    # Client 1 syncs to server
    t1_task = db.get_task(t1.id, client1_db)
    db.sync_task(t1_task, server_db)

    # Server should have the latest update (Client2's)
    server_task = db.get_task(task.id, server_db)
    assert server_task.content == "Client2 update"


def test_init_db_creates_table():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        conn = db.get_conn(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';"
        )

        assert cur.fetchone() is not None

        conn.close()
    finally:
        os.remove(db_path)


def test_create_and_get_task():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        task = db.create_task("Test task", "alice", db_path)

        assert isinstance(task, Task)

        fetched = db.get_task(task.id, db_path)

        assert fetched is not None
        assert fetched.content == "Test task"
        assert fetched.username == "alice"
    finally:
        os.remove(db_path)


def test_get_tasks_for_user():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        db.create_task("Task 1", "bob", db_path)
        db.create_task("Task 2", "bob", db_path)
        db.create_task("Task 3", "carol", db_path)

        tasks = db.get_tasks_for_user("bob", db_path)

        assert len(tasks) == 2
        assert all(t.username == "bob" for t in tasks)
    finally:
        os.remove(db_path)


def test_get_tasks_for_user_filtered_completed():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        db.create_task("Task 1", "dave", db_path)
        t2 = db.create_task("Task 2", "dave", db_path)

        # Mark t2 as completed
        db.complete_task(t2.id, db_path)
        completed = db.get_tasks_for_user_filtered("dave", db_path, only_completed=True)

        assert len(completed) == 1
        assert completed[0].id == t2.id
    finally:
        os.remove(db_path)


def test_get_tasks_for_user_filtered_today():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        t1 = db.create_task("Task 1", "eve", db_path)
        # Set due_date to today

        today = datetime.now().strftime("%Y-%m-%d")
        conn = db.get_conn(db_path)
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET due_date=? WHERE id=?", (today, t1.id))
        conn.commit()
        conn.close()
        today_tasks = db.get_tasks_for_user_filtered("eve", db_path, only_today=True)
        assert len(today_tasks) == 1
        assert today_tasks[0].id == t1.id
    finally:
        os.remove(db_path)


def test_complete_and_uncomplete_task():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        task = db.create_task("Finish assignment", "frank", db_path)

        # Initially not completed
        fetched = db.get_task(task.id, db_path)

        assert fetched is not None
        assert not fetched.is_completed

        # Complete the task
        db.complete_task(task.id, db_path)
        completed = db.get_task(task.id, db_path)

        assert completed.is_completed

        # Uncomplete the task
        db.uncomplete_task(task.id, db_path)
        uncompleted = db.get_task(task.id, db_path)

        assert not uncompleted.is_completed
    finally:
        os.remove(db_path)


def test_set_due_date():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        task = db.create_task("Task with due date", "grace", db_path)

        # Initially no due date
        fetched = db.get_task(task.id, db_path)
        assert fetched is not None
        assert fetched.due_date is None

        # Set a due date
        due_date = "2025-12-01"
        db.set_due_date(task.id, due_date, db_path)
        updated = db.get_task(task.id, db_path)

        assert updated is not None
        assert updated.due_date == due_date
    finally:
        os.remove(db_path)


def test_remove_due_date():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        task = db.create_task("Task with due date", "henry", db_path)

        # Set a due date first
        due_date = "2025-12-01"
        db.set_due_date(task.id, due_date, db_path)
        with_due_date = db.get_task(task.id, db_path)
        assert with_due_date.due_date == due_date

        # Remove the due date
        db.remove_due_date(task.id, db_path)
        without_due_date = db.get_task(task.id, db_path)

        assert without_due_date is not None
        assert without_due_date.due_date is None
    finally:
        os.remove(db_path)


def test_set_and_remove_due_date():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        task = db.create_task("Task for due date testing", "iris", db_path)

        # Initially no due date
        assert db.get_task(task.id, db_path).due_date is None

        # Set first due date
        db.set_due_date(task.id, "2025-12-01", db_path)
        assert db.get_task(task.id, db_path).due_date == "2025-12-01"

        # Update to a different due date
        db.set_due_date(task.id, "2025-12-25", db_path)
        assert db.get_task(task.id, db_path).due_date == "2025-12-25"

        # Remove due date
        db.remove_due_date(task.id, db_path)
        assert db.get_task(task.id, db_path).due_date is None
    finally:
        os.remove(db_path)


def test_update_task_content_success():
    import time

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        task = db.create_task("Original content", "jane", db_path)
        fetched = db.get_task(task.id, db_path)
        assert fetched.content == "Original content"
        old_updated_at = fetched.updated_at
        # Ensure updated_at will change
        time.sleep(1)
        db.update_task_content(task.id, "Updated content", db_path)
        updated = db.get_task(task.id, db_path)
        assert updated.content == "Updated content"
        assert updated.updated_at != old_updated_at
    finally:
        os.remove(db_path)


def test_update_task_content_nonexistent():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        # No tasks created, update nonexistent id
        db.update_task_content(9999, "Should not fail", db_path)
        # Should not raise, and no tasks should exist
        conn = db.get_conn(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tasks;")
        count = cur.fetchone()[0]
        assert count == 0
        conn.close()
    finally:
        os.remove(db_path)
