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

## Running the Production-Mode Server

To run the server in production mode, you can use Docker Compose.

Just run the following from the repository root:

```bash
docker compose up
```

The server will be available at [http://localhost:8030](http://localhost:8030).
