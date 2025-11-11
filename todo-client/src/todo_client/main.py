import argparse
import requests
import sys
from dataclasses import asdict
from todo_common.db import (
    add_full_task,
    complete_task,
    create_task,
    uncomplete_task,
    update_task_content,
)
from todo_common.db import (
    get_tasks_for_user,
    get_tasks_for_user_filtered,
    set_due_date,
    remove_due_date,
)
from todo_common.config import load_config, init_config_file
from todo_common.task import Task
from todo_client.display import get_task_table


def handle_list(config, only_today, only_completed):
    tasks = get_tasks_for_user_filtered(
        config.get("username", "default_user"),
        config.get("database_file", "todo_client.db"),
        only_completed=only_completed,
        only_today=only_today,
    )

    table_output = get_task_table(tasks)
    print(table_output)


def handle_complete(config, task_id: str):
    complete_task(task_id, config.get("database_file", "todo_client.db"))
    print(f"✅ Marked task #{task_id} as complete.")


def handle_create(config, content):
    if not content:
        print("Error: missing task content.\n")
        sys.exit(1)

    new_task = create_task(
        content,
        config.get("username", "default_user"),
        config.get("database_file", "todo_client.db"),
    )

    print(f"✅ Created task #{new_task.id}: {new_task.content}")


def handle_init():
    print("Initializing config...")

    init_config_file("client")

    print("✅ Initialization complete.")


def handle_sync(config):
    remote_server = config.get("server_url", "http://localhost:8030")
    username = config.get("username", "default_user")
    print(f"Syncing with remote server {remote_server}...")

    local_tasks = get_tasks_for_user(
        username,
        config.get("database_file", "todo_client.db"),
    )
    tasks_data = [asdict(task) for task in local_tasks]
    payload = {"tasks": tasks_data, "username": username}
    response = requests.post(f"{remote_server}/sync", json=payload)

    if response.status_code != 200:
        print(f"Error: Failed to sync with server. Status code: {response.status_code}")
        sys.exit(1)

    server_response = response.json()
    
    # Easiest way to ensure consistency is to just overwrite local db with server state
    with open(config.get("database_file", "todo_client.db"), "w"):
        pass  # Clear local database file

    for task in server_response.get("tasks", []):
        add_full_task(Task(**task), config.get("database_file", "todo_client.db"))

    print("✅ Sync complete.")


def handle_uncomplete(config, task_id: str):
    uncomplete_task(task_id, config.get("database_file", "todo_client.db"))
    print(f"❌ Marked task #{task_id} as incomplete.")


def handle_update(config, task_id: str, new_content: str):
    print(f"Updating task #{task_id} to new content: {new_content}")
    update_task_content(
        int(task_id), new_content, config.get("database_file", "todo_client.db")
    )
    print(f"✏️ Updated task #{task_id}.")


def handle_due(config, task_id: str, due_date: str):
    print(f"Handling due date for task #{task_id} to {due_date}.")
    import re
    from datetime import datetime

    # Validate date format YYYY-MM-DD
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(date_pattern, due_date):
        print("Error: Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-01).")
        sys.exit(1)

    # Validate that it's a valid date
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-01).")
        sys.exit(1)

    set_due_date(int(task_id), due_date, config.get("database_file", "todo_client.db"))
    print(f"📅 Set due date for task #{task_id} to {due_date}.")


def handle_undue(config, task_id: str):
    remove_due_date(int(task_id), config.get("database_file", "todo_client.db"))
    print(f"📅 Removed due date from task #{task_id}.")


def main():
    parser = argparse.ArgumentParser(description="Todo Client CLI")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create subparser for the "complete" command
    complete_parser = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_parser.add_argument("task_id", help="ID of the task to mark as completed")

    # Create subparser for the "create" command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("content", help="Content of the task")

    # Create subparser for the "init" command
    subparsers.add_parser("init", help="Initialize the client configuration")

    # Create subparser for the "list" command
    list_parser = subparsers.add_parser(
        "list", help="List tasks (optionally filter with --today / --completed)."
    )
    list_parser.add_argument(
        "--today",
        action="store_true",
        help="Show only tasks due today. If combined with --completed, shows tasks completed today (ignores due date).",
    )
    list_parser.add_argument(
        "--completed",
        action="store_true",
        help="Show only completed tasks. If combined with --today, shows tasks completed today.",
    )

    # Create subparser for the "uncomplete" command
    uncomplete_parser = subparsers.add_parser(
        "uncomplete", help="Mark a task as incomplete"
    )
    uncomplete_parser.add_argument(
        "task_id", help="ID of the task to mark as incomplete"
    )

    # Create subparser for the "update" command
    update_parser = subparsers.add_parser("update", help="Update the content of a task")
    update_parser.add_argument("task_id", help="ID of the task to update")
    update_parser.add_argument("new_content", help="New content for the task")

    # Create subparser for the "due" command
    due_parser = subparsers.add_parser("due", help="Set a due date for a task")
    due_parser.add_argument("task_id", help="ID of the task to set due date for")
    due_parser.add_argument(
        "due_date", help="Due date in YYYY-MM-DD format (e.g., 2025-12-01)"
    )

    # Create subparser for the "undue" command
    undue_parser = subparsers.add_parser(
        "undue", help="Remove the due date from a task"
    )
    undue_parser.add_argument("task_id", help="ID of the task to remove due date from")

    # Create subparser for the "sync" command
    subparsers.add_parser("sync", help="Sync local tasks with the remote server")

    parsed_args = parser.parse_args()

    command = parsed_args.command.lower()

    if command == "init":
        handle_init()
        return

    config = load_config("client", config_path=parsed_args.config)

    if command == "complete":
        handle_complete(config, parsed_args.task_id)

    if command == "create":
        handle_create(config, parsed_args.content)

    if command == "list":
        handle_list(
            config,
            only_today=parsed_args.today,
            only_completed=parsed_args.completed,
        )

    if command == "sync":
        handle_sync(config)

    if command == "uncomplete":
        handle_uncomplete(config, parsed_args.task_id)

    if command == "due":
        handle_due(config, parsed_args.task_id, parsed_args.due_date)

    if command == "undue":
        handle_undue(config, parsed_args.task_id)

    if command == "update":
        handle_update(config, parsed_args.task_id, parsed_args.new_content)


if __name__ == "__main__":
    main()
