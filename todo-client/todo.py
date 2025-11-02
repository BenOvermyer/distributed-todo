# todo-client/todo.py
import argparse
import sys
from pathlib import Path

# Make sure Python can import the 'common' package when run as a script.
# We'll add project root to sys.path so "import common.db" works even if
# you call `python todo-client/todo.py ...`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.db import create_task  # after path fix
from common.config import load_config, init_config_file

def handle_create(config, content):
    if not content:
        print("Error: missing task content.\n")
        sys.exit(1)

    new_id = create_task(content, config.get("username", "default_user"), config.get("database_file", "todo_client.db"))

    print(f"✅ Created task #{new_id}: {content}")

def handle_init():
    print("Initializing config...")

    init_config_file("client")

    print("✅ Initialization complete.")


def main():
    parser = argparse.ArgumentParser(description="Todo Client CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create subparser for the "create" command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("content", help="Content of the task")

    # Create subparser for the "init" command
    init_parser = subparsers.add_parser("init", help="Initialize the client configuration")

    parsed_args = parser.parse_args()

    command = parsed_args.command.lower()

    if command == "init":
        handle_init()

    config = load_config("client")

    if command == "create":
        handle_create(config, parsed_args.content)

if __name__ == "__main__":
    main()
