# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Found is a local image reference and inspiration library desktop application designed for artists, designers, and creators who collect large numbers of images for research and creative work.

## Tech Stack

- **Backend:** Python 3.13+, FastAPI, SQLite, SQLModel, Alembic, Pillow, uvicorn
- **Frontend:** Python 3.13+, PySide6, QML, httpx

## Environment

Python 3.13+ via pyenv virtualenv `found_env`. Activate with:

```
pyenv activate found_env
```

Install all dependencies:

```
make setup
```

Or install individually:

```
pip install -r backend/requirements-dev.txt
pip install -r found_app/requirements-dev.txt
```

## Commands

### Frontend

```bash
# Run the application
python -m found_app

# Run frontend tests (from project root)
python -m pytest found_app/tests/ -v
```

### Backend

Commands run from `backend/`:

```bash
# Run backend tests
python -m pytest tests/ -v

# Start the API server (standalone, without frontend)
uvicorn app.main:app --reload
```

## Architecture

Found has a FastAPI + SQLite backend that indexes images in-place (files are never copied or moved) and a PySide6/QML frontend. The frontend communicates with the backend exclusively through its REST API — no direct database or filesystem access.

## Development workflow _IMPORTANT_

When preparing to write new code:

1. **First break new code up into the smallest necessary change.** Changes should complete a single, distinct logical task. It should be easy to roll back without breaking the system and simple enough for another developer to understand the "why" at a glance.
2. **Write tests first** This project uses Test Drive Development (TDD). The workflow is RED, GREEN, REFACTOR
3. **Write the minimum implementation to make it pass**
4. **Run the full suite to confirm nothing regressed.**
5. **Git commits should always be clean functional code** Write commit messages in the imperative mood that describe _why_, not just _what_.

### Test Driven Development

Backend tests use an in-memory SQLite engine. The `run_migrations` call in the app lifespan is patched out in `conftest.py`; schema is created directly via `SQLModel.metadata.create_all()`.

Frontend tests use an offscreen Qt platform (`QT_QPA_PLATFORM=offscreen`). QML component tests use `QQmlEngine` with `Theme` registered as a context property.

## Key conventions

- All API routes live under `/api/v1`. The `/health` endpoint is root-level.
- Every API response uses a standard envelope: `{"success": true, "data": {}}` / `{"success": false, "error": {"code": "...", "message": "..."}}`.
- Images are never moved or copied — only their paths are stored.
- `get_session` is a FastAPI dependency; tests override it via `app.dependency_overrides`.
- Frontend never accesses the database or thumbnail cache directly — all data goes through the REST API.
- Thumbnails are served via `image://thumbnails/<uuid>` using the registered `ThumbnailProvider`.
