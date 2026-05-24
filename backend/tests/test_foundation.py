from types import SimpleNamespace

from sqlalchemy import text


def test_build_engine_creates_data_dir(tmp_path, monkeypatch):
    from app.core import database as db_module

    db_path = tmp_path / "nested" / "dir" / "database.db"
    monkeypatch.setattr(db_module, "settings", SimpleNamespace(database_url=f"sqlite:///{db_path}"))

    assert not db_path.parent.exists()
    engine = db_module._build_engine()
    assert db_path.parent.exists()
    engine.dispose()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_connection(session):
    session.execute(
        text("CREATE TABLE IF NOT EXISTS _probe (id INTEGER PRIMARY KEY, val TEXT NOT NULL)")
    )
    session.execute(text("INSERT INTO _probe (val) VALUES ('hello')"))
    session.commit()

    result = session.execute(text("SELECT val FROM _probe LIMIT 1")).scalar()
    assert result == "hello"
