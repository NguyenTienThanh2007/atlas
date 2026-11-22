FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY app ./app
COPY migrations ./migrations

RUN useradd --system --uid 10001 atlas
USER atlas
EXPOSE 8000
# Migrate, seed reference data (idempotent), then serve. Startup stops if a migration or the seed
# fails outright (exit 1); a recorded-but-not-applied reference conflict (exit 2) is logged only.
CMD ["sh", "-c", "alembic upgrade head && { python -m app.ingestion reference || [ $? -eq 2 ]; } && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
