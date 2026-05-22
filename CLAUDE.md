# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Found is a local image reference and inspiration library desktop application designed for artists, designers, and creators who collect large numbers of images for research and creative work.

## Tech Stack

- **Backend:** SQLite, FastAPI, sqlmodel, uvicorn, alembic, pillow
- **Frontend:** To be determined

## Environment

Python 3.13+ via pyenv virtualenv `found_env`. Activate with:

```
pyenv activate found_env
```

Install dependencies:

```
pip install -r backend/requirements-dev.txt
```

## Commands

All commands run from `backend/`:

```bash
# Run tests
python -m pytest tests/ -v

# Run a single test
python -m pytest tests/test_foundation.py::test_health_check -v

# Start the API server
uvicorn app.main:app --reload
```

## Architecture

This is a local image library management tool — a FastAPI + SQLite backend that indexes images in-place (files are never copied). Phase 1 is the core API engine only; the GUI is Phase 2.

```
backend/
├── app/
│   ├── main.py          # FastAPI app, lifespan, /health
│   ├── api/v1/          # Route modules (one file per resource)
│   ├── core/
│   │   ├── config.py    # Pydantic Settings; reads .env
│   │   └── database.py  # SQLModel engine, get_session dependency
│   ├── models/          # SQLModel table definitions
│   ├── schemas/         # Request/response Pydantic models
│   ├── services/        # Business logic
│   ├── repositories/    # DB query layer
│   └── utils/
├── tests/
│   ├── conftest.py      # engine / session / client fixtures (in-memory SQLite)
│   └── test_*.py
├── data/                # gitignored — runtime DB and thumbnail cache
├── migrations/          # Alembic migration scripts
├── requirements.txt
└── requirements-dev.txt
```

## Key conventions

- All API routes live under `/api/v1`. The `/health` endpoint is root-level.
- Every API response uses a standard envelope: `{"success": true, "data": {}}` / `{"success": false, "error": {"code": "...", "message": "..."}}`.
- Images are never moved or copied — only their paths are stored.
- `get_session` is a FastAPI dependency; tests override it via `app.dependency_overrides`.
- The production SQLite DB path is computed from `config.py` as an absolute path anchored to `backend/`, so it always resolves to `backend/data/database.db` regardless of working directory.
