"""Shared pytest fixtures.

Tests run against an in-memory SQLite database so they need no external
infrastructure. The schema is created from the SQLAlchemy metadata directly
(rather than running Alembic) for speed.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

# IMPORTANT: configure environment BEFORE importing the app/db modules so that
# pydantic-settings picks up our test database URL the very first time
# ``Settings`` is instantiated.
os.environ.setdefault("REALATIONS_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REALATIONS_JWT_SECRET", "test-secret-do-not-use-in-prod-please-rotate")
os.environ.setdefault("REALATIONS_ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import db as db_pkg  # noqa: F401  -- ensures package init
from app.db import session as db_session
from app.db.base import Base
from app.licensing.catalog import seed_plans
from app.main import create_app


@pytest.fixture(scope="session")
def _engine():
    # Single shared in-memory database for the whole test session.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    # Re-import models so all tables register against this metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(autouse=True)
def _patch_session(_engine, monkeypatch):
    TestSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True, class_=Session)
    monkeypatch.setattr(db_session, "engine", _engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestSession)
    # Also patch the symbol the API layer imported at module load time.
    from app.api import deps as api_deps

    monkeypatch.setattr(api_deps, "SessionLocal", TestSession)
    # Seed plans once per test (cheap on SQLite).
    with TestSession() as s:
        seed_plans(s)
        s.commit()
    yield
    # Wipe data between tests to keep them independent.
    with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as c:
        yield c
