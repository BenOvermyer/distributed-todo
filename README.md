# Distributed To-Do

A distributed To Do TUI application for ENGI 9818 F25

## Development

This project uses [FastAPI](https://fastapi.tiangolo.com/) for the server and SQLite for both the client and server.

To install dependencies, make sure you have `uv` installed (See [the uv docs](https://docs.astral.sh/uv/getting-started/installation/)). Then, run the following in the repository root:

```bash
uv sync
```

To run the server in development mode, run this from the `todo-server` directory:

```bash
uv run fastapi dev src/todo_server/main.py
```

To halt the server, just enter `^C`.

To run the client, enter the `todo-client` directory and run this:

```bash
uv run todo-client
```

## Testing Synchronization

To test synchronization, follow these steps.

1. First run the server using the instructions in "Running the Production-Mode Server" below.
2. Initialize the client configuration if you haven't already.
3. Create some tasks.
4. Run the sync command.
5. Now, change the database filename in your client config.
6. List your tasks. There should be none.
7. Run the sync command.
8. List your tasks again. You should see the tasks from the previous database file.
9. Update a task.
10. Run the sync command.
11. Change the database filename in your client config back to what it was before.
12. List your tasks. It should reflect what you had before the update in step 9.
13. Run the sync command.
14. List your tasks. It should now have the update from step 9.

## Running the Production-Mode Server

To run the server in production mode, you can use Docker Compose.

Just run the following from the repository root:

```bash
docker compose up
```

The server will be available at [http://localhost:8030](http://localhost:8030).
