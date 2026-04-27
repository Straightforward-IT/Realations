"""Pydantic request/response schemas."""

from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate  # noqa: F401
from app.schemas.auth import LoginRequest, RegisterTenantRequest, TokenResponse  # noqa: F401
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate  # noqa: F401
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate  # noqa: F401
from app.schemas.deal import DealCreate, DealRead, DealUpdate  # noqa: F401
from app.schemas.integration import (  # noqa: F401
    IntegrationConnectionCreate,
    IntegrationConnectionRead,
    IntegrationConnectionUpdate,
    WebhookEndpointCreate,
    WebhookEndpointRead,
    WebhookEndpointUpdate,
)
from app.schemas.subscription import (  # noqa: F401
    PlanRead,
    SubscriptionAssign,
    SubscriptionRead,
)
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate  # noqa: F401
from app.schemas.user import UserRead  # noqa: F401
