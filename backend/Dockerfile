FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-cache --no-dev

COPY . .

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]