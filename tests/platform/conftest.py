from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.platform


def pytest_configure(config: pytest.Config) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("sqlalchemy")


@pytest.fixture(scope="module")
def client() -> Generator:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import server.db as db_module
    from server.main import seed_demo

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    db_module.engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    db_module.SessionLocal = sessionmaker(bind=db_module.engine)
    db_module.init_db()

    db = db_module.SessionLocal()
    seed_demo(db)
    db.close()

    from server.main import app

    with TestClient(app) as test_client:
        yield test_client

    db_module.engine.dispose()
    Path(db_path).unlink(missing_ok=True)
