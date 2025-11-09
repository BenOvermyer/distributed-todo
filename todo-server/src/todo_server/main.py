
import os
import sys
from dataclasses import asdict
from todo_common.config import load_config
from todo_common.db import get_tasks_for_user, get_users, sync_task
from todo_common.task import Task
from fastapi import FastAPI


app = FastAPI()


def get_database() -> str:
    # From config or environment, return the path to the server database
    database_file = "todo_server.db"
    config_path = os.environ.get("TODO_SERVER_CONFIG_PATH", None)
    try:
        config = load_config("server", config_path=config_path)
        database_file = config.get("database_file", database_file)
    except Exception:
        print("Error: Could not load server config file.")
        sys.exit(1)
    return database_file


db = get_database()


@app.get("/")
def read_root():
    return {"todo_server_version": "0.1.0"}


@app.get("/users")
def read_users():
    users = get_users(db)
    return {"users": users}


@app.post("/sync")
def sync_tasks(payload: dict):
    # Validate and process the incoming request from the client
    try:
        assert "tasks" in payload
    except AssertionError:
        print("Invalid payload: 'tasks' key missing")
        return {"error": "Invalid payload: 'tasks' key missing"}, 400

    try:
        assert "username" in payload
    except AssertionError:
        print("Invalid payload: 'username' key missing")
        return {"error": "Invalid payload: 'username' key missing"}, 400

    tasks = payload.get("tasks", [])
    username = payload.get("username")

    print(f"Syncing tasks for user {username}, {len(tasks)} tasks received.")

    for task in tasks:
        sync_task(Task(**task), db)

    synced_tasks = get_tasks_for_user(username, db)

    return {"status": "success", "tasks": [asdict(task) for task in synced_tasks]}
