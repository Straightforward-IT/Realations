"""HTTP routes (versioned under /api/v1)."""

from fastapi import APIRouter

from app.api.routes import (
    activities,
    auth,
    companies,
    contacts,
    deals,
    integrations,
    subscriptions,
    tickets,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
