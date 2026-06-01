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
pip install -r frontend/requirements-dev.txt
```

## Commands

### Frontend

```bash
# Run the application
python -m frontend

# Run frontend tests (from project root)
python -m pytest frontend/tests/ -v
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
│   └── repositories/    # DB query layer
├── tests/
│   ├── conftest.py      # in-memory SQLite fixtures
│   └── test_*.py
├── data/                # gitignored — runtime DB and thumbnail cache
├── migrations/          # Alembic migration scripts
├── requirements.txt
└── requirements-dev.txt

frontend/
├── __main__.py          # Entry point — wires all components and starts the app
├── api/
│   └── client.py        # Async ApiClient (httpx); list_images(), health_check()
├── app/
│   └── controller.py    # AppController — connects process manager to app state
├── backend/
│   ├── process_manager.py    # Launches and monitors the backend subprocess
│   └── connection_monitor.py # Runtime health polling
├── library/
│   ├── view_model.py          # LibraryViewModel — owns ThumbnailGridModel, drives loading
│   ├── thumbnail_grid_model.py # QAbstractListModel for the image grid
│   └── thumbnail_provider.py  # QQuickAsyncImageProvider with LRU cache
├── qml/                 # QML UI components
│   ├── main.qml
│   ├── AppWindow.qml
│   ├── MainRouter.qml
│   ├── SplashScreen.qml
│   ├── LibraryView.qml
│   ├── ThumbnailGrid.qml
│   └── ThumbnailTile.qml
├── state/
│   └── app_state.py     # AppStateManager — startup lifecycle state machine
├── theme/
│   └── theme.py         # ThemeManager — design tokens exposed to QML
├── tests/
│   └── test_*.py
├── requirements.txt
└── requirements-dev.txt
```

## Development workflow

### Test Driven Development

This project uses TDD. Always write failing tests first, before writing implementation code:

1. Write a test that captures the intended behaviour — confirm it fails for the right reason (missing feature, not a setup error)
2. Write the minimum implementation to make it pass
3. Run the full suite to confirm nothing regressed

Backend tests use an in-memory SQLite engine. The `run_migrations` call in the app lifespan is patched out in `conftest.py`; schema is created directly via `SQLModel.metadata.create_all()`.

Frontend tests use an offscreen Qt platform (`QT_QPA_PLATFORM=offscreen`). QML component tests use `QQmlEngine` with `Theme` registered as a context property.

### Git practices

Commits should be small and focused — one logical change per commit. Prefer a commit per feature slice or bug fix rather than batching unrelated changes together. Write commit messages in the imperative mood that describe _why_, not just _what_. Keep work-in-progress off `main`; use feature branches for anything non-trivial.

## Key conventions

- All API routes live under `/api/v1`. The `/health` endpoint is root-level.
- Every API response uses a standard envelope: `{"success": true, "data": {}}` / `{"success": false, "error": {"code": "...", "message": "..."}}`.
- Images are never moved or copied — only their paths are stored.
- `get_session` is a FastAPI dependency; tests override it via `app.dependency_overrides`.
- Frontend never accesses the database or thumbnail cache directly — all data goes through the REST API.
- Thumbnails are served via `image://thumbnails/<uuid>` using the registered `ThumbnailProvider`.
