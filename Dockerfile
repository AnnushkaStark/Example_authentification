ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim AS base

RUN pip install --no-cache-dir uv

RUN adduser --disabled-password --gecos "" --home /home/appuser appuser
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /home/appuser

ENV UV_CACHE_DIR="/home/appuser/.cache/uv" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH="/app/src" 

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/home/appuser/.cache/uv \
    uv venv /app/.venv && \
    uv sync --frozen --no-install-project --no-dev
 
    
COPY . .

RUN --mount=type=cache,target=/home/appuser/.cache/uv \
    uv sync --frozen --no-dev


RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app/.venv

USER appuser


CMD  ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]