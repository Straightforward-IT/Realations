"""Aggregate model imports so SQLAlchemy metadata sees every table."""

from app.models.activity import Activity  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.contact import Contact  # noqa: F401
from app.models.deal import Deal  # noqa: F401
from app.models.integration import IntegrationConnection, WebhookEndpoint  # noqa: F401
from app.models.subscription import Plan, Subscription  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.ticket import Ticket  # noqa: F401
from app.models.user import User  # noqa: F401
