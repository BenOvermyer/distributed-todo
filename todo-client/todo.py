# todo-client/todo.py
import sys
from pathlib import Path

# Make sure Python can import the 'common' package when run as a script.
# We'll add project root to sys.path so "import common.db" works even if
# you call `python todo-client/todo.py ...`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.db import create_task  # after path fix

USAGE = """Usage:
  python todo-client/todo.py create "Task content here"

Example:
  python todo-client/todo.py create "Add task creation"
"""

def handle_create(args):
    # args will be the list after the word 'create'
    # e.g. ["Add", "task", "creation"] or ['Add task creation']
    if not args:
        print("Error: missing task content.\n")
        print(USAGE)
        sys.exit(1)

    # Join the rest of the args as the task content.
    task_content = " ".join(args).strip().strip('"').strip("'")

    if not task_content:
        print("Error: task content cannot be empty.")
        sys.exit(1)

    new_id = create_task(task_content)

    print(f"✅ Created task #{new_id}: {task_content}")

def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    command = sys.argv[1].lower()
    args_after_command = sys.argv[2:]

    if command == "create":
        handle_create(args_after_command)
    else:
        print(f"Unknown command: {command}\n")
        print(USAGE)
        sys.exit(1)

if __name__ == "__main__":
    main()
