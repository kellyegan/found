from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings


def _build_engine():
    url = settings.database_url
    if url.startswith("sqlite:///"):
        db_path = Path(url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args={"check_same_thread": False})


engine = _build_engine()


def run_migrations() -> None:
    """Apply all pending Alembic migrations. Called on app startup."""
    from alembic.config import Config
    from alembic import command

    ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    cfg = Config(str(ini_path))
    command.upgrade(cfg, "head")


def create_db_and_tables() -> None:
    """Create all tables directly via SQLModel. Used by the test suite only."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
