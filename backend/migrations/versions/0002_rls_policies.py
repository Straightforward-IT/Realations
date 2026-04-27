"""row level security policies (postgres only)

Revision ID: 0002_rls_policies
Revises: 0001_initial
Create Date: 2026-04-26 21:50:01.000000
"""
from __future__ import annotations

from alembic import op

revision = "0002_rls_policies"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

# Tables that carry a tenant_id column and should be scoped by RLS.
TENANT_SCOPED_TABLES = (
    "users",
    "companies",
    "contacts",
    "deals",
    "activities",
    "tickets",
    "integration_connections",
    "webhook_endpoints",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # RLS is a PostgreSQL feature; on other backends we rely on
        # application-layer filtering via crud helpers.
        return

    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        # The session sets ``app.current_tenant`` via ``SET LOCAL`` on every
        # request; a NULL/missing setting means "no tenant" and the policy
        # will hide every row.
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id::text = current_setting('app.current_tenant', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true))
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
