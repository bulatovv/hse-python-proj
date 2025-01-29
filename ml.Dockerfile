FROM python:3.12-slim-bookworm as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    POETRY_CACHE_DIR='/root/.cache/pypoetry' \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_REQUESTS_TIMEOUT=60

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install poetry==1.8.0
COPY ml/pyproject.toml ml/poetry.lock ./
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} poetry install --no-root

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV='/app/.venv' \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY ml/ml ml
