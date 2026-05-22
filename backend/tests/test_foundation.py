from sqlalchemy import text


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
