import os
import tempfile
import sys
from pathlib import Path
from datetime import datetime

# Ensure the project root is in sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common import db
from common.task import Task

"""
These tests cover operations in common/db.py. 

We use a temporary database file in order to not pollute the real database
while still letting us test real database interactions.

NOTE: These tests were written with GitHub Copilot's help.
"""

def test_init_db_creates_table():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        db_path = tf.name
    try:
        db.init_db(db_path)
        conn = db.get_conn(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';")

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
