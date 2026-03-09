FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

# Copy dependency files only
COPY pyproject.toml uv.lock* ./

# Install Python dependencies using uv
RUN uv venv && \
    uv pip install --upgrade pip && \
    uv sync --locked --no-cache --no-dev

# Copy rest of the code
COPY . .

CMD ["uv", "run", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]