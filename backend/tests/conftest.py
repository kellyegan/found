from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.image import Image


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def make_image(session):
    def _factory(path: str, filename: str = None, **kwargs) -> Image:
        img = Image(filename=filename or Path(path).name, path=path, **kwargs)
        session.add(img)
        session.commit()
        session.refresh(img)
        return img
    return _factory


@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with patch("app.core.database.run_migrations"):
        with TestClient(app) as client:
            yield client
    app.dependency_overrides.clear()
