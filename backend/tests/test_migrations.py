from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

EXPECTED_TABLES = {
    "image", "importjob", "tag", "imagetag",
    "category", "imagecategory", "collection",
    "collectionimage", "importresult",
}


@pytest.fixture
def alembic_cfg(tmp_path):
    db_path = tmp_path / "migration_test.db"
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    cfg.set_main_option("script_location", str(ALEMBIC_INI.parent / "migrations"))
    return cfg, db_path


def test_upgrade_creates_all_tables(alembic_cfg):
    cfg, db_path = alembic_cfg
    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)


def test_upgrade_records_version(alembic_cfg):
    cfg, db_path = alembic_cfg
    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version is not None


def test_downgrade_removes_tables(alembic_cfg):
    cfg, db_path = alembic_cfg
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(f"sqlite:///{db_path}")
    remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert remaining == set()


def test_upgrade_is_idempotent(alembic_cfg):
    """Running upgrade head twice does not raise."""
    cfg, db_path = alembic_cfg
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
