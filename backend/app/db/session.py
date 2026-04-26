"""SQLAlchemy engine, session factory, and tenant-aware session helpers.

The session helpers implement the *Shared Database, Shared Schema* multi-tenancy
model recommended in the architectural blueprint, with PostgreSQL Row-Level
Security as the authoritative isolation mechanism.

Every request that has resolved a tenant context calls
``set_tenant_context(session, tenant_id)`` before issuing queries. This sets a
per-transaction ``app.current_tenant`` GUC that the RLS policies installed via
Alembic migration consult. On non-PostgreSQL backends (notably the SQLite
configuration used in tests) the GUC call is a no-op and isolation is enforced
by the application layer through explicit ``Model.tenant_id`` filtering.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    connect_args: dict = {}
    if settings.database_url.startswith("sqlite"):
        # SQLite uses thread-local connections by default; allow cross-thread for FastAPI.
        connect_args["check_same_thread"] = False
    engine = create_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    if settings.database_url.startswith("sqlite"):
        # Enforce foreign keys on SQLite (off by default) so referential constraints behave
        # consistently with PostgreSQL during development and tests.
        @event.listens_for(engine, "connect")
        def _enable_sqlite_fks(dbapi_connection, _):  # pragma: no cover - trivial
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine: Engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, class_=Session)


def set_tenant_context(session: Session, tenant_id: uuid.UUID | str | None) -> None:
    """Bind the active tenant to the current transaction for RLS enforcement.

    On PostgreSQL this issues ``SET LOCAL app.current_tenant = '<uuid>'`` so that
    any RLS policy referencing ``current_setting('app.current_tenant')`` filters
    rows correctly. On other backends this is a safe no-op.
    """
    if tenant_id is None:
        return
    if not get_settings().is_postgres:
        return
    # Parameter binding is not allowed for SET LOCAL targets in PostgreSQL, so we
    # validate the value by parsing it as a UUID before interpolating it. This
    # prevents SQL injection because only valid UUID strings can reach the SQL.
    tenant_uuid = uuid.UUID(str(tenant_id))
    session.execute(text(f"SET LOCAL app.current_tenant = '{tenant_uuid}'"))


@contextmanager
def session_scope(tenant_id: uuid.UUID | str | None = None) -> Iterator[Session]:
    """Context manager yielding a transactional session bound to a tenant."""
    session = SessionLocal()
    try:
        set_tenant_context(session, tenant_id)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session.

    The actual tenant binding happens in
    :func:`app.api.deps.get_db` once the access token has been validated.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
