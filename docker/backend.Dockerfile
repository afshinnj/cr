# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app ./app

RUN pip install --upgrade pip \
    && pip install ".[analysis]" \
    && pip install "psycopg[binary]"

COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY config /config
COPY scripts /scripts

ENV CONFIG_DIR=/config

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 amip && chown -R amip:amip /app
USER amip

EXPOSE 8787

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8787"]
