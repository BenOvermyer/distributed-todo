FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . /app

RUN cp /app/todo_server_config.ini /app/todo-server/config.ini

WORKDIR /app/todo-server
RUN uv sync --frozen --no-cache

ENV TODO_SERVER_CONFIG_PATH="/app/todo-server/config.ini"

CMD ["/app/.venv/bin/fastapi", "run", "src/todo_server/main.py", "--port", "80", "--host", "0.0.0.0"]
