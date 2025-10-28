# distributed-todo

A distributed To Do TUI application for ENGI 9818 F25

## Development

This project uses [FastAPI](https://fastapi.tiangolo.com/).

To install dependencies, make sure you have `uv` installed (See [the uv docs](https://docs.astral.sh/uv/getting-started/installation/)). Then, run the following:

```bash
uv sync
```

To run the server in development mode, run this:

```bash
uv run fastapi dev
```

To halt the server, just enter `^C`.

To run the client, enter the todo-client directory and run this:

```bash
uv run todo.py
```
