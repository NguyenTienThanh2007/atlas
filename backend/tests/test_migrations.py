from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.config import get_settings

_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _current_revision() -> str | None:
    engine = create_engine(get_settings().database_url)
    try:
        with engine.connect() as conn:
            exists = conn.execute(text("SELECT to_regclass('alembic_version')")).scalar()
            if exists is None:
                return None
            return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    finally:
        engine.dispose()


def test_migrations_upgrade_downgrade_roundtrip() -> None:
    cfg = Config(str(_INI))
    head = ScriptDirectory.from_config(cfg).get_current_head()

    command.upgrade(cfg, "head")
    assert _current_revision() == head

    command.downgrade(cfg, "base")
    assert _current_revision() is None

    command.upgrade(cfg, "head")
    assert _current_revision() == head
